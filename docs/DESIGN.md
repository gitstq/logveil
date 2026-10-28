# LogVeil 预研简报与自研方案（2026-10-28）

## 1. Trending 信号
- 2026-10-28 GitHub Trending / 本周热榜前列几乎被 AI Agent 工具占据（rea、Agent-Reach、skills、xerj 等），共同场景是：开发者把代码、终端输出、日志大量交给 Agent 与外部协作者处理。
- 由此衍生的真实痛点：**分享/投喂前的隐私脱敏**没有趁手工具——密钥扫描器只拦截提交、不改写文本，也不处理日志中的个人信息。

## 2. 账号内去重校验（相似度）
对目标账号已有仓库按名称+描述做关键词交叉比对，最接近的存量项目：
- `SecretScan-CLI` / `SecretShield-CLI` / `ai-secret-guard`：定位是**代码仓库密钥检测/拦截**，只报告不改写，无一致性占位、无还原、无个人信息类别、无校验位防误伤。与 LogVeil 的核心场景（自由文本日志的分享前改写）重合仅在「 token 类检测」一项，整体相似度估算 **< 40%**，低于 60% 一票否决线。
- `ctxpack` / `CodePack`：定位是代码打包给 LLM，与脱敏改写无关。
- 名称 `logveil` 在账号内不存在，`redact / anonym / scrub / mask` 等词在存量仓库名称与描述中均无命中。

## 3. 自研方案（100% 独立实现，未复制任何现有项目代码）
- 技术栈：Python 3.10+ 标准库，零依赖；包结构 `logveil/{detectors,redactor,cli}.py`。
- 核心模块：检测器表（类别/正则/校验器/捕获组）→ 一致性占位引擎（计数器+映射续用）→ CLI（redact/scan/restore）。
- 差异化：Luhn + MOD 11-2 + IPv4 段范围三重校验防误伤；映射表 0600 落盘与 restore 还原；scan 计数报告可挂 CI。
- 自测标准：命中、防误伤、一致性、幂等、往返还原、CLI 退出码，共 17 个 unittest 用例全过后才允许发布。

## 4. 项目类型与发布方式
工具库/脚本类：不做 Release 二进制；以源码仓库 + `pip install .` 集成说明发布，README 三语齐备。
