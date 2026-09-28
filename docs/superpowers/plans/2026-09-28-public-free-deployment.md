# Mangowit Public Free Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy Mangowit to a public Render URL while persisting relational data in Neon PostgreSQL and user avatars in Cloudinary.

**Architecture:** Django remains SQLite/local-media by default for development. Production is activated entirely through environment variables: `DATABASE_URL` selects Neon, `CLOUDINARY_URL` selects Cloudinary media storage, and Render runs Gunicorn with WhiteNoise static assets. A repeatable Django management command seeds the 21 built-in AI answers without touching user data.

**Tech Stack:** Django 5.2, Gunicorn, WhiteNoise, PostgreSQL/psycopg, dj-database-url, Cloudinary, Render Blueprint, Neon.

---

## File map

- Modify `mangowit/settings.py`: environment-based database, storage and production security settings.
- Modify `requirements.txt`: production runtime dependencies.
- Modify `sex_education_app/views.py`: preserve the current avatar when Cloudinary rejects an upload.
- Create `AI_communication/seed_data.py`: canonical sample question/answer data.
- Create `AI_communication/management/commands/seed_ai_data.py`: idempotent seed command.
- Modify `insert_sample_data.py`: compatibility wrapper around the seed function.
- Create `render.yaml`: reproducible Render build/start configuration.
- Modify `.env.example` and `README.md`: document environment variables and deployment.
- Modify `tests/test_settings.py`: isolated environment tests for production settings.
- Create `tests/test_seed_ai_data.py`: command idempotency test.
- Create `tests/test_profile_upload.py`: upload failure regression test.
- Create `tests/test_deployment_files.py`: Render configuration and dependency assertions.

### Task 1: Production database, static files and security settings

**Files:**
- Modify: `requirements.txt`
- Modify: `mangowit/settings.py`
- Modify: `tests/test_settings.py`

- [ ] **Step 1: Add failing settings tests**

Extend the subprocess helper so it can print selected settings, then assert that `DATABASE_URL=postgresql://user:pass@db.example/mangowit` selects `django.db.backends.postgresql`, that `CLOUDINARY_URL` selects `cloudinary_storage.storage.MediaCloudinaryStorage`, and that `MANGOWIT_DEBUG=false` enables secure cookies and proxy HTTPS handling.

- [ ] **Step 2: Run the targeted tests and verify failure**

Run: `.venv/bin/python manage.py test tests.test_settings -v 2`

Expected: failures because `DATABASE_URL`, Cloudinary storage and production security settings are not implemented.

- [ ] **Step 3: Add production dependencies**

Add these entries to `requirements.txt`:

```text
gunicorn>=23.0,<24
whitenoise>=6.8,<7
dj-database-url>=2.3,<3
psycopg[binary]>=3.2,<4
cloudinary>=1.41,<2
django-cloudinary-storage>=0.3,<0.4
```

- [ ] **Step 4: Implement environment-driven settings**

In `mangowit/settings.py`, import `dj_database_url`, insert `whitenoise.middleware.WhiteNoiseMiddleware` immediately after `SecurityMiddleware`, and use:

```python
database_url = os.getenv("DATABASE_URL")
if database_url:
    DATABASES = {
        "default": dj_database_url.parse(
            database_url,
            conn_max_age=600,
            ssl_require=not DEBUG,
        )
    }
elif os.getenv("MANGOWIT_DB_ENGINE", "sqlite").strip().lower() == "mysql":
    # retain the existing MySQL mapping
else:
    # retain the existing SQLite mapping

STORAGES = {
    "default": {
        "BACKEND": (
            "cloudinary_storage.storage.MediaCloudinaryStorage"
            if os.getenv("CLOUDINARY_URL")
            else "django.core.files.storage.FileSystemStorage"
        )
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}
STATIC_ROOT = BASE_DIR / "staticfiles"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("MANGOWIT_CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]
```

- [ ] **Step 5: Install dependencies and run the settings tests**

Run: `.venv/bin/python -m pip install -r requirements.txt && .venv/bin/python manage.py test tests.test_settings -v 2`

Expected: all settings tests pass.

