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

## 主题

页眉右侧的「主题」按钮在三档之间循环：

| 档位 | 行为 | 是否写 localStorage |
| --- | --- | --- |
| 跟随系统 | 读 `prefers-color-scheme`，系统换主题时页面实时跟随 | 否（清掉键值） |
| 亮色 | 强制亮色 | 写 `ts.theme = light` |
| 暗色 | 强制暗色 | 写 `ts.theme = dark` |

主题由 `<head>` 里的一小段脚本在样式表之前写进 `<html data-theme>`，因此不会出现首屏闪白。
页面渲染依赖 JS，跟随系统模式也由 JS 读取媒体查询后再落到 `data-theme`。

## 字体

字体**自托管**，页面没有任何外部运行时依赖——内网、离线环境都能正常显示。

- 文件：`fonts/*.woff2`（14 个，合计约 240 KB）+ `fonts.css`（`@font-face` 声明）。
- 范围：**Manrope**（400/500/600/700）与 **IBM Plex Mono**（400/500/600），
  只保留 `latin` 与 `latin-ext` 子集；cyrillic / greek / vietnamese 对本工具无意义，不下载。
- **中文不引网络字体**，走系统字体（macOS 苹方 / Windows 雅黑）。
  Noto Sans SC 会被切成上百个 `unicode-range` 分片、全量托管有好几 MB，
  对一个纯静态小工具来说代价过高；而中文用系统字体本来就是最常见做法。
- 重新拉取（例如需要增删字重时）：

  ```bash
  python3 scripts/fetch-fonts.py
  ```

  脚本会重新下载并覆盖 `fonts.css`，**不要手工编辑这两个产物**。

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

- 页面入口：`index.html`，计算逻辑与交互逻辑均以内嵌 JavaScript 实现，不请求后端接口。
- 时区计算完全依赖浏览器的 `Intl.DateTimeFormat` 与 IANA 时区数据。
- 样式只有两套颜色令牌：`:root`（亮色）与 `:root[data-theme="dark"]`（暗色）。
  **组件样式一律引用变量，不写死颜色值**——写死一个颜色就等于在暗色主题里埋一颗雷。
  暗色不走 `prefers-color-scheme` 媒体查询，避免同一套颜色在两处维护、各自漂移。
- 关键计算函数：
  - `offsetOf(ts, tz)`：某瞬间在某时区的 UTC 偏移（分钟），按分钟缓存。
  - `stdOffsetOf(ts, tz)`：取一年四个采样点的最小/最大偏移 ⇒ 标准时与夏令时，
    并给出真实拨动幅度。只看 1 月/7 月两点会栽在南半球；按「出现次数最多」投票会栽在
    美国（夏令时长达 7 个多月）；写死 +60 分钟会栽在 Lord Howe（只拨 30 分钟）。
  - `zonedToTs(...)`：把某时区的墙钟读数还原成绝对瞬间，两轮修正保证跨夏令时边界也准。

## 兼容性与验收

- 页面包含移动端 viewport 配置，支持手机、平板、中等宽度和超宽屏布局。
- 时区计算使用浏览器内置的 IANA 时区数据库；浏览器需支持 `Intl.DateTimeFormat` 的 `timeZone` 选项。
  `Intl.supportedValuesOf` 不可用时回退到内置的常见时区清单。
- 浏览器的 ICU 对少数城市仍返回旧名（`Asia/Calcutta`、`Asia/Saigon`、`Europe/Kiev`、
  `America/Buenos_Aires`），代码里有别名表映射回中文名，不要在中文名表里直接写现代 ID。
- 回归验证方式：用无头 Chrome 抓取两套主题下约 90 个代表性选择器的计算样式与元素坐标，
  逐项比对改造前后；再对同一批截图做像素采样。
  - 亮色 1440 / 1200 / 1000px 三档宽度下，除标题列宽与实时条横向位置（给主题按钮让位）
    之外，**页面总高度与所有区块坐标逐像素一致**。
  - 暗色下修复前有 8 处元素对比度低于 2.1:1（输入框、下拉框、分段控件选中态、表头、
    说明卡等，最低 1.03:1，文字实际不可见），修复后全部达到 WCAG AA 正文标准（≥4.5:1）。
- 已知取舍：夏令时按「标准时偏移 + 正向拨动」判定。摩洛哥（斋月回拨的负向夏令时）
  会被判成全年固定，与修复前行为一致。

## 文件

```
index.html                    # 全部页面、样式与脚本
fonts.css                     # @font-face 声明（由 scripts/fetch-fonts.py 生成）
fonts/*.woff2                 # 自托管字体，14 个约 240 KB
scripts/fetch-fonts.py        # 字体拉取脚本
README.md
.gitignore
.github/workflows/pages.yml
```
