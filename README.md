# 时间戳对照台

一个无需后端的在线时区转换工具，使用浏览器内置的 IANA 时区数据库完成计算。

## 在线地址

- GitHub Pages：<https://sandy-wangzining.github.io/timezone/>
- GitHub 仓库：<https://github.com/sandy-wangzining/timezone>

如果 GitHub Pages 页面看起来仍是旧样式，请使用无痕窗口打开，或在地址后增加查询参数，例如：

<https://sandy-wangzining.github.io/timezone/?v=latest>

## 功能

- Unix 时间戳转换为指定时区的日期时间。
- 日期时间转换为秒级和毫秒级时间戳。
- 在两个命名时区之间转换墙上时间。
- 查看 UTC 偏移、夏令时状态和各时区当前时间。
- 收藏常用时区，收藏数据只保存在当前浏览器中。
- 支持深色模式、移动端布局和剪贴板复制。

## 字体

字体**自托管**（`fonts/*.woff2` + `fonts.css`），页面没有任何外部运行时依赖 —— 内网、离线环境都能正常显示。

字体经由**飞书妙搭字体 CDN（`miaoda.feishu.cn`）**拉取后本地子集化生成；字体本身为 Manrope / IBM Plex Mono / Noto Sans SC，SIL Open Font License 1.1。

- Manrope（400/500/600/700）· IBM Plex Mono（400/500/600）· Noto Sans SC（中文，400/500/600/700）
- 中文按**本页实际用到的字**做了分片裁剪：只保留与之相交的字体分片并逐个做子集化，
  `fonts/` 共 103 个文件、**woff2 净字节合计约 941 KB**（另 `fonts.css` 约 134 KB）。浏览器靠 `unicode-range` 只下载当前页面用到的那几片（运行时约 48 个）。
  注：`du -sh fonts` 显示约 1.2 MB 是**文件系统簇分配口径**，非真实传输体积。
- 重新生成（例如后续改动了页面文案、需要补字）：

  ```bash
  python3 scripts/fetch-fonts.py
  ```

  脚本会重新下载并覆盖 `fonts/` 与 `fonts.css`，**不要手工编辑这两个产物**。
  脚本内置两道自检：`url(` 必须闭合、页面所有非 ASCII 码点必须被某个分片覆盖，任一不通过即非零退出。

## 本地运行

项目是纯静态 HTML，不需要安装依赖。直接打开 `index.html` 即可使用，也可以启动任意静态文件服务器：

```bash
python -m http.server 8000
```

然后访问 <http://localhost:8000>。

## GitHub Pages 发布

仓库中的 `.github/workflows/pages.yml` 会在 `main` 分支推送后自动发布。首次使用时，在仓库 Settings -> Pages -> Build and deployment 中将 Source 设置为 `GitHub Actions`。

```bash
git add .
git commit -m "feat(timezone-site): 更新时区工具"
git push origin main
```

## 设计与实现

- 页面入口：`index.html`
- 计算逻辑和交互逻辑均以内嵌 JavaScript 实现。
- 时区计算完全依赖浏览器的 `Intl.DateTimeFormat` 和 IANA 时区数据，不请求后端接口。
- **时区列表策略**：以浏览器 `Intl.supportedValuesOf('timeZone')` 为准；仅在浏览器不支持时回退到 32 个常用时区的内置表（`FALLBACK_TZ`），并始终补充 25 个浏览器不提供的 `Etc/GMT±` / `UTC±HH:00` 固定偏移，以满足固定偏移查询。注意 IANA 的反号约定（`Etc/GMT+5` 实为 `UTC−05:00`），页面已统一显示为 UTC 值。
- 呈现层（配色令牌、间距、圆角、阴影、焦点态、过渡）与文档口径做过整理；**计算逻辑**仅对 DST 标准时推断与提示做了修正，数据来源（浏览器 `Intl` + IANA）未变。

## 兼容性与验收

- 页面包含移动端 viewport 配置，支持手机、平板、中等宽度和超宽屏布局。
- 时区计算使用浏览器内置的 IANA 时区数据库；浏览器需支持 `Intl.DateTimeFormat` 的 `timeZone` 选项。
- 已覆盖秒/毫秒/小数/负数时间戳、闰日与非法日期、夏令时缺失与回拨、半小时偏移、跨时区换算、收藏、筛选转义和转换对调等场景。