- [ ] **Step 6: Commit**

```bash
git add requirements.txt mangowit/settings.py tests/test_settings.py
git commit -m "feat: add production runtime settings"
```

### Task 2: Idempotent production seed command

**Files:**
- Create: `AI_communication/seed_data.py`
- Create: `AI_communication/management/__init__.py`
- Create: `AI_communication/management/commands/__init__.py`
- Create: `AI_communication/management/commands/seed_ai_data.py`
- Modify: `insert_sample_data.py`
- Create: `tests/test_seed_ai_data.py`

- [ ] **Step 1: Write the failing idempotency test**

Create a `TestCase` that runs `call_command("seed_ai_data")` twice and asserts exactly 21 `AIQuestion` and 21 `AIAnswer` rows exist, with every question linked to one answer.

- [ ] **Step 2: Verify the command is missing**

Run: `.venv/bin/python manage.py test tests.test_seed_ai_data -v 2`

Expected: failure reporting unknown command `seed_ai_data`.

- [ ] **Step 3: Extract and implement the seed service**

Move the 21 question/answer dictionaries into `AI_communication/seed_data.py` as `QUESTIONS_AND_ANSWERS`. Implement:

```python
from django.db import transaction
from .models import AIAnswer, AIQuestion

@transaction.atomic
def seed_ai_data():
    for item in QUESTIONS_AND_ANSWERS:
        question, _ = AIQuestion.objects.get_or_create(
            question_text=item["question"]
        )
        AIAnswer.objects.update_or_create(
            question=question,
            defaults={"answer_text": item["answer"]},
        )
```

The management command calls this function and prints a success message. `insert_sample_data.py` becomes a thin compatibility entry point that initializes Django and calls the same function.

- [ ] **Step 4: Run the seed tests**

Run: `.venv/bin/python manage.py test tests.test_seed_ai_data -v 2`

Expected: one test passes and both row counts equal 21 after two executions.

- [ ] **Step 5: Commit**

```bash
git add AI_communication insert_sample_data.py tests/test_seed_ai_data.py
git commit -m "feat: add idempotent AI seed command"
```

### Task 3: Preserve profiles when cloud image upload fails

**Files:**
- Modify: `sex_education_app/views.py`
- Create: `tests/test_profile_upload.py`

- [ ] **Step 1: Write the failing regression test**

Create a logged-in user with an existing avatar name. Submit the profile form with a valid in-memory PNG while patching the active storage `save` method to raise `cloudinary.exceptions.Error("upload failed")`. Assert the response remains 200, contains a user-facing upload error, and the refreshed user still references the original avatar.

- [ ] **Step 2: Run the test and verify the unhandled error**

Run: `.venv/bin/python manage.py test tests.test_profile_upload -v 2`

Expected: test fails because the Cloudinary exception escapes the view.

- [ ] **Step 3: Catch the Cloudinary upload error narrowly**

Import `cloudinary.exceptions.Error as CloudinaryError`. Wrap only `form.save()` in `try/except CloudinaryError`; on failure add `messages.error(request, "头像上传失败，请稍后重试。")`, rebuild the bound form from the submitted text fields without the failed file, and render the profile template without redirecting. Do not catch database or programming errors.

- [ ] **Step 4: Run the upload and route tests**

