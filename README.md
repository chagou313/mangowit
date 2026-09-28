# Mangowit

Mangowit 是一个基于 Django 的性教育科普网站。

## 本地启动（SQLite）

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver 127.0.0.1:8001
```

浏览器访问 <http://127.0.0.1:8001/>。

初始化内置的 21 条 AI 问答：

```bash
.venv/bin/python manage.py seed_ai_data
```

## 测试

```bash
.venv/bin/python manage.py check
.venv/bin/python manage.py test -v 2
```

## 使用 MySQL

先安装 MySQL 开发依赖，然后执行：

```bash
.venv/bin/python -m pip install -r requirements-mysql.txt
export MANGOWIT_DB_ENGINE=mysql
export MANGOWIT_DB_NAME=sex_education
export MANGOWIT_DB_USER=mangowit
export MANGOWIT_DB_PASSWORD='your-password'
export MANGOWIT_DB_HOST=127.0.0.1
export MANGOWIT_DB_PORT=3306
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

生产部署时还需设置 `MANGOWIT_SECRET_KEY`、`MANGOWIT_DEBUG=false` 和 `MANGOWIT_ALLOWED_HOSTS`。

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

Render 免费服务闲置后会休眠，首次访问可能需要等待约一分钟；数据库和头像位于独立的持久服务中，不会因 Web Service 休眠而丢失。
