# 🚀 Render Deployment - Quick Start

## ✅ Fixed Issue

**Problem:** Blueprint couldn't auto-link Redis
**Solution:** Simplified - Redis created manually (takes 1 minute)

---

## 📋 Deployment Steps (Simple)

### 1. Push to GitHub ✅
```bash
git add .
git commit -m "Add Render deployment config"
git push origin main
```

### 2. Deploy Blueprint on Render

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub repo: `Mohitranag18/online_test`
4. Name: `yaksh`
5. Branch: `master`
6. Click **"Apply"**

✅ This creates:
- Web Service (`yaksh-backend`)
- Celery Worker (`yaksh-celery`)

### 3. Create Redis (1 minute)

1. Click **"New +"** → **"Redis"**
2. Name: `yaksh-redis`
3. Plan: **Free**
4. Region: Oregon (same as services)
5. Click **"Create Redis"**
6. **Copy the Internal Redis URL** (looks like: `redis://red-xxxxx:6379`)

### 4. Add Environment Variables

#### For Web Service (`yaksh-backend`):

Go to service → Environment → Add these:

```bash
# Database (Neon DB)
DATABASE_URL=postgresql://neondb_owner:npg_9HAJz7WwSEiC@ep-long-tree-ad7bfusc-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require

# Redis (from step 3)
REDIS_URL=redis://red-xxxxx:6379

# Render URLs (replace with your actual URL)
ALLOWED_HOSTS=yaksh-backend.onrender.com
DOMAIN_HOST=https://yaksh-backend.onrender.com

# Frontend URL (your Vercel URL)
CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app
```

#### For Celery Worker (`yaksh-celery`):

Go to service → Environment → Add these:

```bash
# Same database and Redis
DATABASE_URL=postgresql://neondb_owner:npg_9HAJz7WwSEiC@ep-long-tree-ad7bfusc-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require
REDIS_URL=redis://red-xxxxx:6379
```

Click **"Save Changes"** on both services.

### 5. Create Superuser

Once deployed, go to Web Service → Shell:

```bash
python manage.py createsuperuser
```

### 6. Configure Vercel Frontend

In Vercel → Settings → Environment Variables:

```bash
VITE_API_URL=https://yaksh-backend.onrender.com
```

Redeploy frontend.

---

## ✅ Done!

Visit:
- **Backend API:** https://yaksh-backend.onrender.com/api/
- **Admin:** https://yaksh-backend.onrender.com/admin
- **Frontend:** Your Vercel URL

---

## 💰 Cost: FREE

- Neon DB: FREE
- Render Redis: FREE
- Render Web: FREE
- Render Celery: FREE

**Total: $0/month** 🎉

---

## ⚡ Quick Troubleshooting

**Issue:** "Application failed to respond"
→ Check `ALLOWED_HOSTS` matches your Render URL

**Issue:** "CORS error"
→ Check `CORS_ALLOWED_ORIGINS` matches your Vercel URL

**Issue:** "Database error"
→ Check `DATABASE_URL` is correct in BOTH services

**Issue:** "Celery not working"
→ Check `REDIS_URL` is in BOTH services

---

## 📝 Summary

What we did:
1. ✅ Created render.yaml (Blueprint config)
2. ✅ Pushed to GitHub
3. ✅ Deployed Blueprint (creates Web + Celery)
4. ✅ Created Redis manually
5. ✅ Added environment variables
6. ✅ Created superuser

**Ready to use!** 🚀

