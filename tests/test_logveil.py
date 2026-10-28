import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from logveil import Redactor, restore_text  # noqa: E402


class RedactionTests(unittest.TestCase):
    def test_email_is_consistent(self):
        r = Redactor()
        out = r.redact_text("from a@example.com to a@example.com and b@example.com")
        self.assertEqual(out, "from [EMAIL_1] to [EMAIL_1] and [EMAIL_2]")

    def test_ip_and_home_path(self):
        r = Redactor()
        out = r.redact_text("connect 10.0.0.8 failed, file /Users/steven/logs/app.log")
        self.assertIn("[IP_1]", out)
        self.assertIn("/Users/[USER_PATH_1]/logs/app.log", out)
        self.assertNotIn("steven", out)

    def test_invalid_ip_is_kept(self):
        r = Redactor()
        self.assertEqual(r.redact_text("version 999.1.2.3 released"), "version 999.1.2.3 released")

    def test_secret_assignment_keeps_key_name(self):
        r = Redactor()
        out = r.redact_text("api_key=supersecretvalue123")
        self.assertTrue(out.startswith("api_key="))
        self.assertNotIn("supersecretvalue123", out)

    def test_bearer_token(self):
        r = Redactor()
        out = r.redact_text("Authorization: Bearer abcdefgh12345678")
        self.assertNotIn("abcdefgh12345678", out)
        self.assertIn("Bearer", out)

    def test_github_token_prefix(self):
        r = Redactor()
        out = r.redact_text("token ghp_" + "A" * 36 + " leaked")
        self.assertNotIn("ghp_" + "A" * 36, out)

    def test_bank_card_luhn(self):
        r = Redactor()
        out = r.redact_text("card 4111 1111 1111 1111 charged")
        self.assertNotIn("4111", out)
        # Same shape, wrong check digit -> not a card, must survive.
        r2 = Redactor()
        self.assertIn("4111111111111112", r2.redact_text("order 4111111111111112"))

    def test_cn_id_checksum(self):
        # Build a valid ID: 110105 19491231 002 + computed check digit.
        from logveil.detectors import _ID_CHECK, _ID_WEIGHTS

        body = "11010519491231002"
        total = sum(int(body[i]) * _ID_WEIGHTS[i] for i in range(17))
        valid = body + _ID_CHECK[total % 11]
        r = Redactor()
        self.assertNotIn(valid, r.redact_text(f"id {valid}"))
        r2 = Redactor()
        bad = body + ("0" if valid[-1] != "0" else "1")
        self.assertIn(bad, r2.redact_text(f"serial {bad}"))

    def test_phone_cn(self):
        r = Redactor()
        self.assertNotIn("13812345678", r.redact_text("call 13812345678 now"))

    def test_restore_round_trip(self):
        r = Redactor()
        original = "mail a@example.com from 192.168.1.10"
        redacted = r.redact_text(original)
        self.assertEqual(restore_text(redacted, r.mapping), original)

    def test_idempotent(self):
        r = Redactor()
        once = r.redact_text("mail a@example.com")
        self.assertEqual(Redactor().redact_text(once), once)

    def test_category_filter(self):
        r = Redactor(categories=["EMAIL"])
        out = r.redact_text("a@example.com at 192.168.1.10")
        self.assertIn("[EMAIL_1]", out)
        self.assertIn("192.168.1.10", out)

    def test_mapping_save_load_continues_counters(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "map.json")
            r = Redactor()
            r.redact_text("a@example.com")
            r.save_mapping(path)
            r2 = Redactor.load_mapping(path)
            out = r2.redact_text("b@example.com a@example.com")
            self.assertEqual(out, "[EMAIL_2] [EMAIL_1]")
            with open(path, encoding="utf-8") as fh:
                self.assertEqual(json.load(fh)["a@example.com"], "[EMAIL_1]")

    def test_time_and_date_survive_but_ipv6_and_mac_do_not(self):
        r = Redactor()
        out = r.redact_text("at 09:12:04 on 2026-10-28 from 2001:db8:85a3:0:0:8a2e:370:7334 mac 00:1B:44:11:3A:B7")
        self.assertIn("09:12:04", out)
        self.assertIn("2026-10-28", out)
        self.assertIn("[IP_1]", out)
        self.assertIn("[MAC_1]", out)
        self.assertNotIn("2001:db8", out)
        self.assertNotIn("00:1B:44", out)

    def test_extra_pattern(self):
        r = Redactor(extra_patterns=[("EMPLOYEE_ID", r"EMP-\d{4}")])
        self.assertEqual(r.redact_text("user EMP-1234 logged in"), "user [EMPLOYEE_ID_1] logged in")


class CliTests(unittest.TestCase):
    def _run(self, *argv, stdin=""):
        root = os.path.join(os.path.dirname(__file__), "..")
        return subprocess.run(
            [sys.executable, "-m", "logveil", *argv],
            input=stdin, capture_output=True, text=True, cwd=root,
        )

    def test_scan_exit_codes(self):
        self.assertEqual(self._run("scan", stdin="clean log line").returncode, 0)
        self.assertEqual(self._run("scan", stdin="mail a@example.com").returncode, 1)

    def test_redact_stdin_stdout(self):
        proc = self._run("redact", stdin="ip 8.8.8.8")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("[IP_1]", proc.stdout)


if __name__ == "__main__":
    unittest.main()
