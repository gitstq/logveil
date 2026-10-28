# 🤝 Contributing / 贡献指南

## English
- Fork, branch from `main`, and open a pull request.
- Commit messages follow Angular style: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`.
- Every new detector needs a positive test **and** a false-positive test
  (a look-alike value that must survive redaction).
- Run the full suite before submitting: `python -m unittest discover -s tests -v`
- Never commit a real mapping file or real personal data in examples.

## 简体中文
- Fork 后从 `main` 拉分支，提交 Pull Request。
- 提交信息遵循 Angular 规范：`feat:` / `fix:` / `docs:` / `refactor:` / `test:`。
- 每个新检测规则必须同时有命中测试**和**防误伤测试（形似但不该被脱敏的值）。
- 提交前跑全量测试：`python -m unittest discover -s tests -v`
- 示例里禁止放真实映射文件和真实个人信息。

## Issues
Report false positives / false negatives with a minimal synthetic example —
please redact real data before posting (LogVeil itself can help).
