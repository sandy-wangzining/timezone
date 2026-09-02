# 时间戳对照台

一个无需后端的在线时区转换工具，使用浏览器内置的 IANA 时区数据库完成计算。

## 在线地址

- GitHub Pages：<https://sandy-wangzining.github.io/timezone/>
- 飞书妙搭：<https://presence.feishu.cn/page/Pc1MmZ834dv1N5aAlZ2cR4canjg>
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
- 页面改版只调整 HTML/CSS 呈现层，未改变时间戳解析、日期解析、DST 处理和收藏逻辑。
