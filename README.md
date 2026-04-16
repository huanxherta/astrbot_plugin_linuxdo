# AstrBot LINUX DO 社区助手插件

这是一个为 [AstrBot](https://github.com/AstrBotDevs/AstrBot) v5 框架开发的插件，旨在方便用户直接在聊天机器人中获取 [LINUX DO](https://linux.do) 社区的热帖和搜索内容。

## 🌟 功能特性

- **今日热榜**: 获取社区每日热门话题列表 (Top 15)。
- **站内搜索**: 直接通过指令搜索社区内的帖子 (Top 10)。
- **清爽 UI**: 使用**合并转发消息**展示结果，避免群聊刷屏。
- **强力绕过**: 内置 TLS 指纹伪装 (基于 `curl_cffi`)，有效规避 Cloudflare 403 拦截。

## 🚀 安装方法

### 方式一：WebUI 安装 (推荐)

1. 进入 AstrBot 管理后台。
2. 在“插件”页面选择“从 URL 安装”。
3. 输入本仓库地址：`https://github.com/huanxherta/astrbot_plugin_linuxdo`
4. 点击“安装”并等待依赖自动安装完成。

### 方式二：手动安装

1. 进入 AstrBot 的 `data/plugins` 目录。
2. 执行克隆命令：
   ```bash
   git clone https://github.com/huanxherta/astrbot_plugin_linuxdo.git
   ```
3. 重启 AstrBot。

## 🛠️ 使用指令

| 指令 | 说明 | 示例 |
| :--- | :--- | :--- |
| `/ld_top` | 获取今日热门话题 | `/ld_top` |
| `/ld <关键词>` | 搜索社区帖子 | `/ld 始皇` |

## 📦 依赖管理

本插件使用 `curl_cffi` 模拟浏览器环境。如果通过 WebUI 安装，系统会自动处理；若是手动安装，请确保已执行：
```bash
pip install curl_cffi
```

## 📄 许可证

本项目采用 MIT 许可证。

---
由 GeminiCLI 辅助开发。
