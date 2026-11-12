# 青芒悟语 Mangowit

面向青少年的青春期健康科普网站，基于 Django 5.2。

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

## 免费公开部署

项目包含 `render.yaml`，用于在 Render 创建免费的 Django Web Service。生产环境采用：

- Render 运行 Django 与 Gunicorn，并通过 WhiteNoise 提供静态资源；
- Neon PostgreSQL 长期保存账号、会话、问答和社区数据；
- Cloudinary 长期保存用户上传的头像。

在 Render 创建 Blueprint 时需要填写以下 Secret 环境变量：

```text
DATABASE_URL=<Neon 提供的 PostgreSQL 连接字符串>
CLOUDINARY_URL=<Cloudinary 控制台提供的连接字符串>
```

`MANGOWIT_SECRET_KEY` 由 Blueprint 自动生成。不要把上述连接字符串或密钥提交到 GitHub。

每次推送到 `main` 分支，Render 会自动重新部署，启动时自动执行数据库迁移。

Render 免费服务闲置后会休眠，首次访问可能需要等待约一分钟；数据库和头像位于独立的持久服务中，不会因 Web Service 休眠而丢失。
