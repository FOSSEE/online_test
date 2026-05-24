# 🚀 Complete Deployment Guide - Yaksh Online Test Platform

**This guide documents the complete setup and deployment process that worked successfully.**

---

## 📋 Table of Contents

1. [Local Setup (venv)](#1-local-setup-venv)
2. [Backend Deployment (Render)](#2-backend-deployment-render)
3. [Frontend Deployment (Vercel)](#3-frontend-deployment-vercel)
4. [Configuration & Environment Variables](#4-configuration--environment-variables)
5. [Issues Fixed & Solutions](#5-issues-fixed--solutions)
6. [Testing & Verification](#6-testing--verification)

---

## 1. Local Setup (venv)

### Prerequisites
- Python 3.9+ installed
- Git installed
- GitHub account

### Step 1.1: Clone Repository
```bash
cd /path/to/your/projects
git clone https://github.com/Mohitranag18/online_test.git
cd online_test
```

### Step 1.2: Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 1.3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements/requirements-common.txt
```

### Step 1.4: Setup Database (Local)
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py loaddata fixtures/*.json  # If you have fixtures
```

### Step 1.5: Run Development Server
```bash
python manage.py runserver
```

Visit: `http://localhost:8000`

---

## 2. Backend Deployment (Render)

### Step 2.1: Prepare for Deployment

#### 2.1.1: Create Production Requirements File
File: `requirements/requirements-render.txt`

This file combines common requirements + production-specific packages, **excluding Celery** (not available on free tier):

```txt
pytest
python-decouple
requests
tornado==4.5.3
psutil
nose==1.3.7
invoke==0.21.0
django==3.1.7
django-taggit==1.2.0
pytz==2019.3
requests-oauthlib>=0.6.1
social-auth-app-django==3.1.0
selenium==2.53.6
coverage
ruamel.yaml==0.16.10
pyyaml==5.3.1
markdown==2.6.9
pygments==2.2.0
redis==3.4.1
notifications-plugin==0.1.2
djangorestframework==3.11.2
django-cors-headers==3.1.0
Pillow
pandas>=1.3,<2.0
qrcode
more-itertools==8.4.0
django-storages==1.11.1
boto3==1.17.17
gunicorn
whitenoise
psycopg2-binary
dj-database-url==0.5.0
numpy<1.24
```

**Key Points:**
- ✅ Includes `gunicorn` (production WSGI server)
- ✅ Includes `whitenoise` (static file serving)
- ✅ Includes `psycopg2-binary` (PostgreSQL adapter)
- ✅ Includes `dj-database-url==0.5.0` (database URL parsing)
- ✅ **Excludes Celery** (not on free tier)
- ✅ Pins `numpy<1.24` and `pandas>=1.3,<2.0` (compatibility)

#### 2.1.2: Update settings.py for Production

The production configuration in `online_test/settings.py` should include:

```python
# At the bottom of settings.py
import dj_database_url

DEBUG = config('DEBUG', default=True, cast=bool)

if not DEBUG:
    print("Running in PRODUCTION mode")
    
    # Remove Celery apps (not available on free tier)
    INSTALLED_APPS = tuple(
        app for app in INSTALLED_APPS 
        if app not in ('django_celery_beat', 'django_celery_results')
    )
    
    # Security Settings
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Static Files with WhiteNoise
    MIDDLEWARE = list(MIDDLEWARE)
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
    MIDDLEWARE = tuple(MIDDLEWARE)
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
    
    # Database Configuration
    DATABASES['default'] = dj_database_url.config(
        default=config('DATABASE_URL'),
        conn_max_age=600,
    )
    
    # CORS Configuration - Allow all origins (for testing)
    CORS_ORIGIN_ALLOW_ALL = True
    CORS_ALLOW_CREDENTIALS = True
    
    # Allowed Hosts
    ALLOWED_HOSTS = [
        host.strip() 
        for host in config('ALLOWED_HOSTS', default='').split(',')
        if host.strip()
    ]
    
    # Domain Host
    DOMAIN_HOST = config('DOMAIN_HOST', default='https://your-app.onrender.com')
    
    print(f"ALLOWED_HOSTS: {ALLOWED_HOSTS}")
    print(f"DATABASE: {DATABASES['default']['NAME']}")
    print(f"CORS_ORIGIN_ALLOW_ALL: {CORS_ORIGIN_ALLOW_ALL}")
```

#### 2.1.3: Make Celery Imports Optional

**File: `online_test/__init__.py`**
```python
from __future__ import absolute_import, unicode_literals

try:
    from online_test.celery_settings import app as celery_app
except (ImportError, ModuleNotFoundError):
    celery_app = None  # Skip if Celery not available

__all__ = ('celery_app',)
__version__ = '0.31.1'
```

**File: `yaksh/views.py`**
```python
try:
    from online_test.celery_settings import app
except (ImportError, ModuleNotFoundError):
    app = None  # Celery not available
```

**File: `yaksh/tasks.py`**
```python
try:
    from celery import shared_task
except (ImportError, ModuleNotFoundError):
    def shared_task(func):
        """Dummy decorator when Celery is not available"""
        return func
```

#### 2.1.4: Create render.yaml

File: `render.yaml` (in project root):

```yaml
services:
  # Django Web Service
  - type: web
    name: yaksh-backend
    env: python
    plan: free
    buildCommand: |
      pip install --upgrade pip
      pip install -r requirements/requirements-render.txt
      python manage.py collectstatic --no-input
      python manage.py migrate
    startCommand: gunicorn online_test.wsgi:application --bind 0.0.0.0:$PORT --workers 4
    envVars:
      - key: PYTHON_VERSION
        value: 3.9.0
      - key: SECRET_KEY
        generateValue: true
      - key: DEBUG
        value: False
      - key: DATABASE_URL
        sync: false
      - key: REDIS_URL
        sync: false
```

**Key Points:**
- ✅ Uses `requirements-render.txt` (no Celery)
- ✅ Runs `collectstatic` and `migrate` during build
- ✅ Uses `gunicorn` with 4 workers
- ✅ Sets `DEBUG=False` for production
- ✅ `DATABASE_URL` and `REDIS_URL` must be set manually

### Step 2.2: Setup Neon Database (Free PostgreSQL)

1. Go to [https://neon.tech](https://neon.tech)
2. Sign up with GitHub
3. Create a new project
4. Copy the connection string (looks like):
   ```
   postgresql://neondb_owner:password@ep-xxx-xxx-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require
   ```
5. Save this for Step 2.4

### Step 2.3: Push to GitHub

```bash
git add .
git commit -m "Add Render deployment configuration"
git push origin master
```

### Step 2.4: Deploy on Render

1. Go to [https://dashboard.render.com](https://dashboard.render.com)
2. Sign up with GitHub
3. Click **"New +"** → **"Blueprint"**
4. Connect repository: `Mohitranag18/online_test`
5. Name: `yaksh` (or your choice)
6. Branch: `master`
7. Click **"Apply"**
8. Wait 5-10 minutes for deployment

**This creates:**
- ✅ Web Service (`yaksh-backend`)

**Note:** Celery worker is NOT created (not available on free tier)

### Step 2.5: Create Redis (Optional - for caching)

1. In Render Dashboard, click **"New +"** → **"Redis"**
2. Name: `yaksh-redis`
3. Plan: **Free**
4. Region: Same as your web service
5. Click **"Create Redis"**
6. Copy the **Internal Redis URL** (starts with `redis://`)

### Step 2.6: Add Environment Variables

Go to **yaksh-backend** service → **Environment** tab → Add:

```bash
# Database (from Neon)
DATABASE_URL=postgresql://neondb_owner:password@ep-xxx-xxx-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require

# Redis (from Step 2.5, or skip if not using)
REDIS_URL=redis://red-xxxxx:6379

# Backend URL (replace with your actual Render URL)
ALLOWED_HOSTS=yaksh-backend.onrender.com

# Domain for emails/links
DOMAIN_HOST=https://yaksh-backend.onrender.com

# Frontend URL (will be set after Vercel deployment)
CORS_ALLOWED_ORIGINS=https://yaksh-test.vercel.app
```

**Important:**
- Replace `yaksh-backend.onrender.com` with your actual Render URL
- Replace `yaksh-test.vercel.app` with your actual Vercel URL (after Step 3)
- Click **"Save Changes"** (triggers redeploy)

### Step 2.7: Create Superuser

Once deployment is **Live**:

1. Go to **yaksh-backend** → **Shell** tab
2. Run:
```bash
python manage.py createsuperuser
```
3. Follow prompts to create admin account

### Step 2.8: Verify Backend

Visit:
- **Admin Panel:** `https://yaksh-backend.onrender.com/admin`
- **API Root:** `https://yaksh-backend.onrender.com/api/`
- **Exam Interface:** `https://yaksh-backend.onrender.com/exam/`

---

## 3. Frontend Deployment (Vercel)

### Step 3.1: Prepare Frontend

Ensure your frontend is in the `frontend/` directory with:
- `package.json`
- `vite.config.js`
- `src/` directory

### Step 3.2: Sign Up for Vercel

1. Go to [https://vercel.com/signup](https://vercel.com/signup)
2. Click **"Continue with GitHub"**
3. Authorize Vercel

### Step 3.3: Import Project

1. In Vercel Dashboard, click **"Add New..."** → **"Project"**
2. Find your repository: `Mohitranag18/online_test`
3. Click **"Import"**

### Step 3.4: Configure Build Settings

**Framework Preset:** Vite

**Root Directory:** `frontend` (click "Edit" and type `frontend`)

**Build Command:** `npm run build` (default)

**Output Directory:** `dist` (default for Vite)

**Install Command:** `npm install` (default)

### Step 3.5: Add Environment Variable

Before deploying, add:

**Name:** `VITE_API_URL`
**Value:** `https://yaksh-backend.onrender.com` (your Render backend URL)

**For all environments:** Production, Preview, Development (check all three)

### Step 3.6: Deploy

1. Click **"Deploy"** button
2. Wait 2-3 minutes
3. You'll get a URL like: `https://yaksh-test-xxxxx.vercel.app`

### Step 3.7: Update Backend CORS

After getting your Vercel URL:

1. Go to Render → **yaksh-backend** → **Environment**
2. Update `CORS_ALLOWED_ORIGINS`:
   ```
   CORS_ALLOWED_ORIGINS=https://yaksh-test-xxxxx.vercel.app
   ```
3. Click **"Save Changes"** (triggers redeploy)

**Or** if you want to allow all origins (for testing):
- In `settings.py`, keep `CORS_ORIGIN_ALLOW_ALL = True`

### Step 3.8: Test Frontend

1. Visit your Vercel URL
2. Open DevTools (F12) → Console
3. Try **Sign Up** or **Login**
4. Check for CORS errors

---

## 4. Configuration & Environment Variables

### Backend (Render) - Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | Neon PostgreSQL connection string | `postgresql://user:pass@host/db?sslmode=require` |
| `SECRET_KEY` | Django secret key (auto-generated by Render) | (auto) |
| `DEBUG` | Debug mode (should be `False`) | `False` |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | `yaksh-backend.onrender.com` |
| `DOMAIN_HOST` | Full URL for emails/links | `https://yaksh-backend.onrender.com` |
| `CORS_ALLOWED_ORIGINS` | Frontend URL (or use `CORS_ORIGIN_ALLOW_ALL=True`) | `https://yaksh-test.vercel.app` |
| `REDIS_URL` | Redis connection (optional) | `redis://red-xxxxx:6379` |

### Frontend (Vercel) - Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `https://yaksh-backend.onrender.com` |

---

## 5. Issues Fixed & Solutions

### Issue 1: Celery Installation Error
**Error:** `celery 4.4.2 has invalid metadata: pytz>dev`

**Solution:**
- Created `requirements-render.txt` that excludes Celery
- Made Celery imports optional in code

### Issue 2: ModuleNotFoundError: No module named 'celery'
**Error:** Django couldn't start because Celery wasn't installed

**Solution:**
- Wrapped Celery imports in `try-except` blocks:
  - `online_test/__init__.py`
  - `yaksh/views.py`
  - `yaksh/tasks.py`

### Issue 3: numpy/pandas Compatibility
**Error:** `ValueError: numpy.dtype size changed`

**Solution:**
- Pinned `numpy<1.24` and `pandas>=1.3,<2.0` in `requirements-render.txt`

### Issue 4: dj-database-url Parameter Error
**Error:** `TypeError: config() got an unexpected keyword argument 'conn_health_checks'`

**Solution:**
- Removed `conn_health_checks=True` (not supported in `dj-database-url==0.5.0`)

### Issue 5: MIDDLEWARE Tuple Error
**Error:** `AttributeError: 'tuple' object has no attribute 'insert'`

**Solution:**
- Convert tuple to list, insert WhiteNoise, convert back to tuple

### Issue 6: Static Files Missing
**Error:** `whitenoise.storage.MissingFileError`

**Solution:**
- Changed `STATICFILES_STORAGE` from `CompressedManifestStaticFilesStorage` to `CompressedStaticFilesStorage`

### Issue 7: CORS Errors
**Error:** `Access to XMLHttpRequest blocked by CORS policy`

**Solution:**
- Set `CORS_ORIGIN_ALLOW_ALL = True` in production settings (for testing)
- Or set `CORS_ALLOWED_ORIGINS = ['https://your-frontend.vercel.app']`

### Issue 8: NameError in Print Statement
**Error:** `NameError: name 'CORS_ALLOWED_ORIGINS' is not defined`

**Solution:**
- Updated print statement to use `CORS_ORIGIN_ALLOW_ALL` instead

---

## 6. Testing & Verification

### Backend Tests

1. **Admin Panel:**
   - Visit: `https://yaksh-backend.onrender.com/admin`
   - Login with superuser credentials
   - Should see Django admin interface

2. **API Endpoints:**
   - Visit: `https://yaksh-backend.onrender.com/api/`
   - Should see API root
   - Test: `https://yaksh-backend.onrender.com/api/auth/login/`

3. **Health Check:**
   - Visit: `https://yaksh-backend.onrender.com/`
   - Should redirect to `/exam/`

### Frontend Tests

1. **Homepage:**
   - Visit your Vercel URL
   - Should load without errors

2. **Sign Up:**
   - Try creating a new account
   - Check browser console (F12) for errors
   - Should successfully create user

3. **Login:**
   - Try logging in
   - Should redirect to dashboard

4. **API Connection:**
   - Check Network tab in DevTools
   - API calls should return 200/201 status
   - No CORS errors

### Common Issues

**CORS still failing?**
- Clear browser cache (Cmd+Shift+R / Ctrl+Shift+R)
- Test in incognito/private window
- Verify `CORS_ORIGIN_ALLOW_ALL = True` in settings.py
- Check Render logs for CORS configuration

**Database errors?**
- Verify `DATABASE_URL` is correct
- Check Neon dashboard for connection status
- Run migrations in Render shell: `python manage.py migrate`

**Static files not loading?**
- WhiteNoise should handle this automatically
- Check Render logs for collectstatic output
- Verify `STATICFILES_STORAGE` setting

---

## 7. Final Checklist

### Backend (Render)
- [ ] `render.yaml` created and pushed
- [ ] `requirements-render.txt` created (no Celery)
- [ ] Production settings configured
- [ ] Celery imports made optional
- [ ] Neon database created
- [ ] Environment variables set
- [ ] Superuser created
- [ ] Service is Live

### Frontend (Vercel)
- [ ] Project imported from GitHub
- [ ] Root directory set to `frontend`
- [ ] `VITE_API_URL` environment variable set
- [ ] Deployed successfully
- [ ] CORS configured in backend

### Testing
- [ ] Backend admin accessible
- [ ] API endpoints working
- [ ] Frontend loads correctly
- [ ] Sign up works
- [ ] Login works
- [ ] No CORS errors

---

## 8. Cost Summary

**Total Cost: $0/month** 🎉

- ✅ Neon PostgreSQL: FREE (0.5GB storage, 3GB transfer/month)
- ✅ Render Web Service: FREE (sleeps after 15min inactivity)
- ✅ Render Redis: FREE (optional, for caching)
- ✅ Vercel Frontend: FREE (unlimited deployments, 100GB bandwidth)

**Limitations:**
- Render services wake up in ~30 seconds after sleep
- Shared resources (slower than paid tiers)
- Limited to 750 hours/month on Render free tier

---

## 9. Next Steps (Optional)

### Production Improvements

1. **Custom Domain:**
   - Add custom domain in Render and Vercel
   - Update `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS`

2. **Email Configuration:**
   - Configure SMTP settings in `settings.py`
   - Set `EMAIL_BACKEND`, `EMAIL_HOST`, etc.

3. **Monitoring:**
   - Set up error tracking (Sentry, etc.)
   - Monitor Render and Vercel dashboards

4. **Upgrade to Paid Tiers:**
   - Render Starter: $7/month (always-on web service)
   - Better performance, no sleep

---

## 10. Quick Reference

### Render Dashboard
- **URL:** https://dashboard.render.com
- **Services:** Web, Redis
- **Environment Variables:** Service → Environment tab
- **Shell:** Service → Shell tab
- **Logs:** Service → Logs tab

### Vercel Dashboard
- **URL:** https://vercel.com/dashboard
- **Projects:** Your imported projects
- **Environment Variables:** Project → Settings → Environment Variables
- **Deployments:** Project → Deployments tab

### Neon Dashboard
- **URL:** https://console.neon.tech
- **Projects:** Your database projects
- **Connection String:** Project → Connection Details

---

## 📝 Summary

**What We Did:**
1. ✅ Set up local environment with venv
2. ✅ Created production requirements (excluding Celery)
3. ✅ Updated settings.py for production
4. ✅ Made Celery imports optional
5. ✅ Created render.yaml for deployment
6. ✅ Set up Neon PostgreSQL database
7. ✅ Deployed backend on Render
8. ✅ Deployed frontend on Vercel
9. ✅ Configured CORS
10. ✅ Fixed all deployment issues

**Result:**
- ✅ Backend: Live on Render
- ✅ Frontend: Live on Vercel
- ✅ Database: Neon PostgreSQL
- ✅ Cost: $0/month
- ✅ Fully functional online test platform

---

**🎉 Deployment Complete! Your application is live and ready to use!**

For questions or issues, refer to the troubleshooting section or check the Render/Vercel logs.

