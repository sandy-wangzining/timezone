# 时间戳对照台

纯前端时区转换工具，入口为 `index.html`。

## GitHub Pages 发布

在个人 GitHub 账号创建一个公开仓库后执行：

```bash
git remote add origin <你的个人仓库地址>
git add index.html README.md
git commit -m "feat(timezone-site): 发布时区转换工具"
git branch -M main
git push -u origin main
```

然后在 GitHub 仓库的 Settings -> Pages 中选择 GitHub Actions 或 `main` 分支发布。
