# Lucas 的小站

> **在线访问：[https://mapleyou.github.io](https://mapleyou.github.io)**

个人博客，Hexo + Butterfly 主题，GitHub Pages 托管，GitHub Actions 自动构建部署。

## 写什么

- **ISP 图像处理**：Camera 全链路、影像算法、画质调优
- **系统底层**：Linux 内核、Android Binder、C 语言面向对象
- **音视频 / 后台开发**的学习与实践笔记

同步更新：微信公众号「**码尘飞扬社**」 · [GitHub](https://github.com/MAPLEYOU)

## 近期文章

| 文章 | 分类 | 日期 |
| --- | --- | --- |
| [Linux 内核没有 class，凭什么玩面向对象？](https://mapleyou.github.io/posts/linux-c-oo/) | 系统底层 | 2026-10-04 |
| [学习地图: 一张图看懂 ISP 全链路](https://mapleyou.github.io/posts/isp-roadmap/) | ISP 全链路笔记 | 2026-10-03 |

> Permalink 格式为 `posts/:title/`，与 `_config.yml` 中 `permalink` 配置一致；链接里的 title 是文章文件名（如 `linux-c-oo.md` → `linux-c-oo`）。

## 本地写作

```bash
npm install       # 首次安装依赖
npm run server    # 本地预览 http://localhost:4000
npm run build     # 生成静态文件到 public/
npm run clean     # 清理缓存
```

## 发布流程

在 `source/_posts/` 新建 `.md` 文件（frontmatter 含 `title` / `date` / `tags` / `categories`），然后：

```bash
git add . && git commit -m "post: 文章标题" && git push
```

推送到 `main` 后 GitHub Actions 自动构建并发布到 GitHub Pages，约 1-2 分钟生效。

## 目录说明

| 路径 | 说明 |
| --- | --- |
| `source/_posts/` | 文章（Markdown） |
| `source/img/` | 站点图片（按文章建子目录，如 `img/linux-c-oo/`） |
| `source/about/` `source/tags/` `source/categories/` | 独立页面 |
| `_config.yml` | 站点配置 |
| `_config.butterfly.yml` | 主题配置覆盖 |
| `.github/workflows/deploy.yml` | 自动部署 |
