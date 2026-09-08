# AttendVortex — Production Deployment Guide

This guide details the steps to deploy AttendVortex to production using:
- **Database:** MongoDB Atlas (Cloud Database)
- **Backend:** Render (FastAPI / Uvicorn Python Web Service)
- **Frontend:** Vercel (Next.js Edge Deployment)

```
[ Vercel (Next.js Frontend) ]
              │
              │ HTTPS (NEXT_PUBLIC_API_URL)
              ▼
[ Render (FastAPI Backend) ]
              │
              │ TLS (MONGODB_URI)
              ▼
[ MongoDB Atlas (attendance_db) ]
```

---

## A. MongoDB Atlas Setup

1. **Create an Atlas Account & Cluster**:
   - Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) and sign in or create an account.
   - Deploy a free shared cluster (M0) or dedicated cluster in your preferred region.

2. **Configure Database Access (User Credentials)**:
   - Go to **Security** → **Database Access** → **Add New Database User**.
   - Authentication method: `Password`.
   - Set username (e.g. `attendvortex_user`) and a secure password.
   - Built-in role: `Read and write to any database`.

3. **Configure Network Access (IP Whitelist)**:
   - Go to **Security** → **Network Access** → **Add IP Address**.
   - Add `0.0.0.0/0` (Allow access from anywhere) so Render web instances can connect dynamically.

4. **Obtain Connection String**:
   - In **Databases**, click **Connect** → **Drivers** → Python (version 3.11 or later).
   - Copy the SRV connection URI. It will look like:
     ```
     mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
     ```
   - Replace `<username>` and `<password>` with your Atlas user credentials.

---

## B. Render Backend Setup

1. **Create Web Service**:
   - Log into [Render](https://render.com) and click **New +** → **Web Service**.
   - Connect your GitHub repository containing AttendVortex.

2. **Configure Service Details**:
   - **Name**: `attendvortex-api` (or preferred name)
   - **Region**: Choose the region closest to your MongoDB Atlas cluster.
   - **Root Directory**: `backend`
   - **Runtime**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

---

## C. Required Render Environment Variables

In the Render dashboard under **Environment**:

| Key | Example Value | Description |
|---|---|---|
| `APP_NAME` | `AttendVortex API` | Display name of the application |
| `APP_ENV` | `production` | Deployment mode |
| `DEBUG` | `false` | Disable debug stack traces |
| `MONGODB_URI` | `mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority` | Atlas SRV connection string |
| `MONGODB_DATABASE` | `attendance_db` | Target MongoDB database name |
| `JWT_SECRET_KEY` | *(generate strong 64-char random hex)* | JWT signature key |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Token validity duration |
| `CORS_ORIGINS` | `https://your-frontend.vercel.app` | Comma-separated list of allowed frontend domains |
| `EXPORT_DIRECTORY` | `exports` | Folder for temporary export files |

*(Optional: Run `python scripts/seed_dev_data.py` via Render Shell once to seed initial sample classes and students).*

---

## D. Vercel Frontend Setup

1. **Import Project into Vercel**:
   - Go to [Vercel Dashboard](https://vercel.com) and click **Add New...** → **Project**.
   - Select your repository.

2. **Configure Project Settings**:
   - **Framework Preset**: `Next.js`
   - **Root Directory**: Click **Edit** and set to `frontend`
   - **Build Command**: `npm run build` (or default Next.js build)
   - **Output Directory**: Next.js will automatically handle static exports.

---

## E. Required Vercel Environment Variable

In the Vercel dashboard under **Environment Variables**:

| Key | Example Value | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `https://attendvortex-api.onrender.com/api/v1` | Render backend URL ending in `/api/v1` |

*Ensure there are NO trailing slashes.*

---

## F. CORS Configuration

To prevent browser CORS rejections during authenticated requests:
1. Deploy the backend on Render to get the backend URL (`https://attendvortex-api.onrender.com`).
2. Deploy the frontend on Vercel with `NEXT_PUBLIC_API_URL=https://attendvortex-api.onrender.com/api/v1`.
3. Copy your assigned Vercel URL (e.g., `https://attendvortex.vercel.app`).
4. Update `CORS_ORIGINS` in Render environment variables:
   ```
   CORS_ORIGINS=https://attendvortex.vercel.app,http://localhost:3000
   ```
5. Render will automatically redeploy with the updated CORS policy.

---

## G. How to Verify the Deployed API

1. **Health Check**:
   ```bash
   curl -I https://attendvortex-api.onrender.com/health
   ```
   *Expected Response:* `HTTP/1.1 200 OK` with JSON `{"status":"healthy","app":"..."}`.

2. **Interactive Swagger Documentation**:
   Navigate to `https://attendvortex-api.onrender.com/docs` in your browser.

3. **Authentication Verification**:
   ```bash
   curl -X POST "https://attendvortex-api.onrender.com/api/v1/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"email":"admin@example.com","password":"your_password"}'
   ```
   *Expected Response:* `{"success": true, "data": {"access_token": "...", "token_type": "bearer"}}`.

---

## H. How to Verify the Deployed Frontend

1. Open your Vercel deployment URL in a browser: `https://your-frontend.vercel.app`.
2. Check browser DevTools console — verify 0 errors and no failed resource requests.
3. Sign in on `/login` using seeded admin/teacher credentials.
4. Verify `/dashboard` loads:
   - Real statistics appear.
   - Three.js 3D AttendVortex initializes with live percentage data.
5. Take attendance on `/attendance`:
   - Select class and subject.
   - Mark students and click **Save Attendance**.
   - Verify success confirmation.
6. Verify `/reports` and test CSV / Excel downloads.
