# TokenTrackerGateway

> 桌面悬浮 Token 用量追踪网关。透明中继 IDE（Cursor / Cline / Trae）的 API 请求，实时统计 token 消耗、缓存命中率、首字延迟与费用。

## 功能

- **实时代理**：本地监听 `127.0.0.1:8045`，透明转发到上游 API（OpenAI / Anthropic）
- **悬浮面板**：PyQt6 无边框置顶窗口，支持三态切换（胶囊 / 全量表格）
- **多模型定价**：内置 Claude / GPT-4o / DeepSeek 等主流模型定价表
- **流式解析**：自动解析 SSE 流中的 `usage` 信息，无需完整响应

## 仓库

- **主页**：https://github.com/luck-hope/luck-api-sumUp
- **构建产物**：https://github.com/luck-hope/luck-api-sumUp/actions
- **Release**：https://github.com/luck-hope/luck-api-sumUp/releases

## 系统要求

| 平台 | 依赖 | 说明 |
|------|------|------|
| Windows 10/11 | 无需安装 | 直接运行 `.exe` |
| macOS 10.15+ | 需 Gatekeeper 信任 | `.app` 首次运行需在"系统设置 → 隐私与安全性"中放行 |

## 安装 & 使用

### Windows（推荐）

1. 下载 `TokenTrackerGateway-Win.exe`（[Release](https://github.com/luck-hope/luck-api-sumUp/releases)）
2. 双击运行，托盘区出现胶囊窗口
3. 配置 IDE 的 API Base URL 为 `http://127.0.0.1:8045`
4. 后续所有请求的 token 统计自动显示在面板中

### macOS

1. 下载 `TokenTrackerGateway-Mac.app`（[Release](https://github.com/luck-hope/luck-api-sumUp/releases)）
2. 右键 → 打开，在弹出的安全提示中选择"仍要打开"
3. 配置 IDE 的 API Base URL 为 `http://127.0.0.1:8045`
4. 首次运行可能需要放行防火墙

## 配置

编辑 `data/config.json`（程序启动后自动生成）：

```json
{
  "port": 8045,
  "upstream_url": "https://api.openai.com",
  "api_key": "sk-..."
}
```

## 项目结构

```
gateway/          ← 核心逻辑
  counter.py      Token 统计与计价
  proxy.py        aiohttp 透明代理
ui/               ← 桌面 UI
  widget.py       PyQt6 悬浮面板
main.py           应用主入口
build_exe.py      打包脚本
```

## 开发 & 构建

```bash
# 安装依赖
pip install -r requirements.txt

# 运行
python main.py

# Windows 打包
python build_exe.py  # → dist/TokenTrackerGateway-Win.exe

# macOS 打包
python build_exe.py  # → dist/TokenTrackerGateway-Mac.app
# 生成 .dmg（可选）：
hdiutil create -volname TokenTrackerGateway-Mac \
  -srcfolder dist/TokenTrackerGateway-Mac.app \
  -ov -format UDZO dist/TokenTrackerGateway-Mac.dmg
```

## GitHub Actions 自动构建

推送代码后 GitHub Actions 自动在 Windows + macOS runner 上构建，产物在 [Actions](https://github.com/luck-hope/luck-api-sumUp/actions) 页面下载。

## License

MIT
