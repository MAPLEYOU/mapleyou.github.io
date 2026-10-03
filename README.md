# lucas-blog

个人博客, Hexo + Butterfly 主题, GitHub Pages 托管。

## 本地写作

```bash
npm run server    # 本地预览 http://localhost:4000
npm run build     # 生成静态文件到 public/
npm run clean     # 清理缓存
```

## 发布流程

写文章: 在 `source/_posts/` 新建 `.md` 文件, 然后:

```bash
git add . && git commit -m "post: 文章标题" && git push
```

GitHub Actions 会自动构建并发布到 GitHub Pages, 约 1-2 分钟生效。

## 目录说明

- `source/_posts/` — 文章 (Markdown)
- `source/about/` `source/tags/` `source/categories/` — 独立页面
- `_config.yml` — 站点配置
- `_config.butterfly.yml` — 主题配置覆盖
- `.github/workflows/deploy.yml` — 自动部署
