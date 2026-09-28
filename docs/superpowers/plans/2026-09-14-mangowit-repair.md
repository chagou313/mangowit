# Mangowit Runtime Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the extracted Mangowit Django site start locally with SQLite by default, retain opt-in MySQL support, and eliminate every reproduced HTTP 500 response.

**Architecture:** Keep Django's existing app structure and introduce no new framework. Runtime settings are driven by environment variables, with SQLite as the zero-configuration default; each broken route is repaired at its actual view, URL, or template boundary and guarded by a focused Django regression test.

**Tech Stack:** Python 3.14, Django 5.1–5.2, SQLite, optional MySQL via mysqlclient, Pillow, Django TestCase, Codex in-app browser.

---

## File structure

- `mangowit/settings.py`: environment-driven security and database configuration; local SQLite defaults.
- `requirements.txt`: dependencies required for the default SQLite runtime.
- `requirements-mysql.txt`: optional MySQL driver layered on the base requirements.
- `.env.example`: non-secret examples for both local and MySQL modes.
- `README.md`: reproducible setup, test, migration, and start commands.
- `tests/__init__.py`: makes the cross-app regression suite importable.
- `tests/test_settings.py`: subprocess tests that load settings in clean environments.
- `tests/test_entry_routes.py`: old quiz entry, profile authentication, and level-selection regressions.
- `tests/test_education.py`: education index empty/populated rendering regressions.
- `tests/test_community.py`: topic detail success and not-found regressions.
- `sex_education_app/views.py`: canonical public views, auth flow, and protected profile view.
- `challenge/views.py`: legacy challenge redirect and category-aware level rendering.
- `EducationInformation/templates/education_index.html`: missing article-list page with empty state.
- `CommunityForums/views.py`: standard 404 lookup for topic detail.

### Task 1: Runtime configuration and dependency manifests

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/test_settings.py`
- Modify: `mangowit/settings.py:1-158`
- Create: `requirements.txt`
- Create: `requirements-mysql.txt`
- Create: `.env.example`

- [ ] **Step 1: Add failing settings tests**

Create an empty `tests/__init__.py` and create `tests/test_settings.py` with:

```python
import json
import os
import subprocess
import sys
from pathlib import Path

from unittest import TestCase


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SETTING_NAMES = {
    "MANGOWIT_DB_ENGINE",
    "MANGOWIT_DB_NAME",
    "MANGOWIT_DB_USER",
    "MANGOWIT_DB_PASSWORD",
    "MANGOWIT_DB_HOST",
    "MANGOWIT_DB_PORT",
}


class RuntimeSettingsTests(TestCase):
    def load_databases(self, overrides=None):
        environment = os.environ.copy()
        for name in SETTING_NAMES:
            environment.pop(name, None)
        environment.update(overrides or {})
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import json; "
                    "from mangowit.settings import DATABASES; "
                    "print(json.dumps(DATABASES, default=str))"
                ),
            ],
            cwd=PROJECT_ROOT,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(result.stdout)

    def test_sqlite_is_the_default_database(self):
        databases = self.load_databases()

        self.assertEqual(databases["default"]["ENGINE"], "django.db.backends.sqlite3")
        self.assertTrue(databases["default"]["NAME"].endswith("db.sqlite3"))

    def test_mysql_configuration_comes_from_environment(self):
        databases = self.load_databases(
            {
                "MANGOWIT_DB_ENGINE": "mysql",
                "MANGOWIT_DB_NAME": "mangowit_test",
                "MANGOWIT_DB_USER": "mangowit_user",
                "MANGOWIT_DB_PASSWORD": "test-password",
                "MANGOWIT_DB_HOST": "db.internal",
                "MANGOWIT_DB_PORT": "3307",
            }
        )

        self.assertEqual(
            databases["default"],
            {
                "ENGINE": "django.db.backends.mysql",
                "NAME": "mangowit_test",
                "USER": "mangowit_user",
                "PASSWORD": "test-password",
                "HOST": "db.internal",
                "PORT": "3307",
            },
        )
```

- [ ] **Step 2: Run the settings tests and verify RED**

Run:

```bash
.venv/bin/python -m unittest tests.test_settings -v
```

Expected: `test_sqlite_is_the_default_database` fails because the current default engine is `django.db.backends.mysql`; the MySQL environment test fails because the current hard-coded values ignore the supplied environment.

- [ ] **Step 3: Replace hard-coded runtime settings**

In `mangowit/settings.py`, keep the existing installed apps, middleware, templates, password validators, localization, media, and static configuration. Replace the security, database, and Neo4j constant blocks with:

```python
def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