Run: `.venv/bin/python manage.py test tests.test_profile_upload tests.test_entry_routes -v 2`

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add sex_education_app/views.py tests/test_profile_upload.py
git commit -m "fix: preserve profile on avatar upload failure"
```

### Task 4: Render deployment manifest and documentation

**Files:**
- Create: `render.yaml`
- Modify: `.env.example`
- Modify: `README.md`
- Create: `tests/test_deployment_files.py`

- [ ] **Step 1: Write failing deployment-file tests**

Assert `render.yaml` declares a Python web service named `mangowit`, free plan, `/` health check, a build command containing `collectstatic`, and a start command containing `migrate`, `seed_ai_data`, and Gunicorn. Assert every non-built-in command is present in `requirements.txt`.

- [ ] **Step 2: Run the test and verify failure**

Run: `.venv/bin/python manage.py test tests.test_deployment_files -v 2`

Expected: failure because `render.yaml` does not exist.

- [ ] **Step 3: Add the Render Blueprint**

Create `render.yaml` with:

```yaml
services:
  - type: web
    name: mangowit
    runtime: python
    plan: free
    buildCommand: pip install -r requirements.txt && python manage.py collectstatic --noinput
    startCommand: python manage.py migrate && python manage.py seed_ai_data && gunicorn mangowit.wsgi:application --bind 0.0.0.0:$PORT
    healthCheckPath: /
    envVars:
      - key: PYTHON_VERSION
        value: 3.13.7
      - key: MANGOWIT_DEBUG
        value: "false"
      - key: MANGOWIT_SECRET_KEY
        generateValue: true
      - key: MANGOWIT_ALLOWED_HOSTS
        value: .onrender.com
      - key: MANGOWIT_CSRF_TRUSTED_ORIGINS
        value: https://*.onrender.com
      - key: DATABASE_URL
        sync: false
      - key: CLOUDINARY_URL
        sync: false
```

- [ ] **Step 4: Document local and production setup**

Add `DATABASE_URL`, `CLOUDINARY_URL`, and `MANGOWIT_CSRF_TRUSTED_ORIGINS` placeholders to `.env.example`. Update README to use local port 8001, describe the Render/Neon/Cloudinary architecture, list secrets that must be entered in Render, and state that free Render services sleep after inactivity.

- [ ] **Step 5: Run deployment-file tests**

Run: `.venv/bin/python manage.py test tests.test_deployment_files -v 2`

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add render.yaml .env.example README.md tests/test_deployment_files.py
git commit -m "docs: add Render deployment blueprint"
```

### Task 5: Full verification and GitHub update

**Files:**
- Verify all changed files.

- [ ] **Step 1: Run formatting-independent repository checks**

Run: `git diff --check && .venv/bin/python manage.py makemigrations --check --dry-run`

Expected: no whitespace errors and `No changes detected`.

- [ ] **Step 2: Run the complete Django suite**

Run: `.venv/bin/python manage.py check && .venv/bin/python manage.py test -v 2`

Expected: system check reports no issues and all tests pass.

- [ ] **Step 3: Validate production static collection**

Run: `MANGOWIT_DEBUG=false MANGOWIT_SECRET_KEY=test MANGOWIT_ALLOWED_HOSTS=.onrender.com .venv/bin/python manage.py collectstatic --noinput`

Expected: static files are collected into `staticfiles/` without an exception.

- [ ] **Step 4: Push main**

Run: `git push origin main`

Expected: GitHub `main` advances to the verified local commit.

### Task 6: Provision free cloud services and verify persistence

**External configuration:** Neon, Cloudinary, Render.

- [ ] **Step 1: Create Neon PostgreSQL project**

Sign in using the user's GitHub identity, create a free project named `mangowit`, and copy its pooled PostgreSQL connection string without exposing it in chat, logs or Git.

- [ ] **Step 2: Create Cloudinary product environment**

Sign in, create the free product environment, and copy its `CLOUDINARY_URL` secret without exposing it in chat, logs or Git.

- [ ] **Step 3: Create the Render Web Service**

Connect private repository `chagou313/mangowit`, select the repository Blueprint, enter `DATABASE_URL` and `CLOUDINARY_URL` as secret environment values, and launch the free service.

- [ ] **Step 4: Verify deployment logs**

Confirm dependency installation, `collectstatic`, migrations, 21-item seed command and Gunicorn startup succeed. Confirm logs do not print either secret.

- [ ] **Step 5: Run browser smoke checks**

Open the public HTTPS URL and verify the homepage, `/news/`, `/knowledge/`, `/category_select/`, `/community/`, registration, login and profile pages.

- [ ] **Step 6: Verify persistence**

Register a dedicated deployment-test user, create a community topic, upload a small generated avatar, trigger a manual redeploy, then confirm the same account can log in and both the topic and avatar remain present. Remove only the deployment-test content after verification.

- [ ] **Step 7: Record the public URL**

Add the live URL to the GitHub repository About section and README, commit and push the documentation update, then provide the URL to the user.
