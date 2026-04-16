# AstrBot LINUX DO 社区助手插件

这是一个为 [AstrBot](https://github.com/AstrBotDevs/AstrBot) 框架开发的插件，旨在方便用户直接在聊天机器人中获取 [LINUX DO](https://linux.do) 社区的热帖和最新讨论。

## 🌟 功能特性

- **今日热榜**: 获取社区每日热门话题列表 (`/ld_top`)。
- **最新讨论**: 获取社区最新的讨论话题 (`/ld_new`)。
- **智能过滤**: 自动过滤置顶帖，只看新鲜干货。
- **清爽 UI**: 使用**合并转发消息**展示结果，点开即看，不刷屏。
- **WebUI 配置**: 支持在管理后台直接调整展示数量和过滤开关。
- **强力绕过**: 内置 TLS 指纹伪装，有效规避 Cloudflare 403 拦截。

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
| `/ld_new` | 获取最新讨论话题 | `/ld_new` |

## 📄 许可证

本项目采用 MIT 许可证。

---
由 GeminiCLI 辅助开发。
