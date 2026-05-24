# 🛠️ Local Setup Guide - Yaksh Online Test Platform

**Complete step-by-step guide for setting up Yaksh locally on your machine using Python venv.**

---

## 📋 Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Project Setup](#2-project-setup)
3. [Virtual Environment (venv)](#3-virtual-environment-venv)
4. [Install Dependencies](#4-install-dependencies)
5. [Database Setup](#5-database-setup)
6. [Environment Configuration](#6-environment-configuration)
7. [Run Development Server](#7-run-development-server)
8. [Code Server Setup (Optional)](#8-code-server-setup-optional)
9. [Frontend Setup (Optional)](#9-frontend-setup-optional)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Prerequisites

### Required Software

- **Python 3.9+** (3.6, 3.7, 3.8, 3.9, 3.10, 3.11)
  - Check version: `python3 --version`
  - Download: https://www.python.org/downloads/

- **Git**
  - Check: `git --version`
  - Download: https://git-scm.com/downloads

- **Redis** (for Celery background tasks)
  - **macOS:**
    ```bash
    brew install redis
    brew services start redis
    ```
  - **Linux (Ubuntu/Debian):**
    ```bash
    sudo apt update
    sudo apt install redis-server
    sudo systemctl start redis
    sudo systemctl enable redis
    ```
  - **Linux (CentOS/RHEL):**
    ```bash
    sudo yum install redis
    sudo systemctl start redis
    sudo systemctl enable redis
    ```
  - **Windows:**
    - Download from: https://github.com/microsoftarchive/redis/releases
    - Or use WSL (Windows Subsystem for Linux)

- **Docker** (Optional - for code server)
  - Download: https://www.docker.com/get-started
  - Required only if you want to run code execution server

### Verify Prerequisites

```bash
# Check Python version
python3 --version  # Should be 3.9 or higher

# Check Git
git --version

# Check Redis
redis-cli ping  # Should return "PONG"

# Check Docker (optional)
docker --version
```

---

## 2. Project Setup

### Step 2.1: Clone Repository

```bash
# Navigate to your projects directory
cd ~/Desktop  # or wherever you keep projects

# Clone the repository
git clone https://github.com/Mohitranag18/online_test.git

# Navigate into project directory
cd online_test
```

### Step 2.2: Verify Project Structure

You should see these directories:
```
online_test/
├── api/              # API endpoints
├── frontend/         # React frontend
├── grades/           # Grading system
├── online_test/     # Django project settings
├── requirements/    # Python dependencies
├── yaksh/           # Main application
├── manage.py        # Django management script
├── tasks.py         # Invoke tasks
└── render.yaml      # Render deployment config
```

---

## 3. Virtual Environment (venv)

### Step 3.1: Create Virtual Environment

**macOS/Linux:**
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

**Windows:**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate
```

**After activation, you should see `(venv)` in your terminal prompt:**
```
(venv) user@computer:~/Desktop/online_test$
```

### Step 3.2: Upgrade Pip

```bash
# Upgrade pip to latest version
pip install --upgrade pip
```

### Step 3.3: Deactivate Virtual Environment (When Done)

```bash
# To deactivate virtual environment
deactivate
```

**Note:** Always activate the virtual environment before working on the project!

---

## 4. Install Dependencies

### Step 4.1: Install Common Dependencies

```bash
# Make sure venv is activated
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate    # Windows

# Install all dependencies
pip install -r requirements/requirements-common.txt
```

**This installs:**
- Django 3.1.7
- Celery 4.4.2
- Redis client
- Django REST Framework
- All other required packages

**Installation time:** ~5-10 minutes (depending on internet speed)

### Step 4.2: Verify Installation

```bash
# Check Django installation
python manage.py --version

# Check if all packages are installed
pip list | grep -i django
pip list | grep -i celery
```

### Step 4.3: Install Code Server Dependencies (Optional)

Only needed if you want to run the code execution server:

```bash
pip install -r requirements/requirements-codeserver.txt
```

---

## 5. Database Setup

### Step 5.1: Create Database Migrations

```bash
# Make sure venv is activated
source venv/bin/activate

# Create migration files
python manage.py makemigrations

# Apply migrations to database
python manage.py migrate
```

**Expected output:**
```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, sessions, yaksh, ...
Running migrations:
  Applying yaksh.0001_initial... OK
  Applying yaksh.0002_... OK
  ...
```

### Step 5.2: Create Superuser (Admin Account)

```bash
python manage.py createsuperuser
```

**Follow the prompts:**
```
Username: admin
Email address: admin@example.com
Password: ********
Password (again): ********
Superuser created successfully.
```

**Save these credentials!** You'll need them to access the admin panel.

### Step 5.3: Load Demo Data (Optional)

If you want sample courses, quizzes, and users:

```bash
# Load demo fixtures
python manage.py loaddata yaksh/fixtures/demo_fixtures.json
```

**Note:** This will create sample data including:
- Demo courses
- Sample quizzes
- Test users (teacher1, student1, etc.)

---

## 6. Environment Configuration

### Step 6.1: Create Environment File

Create a `.env` file in the project root (copy from `.sampleenv`):

```bash
# Copy sample environment file
cp .sampleenv .env

# Edit .env file (optional - defaults work for local dev)
nano .env  # or use your preferred editor
```

### Step 6.2: Environment Variables

**Default `.env` file:**
```bash
# Django settings
SECRET_KEY=dUmMy_s3cR3t_k3y

# Database (SQLite by default - no config needed)
# For MySQL/PostgreSQL, uncomment and configure:
#DB_ENGINE=mysql
#DB_NAME=yaksh
#DB_USER=root
#DB_PASSWORD=root
#DB_HOST=localhost
#DB_PORT=3306

# Code Server Settings
N_CODE_SERVERS=5
#SERVER_POOL_PORT=53579
#SERVER_HOST_NAME=http://localhost
#SERVER_TIMEOUT=4
```

**For local development, defaults are fine!** SQLite database will be created automatically.

---

## 7. Run Development Server

### Step 7.1: Start Redis (Required for Celery)

**macOS:**
```bash
brew services start redis
# OR
redis-server
```

**Linux:**
```bash
sudo systemctl start redis
# OR
redis-server
```

**Verify Redis is running:**
```bash
redis-cli ping
# Should return: PONG
```

### Step 7.2: Start Celery Worker (Background Tasks)

Open a **new terminal window** (keep Redis terminal open):

```bash
# Navigate to project
cd ~/Desktop/online_test

# Activate venv
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate    # Windows

# Start Celery worker with beat scheduler
celery -A online_test worker -B
```

**Expected output:**
```
celery@hostname v4.4.2 (singularity)

[config]
.> app:         online_test:0x...
.> transport:   redis://localhost:6379/0
.> results:     django-db://
.> concurrency: 4 (prefork)
.> task events: ON

[tasks]
  . yaksh.tasks.regrade_papers
  . yaksh.tasks.update_user_marks
  ...

[2024-XX-XX XX:XX:XX,XXX: INFO/MainProcess] Connected to redis://localhost:6379/0
[2024-XX-XX XX:XX:XX,XXX: INFO/MainProcess] celery@hostname ready.
```

**Keep this terminal open!** Celery needs to run in the background.

### Step 7.3: Start Django Development Server

Open **another new terminal window**:

```bash
# Navigate to project
cd ~/Desktop/online_test

# Activate venv
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate    # Windows

# Start Django server
python manage.py runserver
```

**Expected output:**
```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
December 15, 2024 - XX:XX:XX
Django version 3.1.7, using settings 'online_test.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

### Step 7.4: Access the Application

Open your browser and visit:

- **Home/Exam Interface:** http://127.0.0.1:8000/exam/
- **Admin Panel:** http://127.0.0.1:8000/admin/
- **API Root:** http://127.0.0.1:8000/api/

**Login with superuser credentials** you created in Step 5.2.

---

## 8. Code Server Setup (Optional)

The code server allows students to execute Python, C++, Java, etc. code in quizzes.

### Option A: Using Docker (Recommended)

**Prerequisites:** Docker must be installed and running.

#### Step 8.1: Pull Docker Image

```bash
# Make sure venv is activated
source venv/bin/activate

# Pull the code server image (happens automatically)
invoke start
```

**This will:**
- Pull `fossee/yaksh_codeserver` Docker image
- Create and run a Docker container
- Bind ports for code execution
- Wait for server to be ready

**Expected output:**
```
** Pulling latest image <fossee/yaksh_codeserver> from docker hub **
** Preparing code server **
** Initializing code server within docker container **
** Checking code server status. Press Ctrl-C to exit **
** Code server is up and running successfully **
```

#### Step 8.2: Stop Code Server

```bash
invoke stop
```

### Option B: Using Invoke Tasks

The `tasks.py` file provides convenient commands:

```bash
# Activate venv first
source venv/bin/activate

# Setup database and load fixtures, then start server
invoke serve

# Setup database only
invoke setupdb

# Load fixtures only
invoke loadfixtures

# Start code server (Docker)
invoke start

# Stop code server
invoke stop

# List all available tasks
invoke --list
```

---

## 9. Frontend Setup (Optional)

If you want to run the React frontend locally:

### Step 9.1: Install Node.js

- Download: https://nodejs.org/
- Version: 16+ recommended
- Verify: `node --version` and `npm --version`

### Step 9.2: Install Frontend Dependencies

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
```

**Installation time:** ~2-5 minutes

### Step 9.3: Create Environment File

Create `frontend/.env`:

```bash
# Backend API URL
VITE_API_URL=http://localhost:8000
```

### Step 9.4: Run Frontend Development Server

```bash
# Make sure you're in frontend directory
cd frontend

# Start development server
npm run dev
```

**Expected output:**
```
  VITE v7.2.2  ready in XXX ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

**Access frontend:** http://localhost:5173/

---

## 10. Troubleshooting

### Issue 1: "No module named 'venv'"

**Solution:**
```bash
# Install venv module
python3 -m pip install --user virtualenv

# Then create venv
python3 -m venv venv
```

### Issue 2: "Permission denied" when activating venv

**macOS/Linux:**
```bash
# Make scripts executable
chmod +x venv/bin/activate
source venv/bin/activate
```

**Windows:**
- Run terminal as Administrator
- Or use: `venv\Scripts\activate.bat`

### Issue 3: "ModuleNotFoundError" after installation

**Solution:**
```bash
# Make sure venv is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements/requirements-common.txt
```

### Issue 4: "Redis connection refused"

**Solution:**
```bash
# Check if Redis is running
redis-cli ping

# If not running, start it:
# macOS:
brew services start redis

# Linux:
sudo systemctl start redis

# Windows:
# Start Redis service from Services panel
```

### Issue 5: "Port 8000 already in use"

**Solution:**
```bash
# Use a different port
python manage.py runserver 8001

# Or kill the process using port 8000
# macOS/Linux:
lsof -ti:8000 | xargs kill -9

# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Issue 6: "Database is locked" (SQLite)

**Solution:**
- Close any database browsers or other connections
- Restart the Django server
- If persistent, delete `db.sqlite3` and run migrations again:
  ```bash
  rm db.sqlite3
  python manage.py migrate
  python manage.py createsuperuser
  ```

### Issue 7: Celery not connecting to Redis

**Solution:**
```bash
# Check Redis is running
redis-cli ping

# Check Celery configuration in settings.py
# Verify CELERY_BROKER_URL = 'redis://localhost:6379/0'

# Restart Celery worker
# Press Ctrl+C to stop, then:
celery -A online_test worker -B
```

### Issue 8: Docker code server not starting

**Solution:**
```bash
# Check Docker is running
docker ps

# Check if image exists
docker images | grep yaksh

# Pull image manually
docker pull fossee/yaksh_codeserver

# Try starting again
invoke start
```

### Issue 9: Frontend not connecting to backend

**Solution:**
1. Check `frontend/.env` has correct `VITE_API_URL`
2. Make sure Django server is running on port 8000
3. Check CORS settings in `online_test/settings.py`:
   ```python
   CORS_ORIGIN_ALLOW_ALL = True  # For local dev
   ```
4. Restart both frontend and backend servers

### Issue 10: "pip install" fails with SSL errors

**Solution:**
```bash
# Upgrade pip, setuptools, wheel
pip install --upgrade pip setuptools wheel

# Try installing with trusted hosts
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements/requirements-common.txt
```

---

## 11. Quick Start Commands Reference

### Daily Development Workflow

```bash
# 1. Navigate to project
cd ~/Desktop/online_test

# 2. Activate virtual environment
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate    # Windows

# 3. Start Redis (if not running as service)
redis-server  # Keep this terminal open

# 4. Start Celery (new terminal)
cd ~/Desktop/online_test
source venv/bin/activate
celery -A online_test worker -B

# 5. Start Django server (new terminal)
cd ~/Desktop/online_test
source venv/bin/activate
python manage.py runserver

# 6. Start Frontend (optional, new terminal)
cd ~/Desktop/online_test/frontend
npm run dev
```

### Useful Django Commands

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load fixtures
python manage.py loaddata yaksh/fixtures/demo_fixtures.json

# Collect static files
python manage.py collectstatic

# Django shell
python manage.py shell

# Run tests
python manage.py test
```

### Useful Invoke Commands

```bash
# List all tasks
invoke --list

# Setup database and load fixtures, then serve
invoke serve

# Setup database only
invoke setupdb

# Load fixtures only
invoke loadfixtures

# Start code server (Docker)
invoke start

# Stop code server
invoke stop
```

---

## 12. Project Structure Overview

```
online_test/
├── api/                    # REST API endpoints
│   ├── urls.py            # API URL routing
│   ├── views.py            # API views
│   └── serializers.py     # API serializers
│
├── frontend/               # React frontend
│   ├── src/               # Source files
│   ├── public/            # Static assets
│   ├── package.json       # Node dependencies
│   └── vite.config.js     # Vite configuration
│
├── grades/                 # Grading system app
│   ├── models.py          # Grade models
│   └── views.py           # Grade views
│
├── online_test/           # Django project settings
│   ├── settings.py        # Main settings file
│   ├── urls.py            # Root URL config
│   └── wsgi.py            # WSGI config
│
├── requirements/           # Python dependencies
│   ├── requirements-common.txt      # Core dependencies
│   ├── requirements-codeserver.txt  # Code server deps
│   └── requirements-render.txt     # Production deps
│
├── yaksh/                  # Main application
│   ├── models.py          # Database models
│   ├── views.py           # Views
│   ├── forms.py           # Forms
│   ├── templates/         # HTML templates
│   ├── static/            # Static files (CSS, JS)
│   ├── fixtures/          # Sample data
│   └── migrations/        # Database migrations
│
├── manage.py              # Django management script
├── tasks.py               # Invoke task definitions
├── .env                   # Environment variables (create this)
└── db.sqlite3             # SQLite database (created after migrate)
```

---

## 13. Next Steps

### After Successful Setup

1. **Access Admin Panel:**
   - URL: http://127.0.0.1:8000/admin/
   - Login with superuser credentials

2. **Create Your First Course:**
   - Go to Admin → Courses → Add Course
   - Fill in course details
   - Save

3. **Create a Quiz:**
   - Go to Admin → Quizzes → Add Quiz
   - Link to your course
   - Add questions

4. **Test Student Experience:**
   - Visit: http://127.0.0.1:8000/exam/
   - Create a student account
   - Enroll in course
   - Take a quiz

5. **Explore API:**
   - Visit: http://127.0.0.1:8000/api/
   - Use API for frontend integration

### Learning Resources

- **Django Documentation:** https://docs.djangoproject.com/
- **Yaksh Documentation:** http://yaksh.readthedocs.io
- **Django REST Framework:** https://www.django-rest-framework.org/

---

## 14. Summary Checklist

Use this checklist to verify your setup:

- [ ] Python 3.9+ installed
- [ ] Git installed
- [ ] Redis installed and running
- [ ] Project cloned from GitHub
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`requirements-common.txt`)
- [ ] Database migrations applied
- [ ] Superuser created
- [ ] Redis service running
- [ ] Celery worker running
- [ ] Django server running on port 8000
- [ ] Can access http://127.0.0.1:8000/exam/
- [ ] Can login to admin panel
- [ ] (Optional) Code server running (Docker)
- [ ] (Optional) Frontend running on port 5173

---

## 🎉 Setup Complete!

Your local development environment is ready! You can now:

- ✅ Create courses and quizzes
- ✅ Test student functionality
- ✅ Develop new features
- ✅ Run tests
- ✅ Access admin panel

**Happy coding!** 🚀

For deployment to production, see `COMPLETE_DEPLOYMENT_GUIDE.md`.

