# Mangowit

Mangowit 是一个基于 Django 的性教育科普网站。

## 本地启动（SQLite）

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

浏览器访问 <http://127.0.0.1:8000/>。

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
