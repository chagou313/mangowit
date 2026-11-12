# 青芒悟语 Mangowit

面向青少年的青春期健康科普网站，基于 Django 5.2。

**在线访问：<https://mangowit.onrender.com>**（免费服务，闲置后首次打开需要等待约一分钟）

## 功能

| 模块 | 地址 | 说明 |
| --- | --- | --- |
| 首页 | `/` | 每日一题、继续闯关、最新内容 |
| 知识图谱 | `/physiology/`、`/psychology/`、`/safety/` | 生理、心理、安全三张可交互知识图谱 |
| 科普视频 | `/knowledge/` | 青春期（上）（下） |
| 新闻资讯 | `/news/`、`/education/<文章>/` | 新闻与法规文章，支持点赞、收藏、评论 |
| 答题闯关 | `/category_select/` | 三类各三关，共 45 道带出处的题目，记录成绩 |
| 社区 | `/community/` | 发布话题、点赞、收藏、评论 |
| AI 问答 | `/ai/` | 内置问答库 |
| 个人主页 | `/profile/` | 资料、头像、收藏 / 点赞、答题记录 |

评论经过敏感词与联系方式过滤后直接显示（每人每分钟最多 5 条），管理员可在 `/admin/` 隐藏评论。

## 目录结构

```text
mangowit/                 项目配置（settings、urls）
sex_education_app/        用户、首页、个人主页、登录注册
KnowledgePopularization/  知识图谱与科普视频
EducationInformation/     新闻法规文章、点赞收藏
challenge/                答题闯关（题库在 question_bank.py）
CommunityForums/          社区话题
AI_communication/         AI 问答
interactions/             评论（敏感词过滤在 moderation.py）
static/                   样式、图片、视频、知识图谱数据（static/kg/）
tests/                    自动化测试
```

## 本地启动（SQLite）

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_ai_data
.venv/bin/python manage.py runserver 127.0.0.1:8001
```

浏览器访问 <http://127.0.0.1:8001/>。拉取新代码后如果有模型改动，记得再执行一次 `migrate`。

## 测试

```bash
.venv/bin/python manage.py check
.venv/bin/python manage.py test
```

## 线上部署

网站部署在 Render 免费套餐上，配置写在 `render.yaml`：

| 服务 | 用途 |
| --- | --- |
| Render | 运行 Django 与 Gunicorn，WhiteNoise 提供静态资源 |
| Neon PostgreSQL | 保存账号、点赞收藏、评论、答题记录、社区和问答数据 |
| Cloudinary | 保存用户上传的头像 |

**更新网站**：把代码合并到 `main` 分支即可。Render 会自动重新构建，启动时自动执行数据库迁移并导入 AI 问答数据。

**环境变量**（在 Render 服务的 Environment 页面管理）：

| 变量 | 说明 |
| --- | --- |
| `DATABASE_URL` | Neon 提供的连接字符串，以 `postgresql://` 开头 |
| `CLOUDINARY_URL` | Cloudinary 控制台提供的连接字符串，以 `cloudinary://` 开头 |
| `MANGOWIT_SECRET_KEY` | 由 Blueprint 自动生成 |

连接字符串和密钥只填在 Render 里，不要提交到 GitHub。

**注意事项**：

- 免费服务 15 分钟无人访问会休眠，下次打开需要等待约一分钟；数据保存在 Neon 和 Cloudinary，不会因休眠丢失。
- Neon 数据库长期不用会自动归档，网站再次访问时会自动恢复。
- 部署失败时，在 Render 的 Deploys 页面打开对应部署查看日志。
