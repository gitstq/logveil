# 🕶️ LogVeil — 日志脱敏分享工具

**语言 / Language / 語言：** [简体中文](README.md) ｜ [繁體中文](README.zh-TW.md) ｜ [English](README.en.md)

> 把日志、堆栈和终端输出放心地贴进 Issue、工单和 AI 对话——先脱敏，而且脱得可逆、脱得不误伤。

## 🎉 项目介绍

调试时最常做的事，就是把日志贴给别人看：贴进 GitHub Issue、发给同事、喂给 AI 助手。但日志里往往混着邮箱、内网 IP、令牌、手机号、银行卡号和家目录用户名——贴出去的是问题，泄露的是隐私。

现有的密钥扫描工具解决的是「代码提交前拦截」，它们只报警、不改写，也不管日志里的个人信息。**LogVeil 专为「分享前脱敏」而生**：它把敏感值替换成**一致的占位符**（同一个邮箱在全文永远是 `[EMAIL_1]`），所以脱敏后的日志仍然能看出「同一个用户、同一个 IP 反复出现」这种调试线索；映射表只留在你本地，需要时一条命令就能把对方回复里的占位符**还原**回原值。

灵感来源：2026 年 GitHub Trending 被 AI Agent 工具占据，开发者把终端输出喂给 Agent 已成日常，「喂之前先脱敏」却一直没有趁手的零依赖小工具。

**自研差异化亮点：**
- 🔁 **可逆**：映射表本地保存（权限 0600），`restore` 可还原，全网同类工具多为单向涂抹
- 🎯 **不误伤**：银行卡过 Luhn 校验、身份证过 MOD 11-2 校验位、IPv4 逐段验范围，订单号、时间戳、假 IP 不会被误涂
- 🧭 **一致性**：同一原值同一占位符，跨行跨文件（续用映射表）保持关联

## ✨ 核心特性

- 🔑 **令牌与密钥**：GitHub / OpenAI / AWS / Slack / Google 令牌前缀、JWT、`Authorization: Bearer`、`api_key=` 类赋值（保留键名只涂值）
- 📧 **个人信息**：邮箱、手机号、中国居民身份证（校验位验证）
- 🌐 **网络标识**：IPv4、IPv6、MAC、带口令的 URL
- 💳 **金融信息**：银行卡号（Luhn 验证，形似的订单号不误伤）
- 🏠 **路径隐私**：`/Users/<名字>/`、`C:\Users\<名字>\` 中的用户名、GPS 坐标对、私钥块
- 🧩 **可扩展**：JSON 配置自定义类别（如员工号 `EMP-\d{4}`），可按类别开关
- 📊 **只报数模式**：`scan` 只输出各类别计数、发现即退出码 1，可挂 CI
- 📦 **零依赖**：纯 Python 3.10+ 标准库，下载即跑

## 🚀 快速开始

环境要求：Python 3.10+（Windows / macOS / Linux 均可），无任何第三方依赖。

```bash
# 方式一：克隆后直接运行（免安装）
git clone https://github.com/gitstq/logveil.git
cd logveil
python -m logveil --help

# 方式二：安装为命令
pip install .
logveil --help
```

脱敏一个日志文件（映射表务必留在本地、不要外发）：

```bash
python -m logveil redact examples/sample.log -o sample.redacted.log --map mapping.json
```

## 📖 详细使用指南

### 三个子命令

```bash
# 1) redact：脱敏。支持 stdin/stdout 管道
cat app.log | python -m logveil redact --map mapping.json > app.safe.log

# 2) scan：只检查不改写，输出计数 JSON；有发现时退出码为 1
python -m logveil scan app.log

# 3) restore：对方回复里全是占位符时，用映射表还原
python -m logveil restore reply.md --map mapping.json -o reply.restored.md
```

### 脱敏前 → 脱敏后（真实示例输出）

```text
2026-10-28 09:12:04 INFO  login ok user=[EMAIL_1] ip=[IP_1] path=/Users/[USER_PATH_1]/app/config.yaml
2026-10-28 09:12:05 ERROR charge failed card=[BANK_CARD_1] phone=[PHONE_1] order=4111111111111112
```

注意 `order=4111111111111112` 被保留了：它形似卡号但过不了 Luhn 校验；时间戳 `09:12:04` 和假 IP `999.1.2.3` 同样不会被误伤。

### 参数说明

| 参数 | 说明 |
|---|---|
| `--map <file>` | 映射表 JSON 的写入/读取路径（redact 写、restore 读），**请勿外发、勿提交仓库** |
| `--report <file>` | 只含计数的报告 JSON（不含原值，可安全外发） |
| `--categories EMAIL,IP` | 只启用指定类别，逗号分隔 |
| `--config <file>` | JSON 配置，`extra_patterns` 里写自定义正则类别 |

自定义类别示例 `logveil.json`：

```json
{ "extra_patterns": { "EMPLOYEE_ID": "EMP-\\d{4}" } }
```

典型场景：提 Issue 前脱敏日志、把终端输出喂给 AI 助手前自查、给外部供应商发故障 trace、内部工单跨团队流转。

> 📸 演示截图 / 动图：见 `examples/sample.log` 与 `examples/sample.redacted.log` 的前后对照（占位，后续补录屏）。

## 💡 设计思路与迭代规划

- **为什么用校验而非纯正则**：日志里充满「长得像」的数字，误涂一条订单号，脱敏日志就失去调试价值。校验位是现成的真伪判据，不用白不用。
- **为什么占位符要一致且可逆**：脱敏不是销毁。保留关联关系、保留还原能力，脱敏后的材料才仍然「能用来修 bug」。
- **技术选型**：纯标准库 + 逐行流式处理，大日志不吃内存；检测器与引擎分离，加新类别只需一条规则 + 两个测试（命中与防误伤）。
- **迭代计划**：地址/人名等上下文型 PII 的可选规则包、HTML 报告、VS Code 选区脱敏插件、更多国家/地区的证件与电话格式。
- **社区贡献方向**：新类别规则、防误伤语料、更多语言的文档润色。

## 📦 打包与部署指南

本项目属**工具库 / 脚本类**项目，按规则不发布 Release 二进制，集成方式如下：

```bash
# 作为包安装（生成 logveil 命令）
pip install .

# 构建 sdist / wheel
python -m pip install build
python -m build

# 运行测试
python -m unittest discover -s tests -v
```

兼容环境：Python 3.10–3.13，Windows / macOS / Linux。无环境变量要求。

常见问题：
- **映射表丢了还能还原吗？** 不能，这正是设计意图：映射表就是钥匙，请像密码一样保管。
- **脱敏会改文件结构吗？** 不会，除敏感值外逐字节保留（含时间戳与顺序）。
- **`scan` 退出码 1 是报错吗？** 不是，表示「有发现」，专为 CI 门禁设计。

## 🤝 贡献指南

欢迎 PR 与 Issue：提交信息遵循 Angular 规范（`feat:` / `fix:` / `docs:` / `refactor:`）；每个新检测规则必须同时带命中测试与防误伤测试；禁止在示例中提交真实个人信息或真实映射表。详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 📄 开源协议说明

MIT License，详见 [LICENSE](LICENSE)。可自由使用、修改与分发，保留版权声明即可。