SECRET_KEY = os.getenv(
    "MANGOWIT_SECRET_KEY",
    "django-insecure-local-development-key-change-before-deployment",
)
DEBUG = env_bool("MANGOWIT_DEBUG", True)
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("MANGOWIT_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    if host.strip()
]

if os.getenv("MANGOWIT_DB_ENGINE", "sqlite").strip().lower() == "mysql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.getenv("MANGOWIT_DB_NAME", "sex_education"),
            "USER": os.getenv("MANGOWIT_DB_USER", "root"),
            "PASSWORD": os.getenv("MANGOWIT_DB_PASSWORD", ""),
            "HOST": os.getenv("MANGOWIT_DB_HOST", "127.0.0.1"),
            "PORT": os.getenv("MANGOWIT_DB_PORT", "3306"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

LOGIN_URL = "/login_register/"

NEO4J_CONFIG = {
    "uri": os.getenv("MANGOWIT_NEO4J_URI", "bolt://localhost:7687"),
    "user": os.getenv("MANGOWIT_NEO4J_USER", "neo4j"),
    "password": os.getenv("MANGOWIT_NEO4J_PASSWORD", ""),
}
```

Remove the original hard-coded `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, both MySQL database dictionaries, and the hard-coded Neo4j password.

- [ ] **Step 4: Add dependency manifests**

Create `requirements.txt`:

```text
Django>=5.1,<5.3
Pillow>=10.0
```

Create `requirements-mysql.txt`:

```text
-r requirements.txt
mysqlclient>=2.2
```

Create `.env.example`:

```dotenv
MANGOWIT_SECRET_KEY=replace-with-a-random-production-secret
MANGOWIT_DEBUG=true
MANGOWIT_ALLOWED_HOSTS=127.0.0.1,localhost

# SQLite is the default. Uncomment the following lines to use MySQL.
# MANGOWIT_DB_ENGINE=mysql
# MANGOWIT_DB_NAME=sex_education
# MANGOWIT_DB_USER=mangowit
# MANGOWIT_DB_PASSWORD=replace-with-a-database-password
# MANGOWIT_DB_HOST=127.0.0.1
# MANGOWIT_DB_PORT=3306

MANGOWIT_NEO4J_URI=bolt://localhost:7687
MANGOWIT_NEO4J_USER=neo4j
MANGOWIT_NEO4J_PASSWORD=
```

- [ ] **Step 5: Run settings tests and Django system check**

Run:

```bash
.venv/bin/python -m unittest tests.test_settings -v
.venv/bin/python manage.py check
```

Expected: 2 tests pass and the system check reports `System check identified no issues`.

- [ ] **Step 6: Commit the runtime configuration**

```bash
git add mangowit/settings.py requirements.txt requirements-mysql.txt .env.example tests/__init__.py tests/test_settings.py
git commit -m "fix: add portable local runtime configuration"
```

### Task 2: Old quiz entry points and protected profile

**Files:**
- Create: `tests/test_entry_routes.py`
- Modify: `sex_education_app/views.py:1-148`

- [ ] **Step 1: Add failing route and authentication tests**

Create `tests/test_entry_routes.py` with:

```python
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class SexEducationEntryRouteTests(TestCase):
    def setUp(self):
        self.client.raise_request_exception = False

    def test_legacy_quiz_redirects_to_category_selection(self):
        response = self.client.get(reverse("quiz"))

        self.assertRedirects(response, reverse("category_select"))

    def test_anonymous_profile_redirects_to_login_register(self):
        response = self.client.get(reverse("profile"))

        self.assertRedirects(
            response,
            f'{reverse("login_register")}?next={reverse("profile")}',
        )

    def test_authenticated_profile_renders(self):
        user = get_user_model().objects.create_user(
            username="profile-user",
            password="safe-test-password",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "profile-user")
```

- [ ] **Step 2: Run entry-route tests and verify RED**

Run:

```bash
.venv/bin/python manage.py test tests.test_entry_routes.SexEducationEntryRouteTests -v 2
```

Expected: the quiz assertion receives HTTP 500 due to `NoReverseMatch('home')`, and anonymous profile receives HTTP 500 because `AnonymousUser` is passed to `UserProfileForm`; the authenticated profile test already demonstrates the working authenticated path.

- [ ] **Step 3: Consolidate the sex education views**

Replace `sex_education_app/views.py` with the following equivalent, deduplicated implementation:

```python
import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import RegistrationForm, UserProfileForm


logger = logging.getLogger(__name__)


def index(request):
    return render(request, "index.html")


def knowledge(request):
    return render(request, "knowledge.html")


def news(request):
    return render(request, "news.html")


def quiz(request):
    return redirect("category_select")


def community(request):
    return render(request, "community.html")


def physiological_knowledge(request):
    return render(request, "knowledge/physiological_knowledge.html")


def psychological_knowledge(request):
    return render(request, "knowledge/psychological_knowledge.html")


def safety_knowledge(request):
    return render(request, "knowledge/safety_knowledge.html")


def quiz_history(request):
    return render(request, "quiz_history.html")


def category_select(request):
    return render(request, "category_select.html")


def favorite_news(request):
    return render(request, "favorite_news.html")


def login_register(request):
    form_type = request.GET.get("form_type", "login")
    form = None

    if request.method == "POST":
        if form_type == "login":
            username = request.POST.get("username")
            password = request.POST.get("password")
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                logger.info("User %s logged in successfully.", username)
                messages.success(request, "登录成功！")
                return redirect("index")
            messages.error(request, "用户名或密码错误，请重试。")
            logger.warning("Failed login attempt for user %s.", username)
        else:
            form = RegistrationForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "注册成功，请登录。")
                return redirect("login_register")
            messages.error(request, "注册失败，请检查输入信息。")
    elif form_type == "register":
        form = RegistrationForm()

    return render(
        request,
        "login_register.html",
        {"form_type": form_type, "form": form},
    )


def user_logout(request):
    logout(request)
    messages.success(request, "退出登录成功！")
    return redirect("index")


@login_required(login_url="login_register")
def profile(request):
    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "个人信息更新成功！")
            return redirect("profile")
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, "profile.html", {"form": form})
```

- [ ] **Step 4: Run entry-route tests and verify GREEN**

Run:

```bash
.venv/bin/python manage.py test tests.test_entry_routes.SexEducationEntryRouteTests -v 2
```

Expected: all 3 tests pass.

- [ ] **Step 5: Commit quiz/profile repairs**

```bash
git add sex_education_app/views.py tests/test_entry_routes.py
git commit -m "fix: repair quiz entry and profile authentication"
```

### Task 3: Challenge compatibility routes

**Files:**
- Modify: `tests/test_entry_routes.py`
- Modify: `challenge/views.py:1-48`

- [ ] **Step 1: Add failing challenge route tests**

Append to `tests/test_entry_routes.py`:

```python
class ChallengeEntryRouteTests(TestCase):
    def setUp(self):
        self.client.raise_request_exception = False

    def test_legacy_question_redirects_to_category_selection(self):
        response = self.client.get(reverse("question"))

        self.assertRedirects(response, reverse("category_select"))

    def test_level_selection_without_category_redirects(self):
        response = self.client.get("/level_select/")

        self.assertRedirects(response, reverse("category_select"))

    def test_level_selection_with_category_renders(self):
        response = self.client.get("/level_select/physiology/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "physiology")
```

- [ ] **Step 2: Run challenge tests and verify RED**

Run:

```bash
.venv/bin/python manage.py test tests.test_entry_routes.ChallengeEntryRouteTests -v 2
```

Expected: the legacy question page returns HTTP 500 due to missing template URL names, and `/level_select/` returns HTTP 500 because `category` is missing; the category-specific route returns 200.

- [ ] **Step 3: Repair the challenge entry views**

Replace `challenge/views.py` with:

```python
from django.shortcuts import redirect, render


def category_select(request):
    return render(request, "category_select.html")


def question(request):
    return redirect("category_select")


def question1(request):
    return render(request, "question1.html")


def question2(request):
    return render(request, "question2.html")


def question3(request):
    return render(request, "question3.html")


def question21(request):
    return render(request, "question21.html")


def question22(request):
    return render(request, "question22.html")


def question23(request):
    return render(request, "question23.html")


def question31(request):
    return render(request, "question31.html")


def question32(request):
    return render(request, "question32.html")


def question33(request):
    return render(request, "question33.html")


def result(request):
    return render(request, "result.html")


def level_select(request, category=None):
    if category is None:
        return redirect("category_select")
    levels = [1, 2, 3]
    return render(
        request,
        "level_select.html",
        {"category": category, "levels": levels},
    )
```

- [ ] **Step 4: Run challenge tests and verify GREEN**

Run:

```bash
.venv/bin/python manage.py test tests.test_entry_routes.ChallengeEntryRouteTests -v 2
```

Expected: all 3 tests pass.

- [ ] **Step 5: Commit challenge route repairs**

```bash
git add challenge/views.py tests/test_entry_routes.py
git commit -m "fix: redirect incomplete challenge entry routes"
```

### Task 4: Education information index

**Files:**
- Create: `tests/test_education.py`
- Create: `EducationInformation/templates/education_index.html`

- [ ] **Step 1: Add failing education index tests**

Create `tests/test_education.py`:

```python
from django.test import TestCase
from django.urls import reverse

from EducationInformation.models import Article


class EducationIndexTests(TestCase):
    def setUp(self):
        self.client.raise_request_exception = False

    def test_empty_education_index_renders(self):
        response = self.client.get(reverse("education_index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "暂无教育资讯")

    def test_education_index_lists_articles(self):
        Article.objects.create(
            title="测试教育资讯",
            content="用于页面回归测试的文章内容",
            source_url="https://example.com/article",
        )

        response = self.client.get(reverse("education_index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "测试教育资讯")
        self.assertContains(response, "https://example.com/article")
```

- [ ] **Step 2: Run education tests and verify RED**

Run:

```bash
.venv/bin/python manage.py test tests.test_education -v 2
```

Expected: both tests receive HTTP 500 because `education_index.html` does not exist.

- [ ] **Step 3: Create the education index template**

Create `EducationInformation/templates/education_index.html`:

```django
{% extends "base.html" %}

{% block title %}教育资讯{% endblock %}

{% block content %}
<section style="max-width: 960px; margin: 2rem auto; padding: 2rem; background: white; border-radius: 1rem;">
    <h1 style="margin-bottom: 1.5rem; color: #6d43b5;">教育资讯</h1>
    {% for article in articles %}
        <article style="padding: 1rem 0; border-bottom: 1px solid #eee;">
            <h2>{{ article.title }}</h2>
            <p>{{ article.content|truncatechars:180 }}</p>
            <a href="{{ article.source_url }}" rel="noopener noreferrer">查看来源</a>
        </article>
    {% empty %}
        <p>暂无教育资讯。</p>
    {% endfor %}
    <p style="margin-top: 1.5rem;"><a href="{% url 'news' %}">返回新闻资讯</a></p>
</section>
{% endblock %}
```

- [ ] **Step 4: Run education tests and verify GREEN**

Run:

```bash
.venv/bin/python manage.py test tests.test_education -v 2
```

Expected: both tests pass.

- [ ] **Step 5: Commit the education index**

```bash
git add EducationInformation/templates/education_index.html tests/test_education.py
git commit -m "fix: add education information index"
```

### Task 5: Topic detail not-found behavior

**Files:**
- Create: `tests/test_community.py`
- Modify: `CommunityForums/views.py:1-38`

- [ ] **Step 1: Add failing community detail tests**

Create `tests/test_community.py`:

```python
from django.test import TestCase
from django.urls import reverse

from CommunityForums.models import Topic


class TopicDetailTests(TestCase):
    def setUp(self):
        self.client.raise_request_exception = False

    def test_missing_topic_returns_404(self):
        response = self.client.get(reverse("topic_detail", args=[999999]))

        self.assertEqual(response.status_code, 404)

    def test_existing_topic_renders(self):
        topic = Topic.objects.create(title="测试话题", content="测试话题内容")

        response = self.client.get(reverse("topic_detail", args=[topic.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "测试话题")
        self.assertContains(response, "测试话题内容")
```

- [ ] **Step 2: Run community tests and verify RED**

Run:

```bash
.venv/bin/python manage.py test tests.test_community -v 2
```

Expected: the missing-topic test receives HTTP 500 because the exception branch tries to render absent `404.html`; the existing-topic test passes.

- [ ] **Step 3: Use Django's standard object-or-404 lookup**

Replace `CommunityForums/views.py` with:

```python
from django.shortcuts import get_object_or_404, redirect, render

from .models import Topic


def community_index(request):
    topics = Topic.objects.all().order_by("-created_at")
    return render(request, "community_index.html", {"topics": topics})


def publish_topic(request):
    if request.method == "POST":
        title = request.POST.get("title")
        content = request.POST.get("content")
        if not title or not content:
            return render(
                request,
                "publish_topic.html",
                {"initial_title": title, "error_message": "话题标题和详细内容不能为空"},
            )
        topic = Topic.objects.create(title=title, content=content)
        return redirect("topic_detail", topic_id=topic.id)

    initial_title = request.GET.get("title", "")
    return render(request, "publish_topic.html", {"initial_title": initial_title})


def sexual_impulse(request):
    return render(request, "sexual_impulse.html")


def topic_detail(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    return render(
        request,
        "topic_detail.html",
        {"title": topic.title, "content": topic.content},
    )
```

- [ ] **Step 4: Run community tests and verify GREEN**

Run:

```bash
.venv/bin/python manage.py test tests.test_community -v 2
```

Expected: both tests pass and the missing record is reported as HTTP 404.

- [ ] **Step 5: Commit the topic detail repair**

```bash
git add CommunityForums/views.py tests/test_community.py
git commit -m "fix: return 404 for missing forum topics"
```

### Task 6: Setup documentation and complete verification

**Files:**
- Create: `README.md`
- Modify during local setup only: `db.sqlite3`

- [ ] **Step 1: Write the setup documentation**

Create `README.md`:

```markdown
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
```

- [ ] **Step 2: Run migrations against the included SQLite database**

Run:

```bash
.venv/bin/python manage.py migrate
```

Expected: every included migration reports `OK` or `No migrations to apply`; `sqlite3 db.sqlite3 '.tables'` lists Django auth/session tables and app tables.

- [ ] **Step 3: Run the complete automated suite**

Run:

```bash
.venv/bin/python manage.py check
.venv/bin/python manage.py test -v 2
```

Expected: system check has no issues and all tests pass.

- [ ] **Step 4: Run the 42-route smoke check**

Run:

```bash
.venv/bin/python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mangowit.settings'); django.setup(); from django.test import Client; client = Client(raise_request_exception=False, HTTP_HOST='localhost'); paths = ['/', '/knowledge/', '/news/', '/quiz/', '/community/', '/profile/', '/login_register/', '/knowledge/physiological_knowledge/', '/knowledge/psychological_knowledge/', '/knowledge/safety_knowledge/', '/quiz_history/', '/favorite_news/', '/category_select/', '/question/', '/question1/', '/question2/', '/question3/', '/question21/', '/question22/', '/question23/', '/question31/', '/question32/', '/question33/', '/result/', '/level_select/', '/level_select/physiology/', '/physiology/', '/psychology/', '/safety/', '/video1/', '/video2/', '/education/', '/education/news1/', '/education/news2/', '/education/news3/', '/education/law1/', '/education/law2/', '/education/law3/', '/community/publish_topic/', '/community/sexual_impulse/', '/community/topic_detail/999999/', '/ai/']; results = [(path, client.get(path).status_code) for path in paths]; print(results); assert all(status < 500 for _, status in results), results"
```

Expected: command exits 0, prints 42 route results, and none has status 500 or greater. `/profile/` returns 302 because login is required, and the intentionally missing topic returns 404; all remaining routes return 200 or intentional redirects.

- [ ] **Step 5: Start the server for browser verification**

Run:

```bash
.venv/bin/python manage.py runserver 127.0.0.1:8765 --noreload
```

Expected: Django reports `Starting development server at http://127.0.0.1:8765/` without a system-check error.

- [ ] **Step 6: Verify in a real browser**

Using the available browser automation, open `http://127.0.0.1:8765/`, verify the page body is non-empty, capture a screenshot, click “答题闯关”, and confirm the resulting URL is `/category_select/` with the three category links visible. Check the server log for HTTP 200 responses for the homepage, category page, and local static images. Stop the temporary server after verification.

- [ ] **Step 7: Commit documentation**

```bash
git add README.md
git commit -m "docs: add mangowit setup instructions"
```

- [ ] **Step 8: Review the final diff**

Run:

```bash
git status --short
git diff --check 4641486..HEAD
git log --oneline -8
```

Expected: no whitespace errors; commits after the approved design cover the implementation plan, runtime configuration, entry routes, challenge routes, education index, topic 404 handling, and setup documentation. Unrelated files outside `mangowit/` remain untouched.
