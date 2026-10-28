# 🕶️ LogVeil — 日誌脫敏分享工具

**語言 / Language / 语言：** [繁體中文](README.zh-TW.md) ｜ [简体中文](README.md) ｜ [English](README.en.md)

> 把日誌、堆疊追蹤和終端輸出放心地貼進 Issue、工單和 AI 對話——先脫敏，而且脫得可逆、脫得不誤傷。

## 🎉 專案介紹

除錯時最常做的事，就是把日誌貼給別人看：貼進 GitHub Issue、傳給同事、餵給 AI 助手。但日誌裡往往混著信箱、內網 IP、權杖、手機號、銀行卡號和家目錄使用者名稱——貼出去的是問題，洩露的是隱私。

現有的密鑰掃描工具解決的是「程式碼提交前攔截」，它們只警報、不改寫，也不管日誌裡的個人資訊。**LogVeil 專為「分享前脫敏」而生**：它把敏感值替換成**一致的佔位符**（同一個信箱在全文永遠是 `[EMAIL_1]`），所以脫敏後的日誌仍然看得出「同一個使用者、同一個 IP 反覆出現」這種除錯線索；對照表只留在你本機，需要時一條命令就能把對方回覆裡的佔位符**還原**回原值。

靈感來源：2026 年 GitHub Trending 被 AI Agent 工具佔據，開發者把終端輸出餵給 Agent 已成日常，「餵之前先脫敏」卻一直沒有趁手的零依賴小工具。

**自研差異化亮點：**
- 🔁 **可逆**：對照表保存在本機（權限 0600），`restore` 可還原，同類工具多為單向塗抹
- 🎯 **不誤傷**：銀行卡過 Luhn 校驗、身分證過 MOD 11-2 校驗碼、IPv4 逐段驗範圍，訂單號、時間戳、假 IP 不會被誤塗
- 🧭 **一致性**：同一原值同一佔位符，跨行跨檔案（續用對照表）保持關聯

## ✨ 核心特性

- 🔑 **權杖與密鑰**：GitHub / OpenAI / AWS / Slack / Google 權杖前綴、JWT、`Authorization: Bearer`、`api_key=` 類賦值（保留鍵名只塗值）
- 📧 **個人資訊**：信箱、手機號、中國居民身分證（校驗碼驗證）
- 🌐 **網路標識**：IPv4、IPv6、MAC、帶密碼的 URL
- 💳 **金融資訊**：銀行卡號（Luhn 驗證，形似的訂單號不誤傷）
- 🏠 **路徑隱私**：`/Users/<名字>/`、`C:\Users\<名字>\` 中的使用者名稱、GPS 座標對、私鑰區塊
- 🧩 **可擴充**：JSON 設定自訂類別（如員工號 `EMP-\d{4}`），可按類別開關
- 📊 **只報數模式**：`scan` 只輸出各類別計數、發現即結束碼 1，可掛 CI
- 📦 **零依賴**：純 Python 3.10+ 標準函式庫，下載即跑

## 🚀 快速開始

環境要求：Python 3.10+（Windows / macOS / Linux 均可），無任何第三方依賴。

```bash
# 方式一：複製後直接執行（免安裝）
git clone https://github.com/gitstq/logveil.git
cd logveil
python -m logveil --help

# 方式二：安裝為命令
pip install .
logveil --help
```

脫敏一個日誌檔（對照表務必留在本機、不要外傳）：

```bash
python -m logveil redact examples/sample.log -o sample.redacted.log --map mapping.json
```

## 📖 詳細使用指南

### 三個子命令

```bash
# 1) redact：脫敏。支援 stdin/stdout 管線
cat app.log | python -m logveil redact --map mapping.json > app.safe.log

# 2) scan：只檢查不改寫，輸出計數 JSON；有發現時結束碼為 1
python -m logveil scan app.log

# 3) restore：對方回覆裡全是佔位符時，用對照表還原
python -m logveil restore reply.md --map mapping.json -o reply.restored.md
```

### 脫敏前 → 脫敏後（真實範例輸出）

```text
2026-10-28 09:12:04 INFO  login ok user=[EMAIL_1] ip=[IP_1] path=/Users/[USER_PATH_1]/app/config.yaml
2026-10-28 09:12:05 ERROR charge failed card=[BANK_CARD_1] phone=[PHONE_1] order=4111111111111112
```

注意 `order=4111111111111112` 被保留了：它形似卡號但過不了 Luhn 校驗；時間戳 `09:12:04` 和假 IP `999.1.2.3` 同樣不會被誤傷。

### 參數說明

| 參數 | 說明 |
|---|---|
| `--map <file>` | 對照表 JSON 的寫入/讀取路徑（redact 寫、restore 讀），**請勿外傳、勿提交倉庫** |
| `--report <file>` | 只含計數的報告 JSON（不含原值，可安全外傳） |
| `--categories EMAIL,IP` | 只啟用指定類別，逗號分隔 |
| `--config <file>` | JSON 設定，`extra_patterns` 裡寫自訂正則類別 |

自訂類別範例 `logveil.json`：

```json
{ "extra_patterns": { "EMPLOYEE_ID": "EMP-\\d{4}" } }
```

典型場景：提 Issue 前脫敏日誌、把終端輸出餵給 AI 助手前自查、給外部供應商傳故障 trace、內部工單跨團隊流轉。

> 📸 演示截圖 / 動圖：見 `examples/sample.log` 與 `examples/sample.redacted.log` 的前後對照（佔位，後續補錄屏）。

## 💡 設計思路與迭代規劃

- **為什麼用校驗而非純正則**：日誌裡充滿「長得像」的數字，誤塗一條訂單號，脫敏日誌就失去除錯價值。校驗碼是現成的真偽判據，不用白不用。
- **為什麼佔位符要一致且可逆**：脫敏不是銷毀。保留關聯關係、保留還原能力，脫敏後的材料才仍然「能用來修 bug」。
- **技術選型**：純標準函式庫 + 逐行串流處理，大日誌不吃記憶體；檢測器與引擎分離，加新類別只需一條規則 + 兩個測試（命中與防誤傷）。
- **迭代計劃**：地址/人名等上下文型 PII 的可選規則包、HTML 報告、VS Code 選區脫敏外掛、更多國家/地區的證件與電話格式。
- **社群貢獻方向**：新類別規則、防誤傷語料、更多語言的文件潤色。

## 📦 打包與部署指南

本專案屬**工具庫 / 指令稿類**專案，按規則不發布 Release 二進位，整合方式如下：

```bash
# 作為套件安裝（產生 logveil 命令）
pip install .

# 建置 sdist / wheel
python -m pip install build
python -m build

# 執行測試
python -m unittest discover -s tests -v
```

相容環境：Python 3.10–3.13，Windows / macOS / Linux。無環境變數要求。

常見問題：
- **對照表丟了還能還原嗎？** 不能，這正是設計意圖：對照表就是鑰匙，請像密碼一樣保管。
- **脫敏會改檔案結構嗎？** 不會，除敏感值外逐位元組保留（含時間戳與順序）。
- **`scan` 結束碼 1 是報錯嗎？** 不是，表示「有發現」，專為 CI 門禁設計。

## 🤝 貢獻指南

歡迎 PR 與 Issue：提交訊息遵循 Angular 規範（`feat:` / `fix:` / `docs:` / `refactor:`）；每個新檢測規則必須同時帶命中測試與防誤傷測試；禁止在範例中提交真實個人資訊或真實對照表。詳見 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 📄 開源協議說明

MIT License，詳見 [LICENSE](LICENSE)。可自由使用、修改與分發，保留版權聲明即可。
