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

You can deploy the backend using either **Render Blueprints (Automated via `render.yaml`)** or **Manual Web Service Configuration**.

### Option 1: Render Blueprint (Recommended)
1. In the [Render Dashboard](https://dashboard.render.com), click **New +** → **Blueprint**.
2. Connect your GitHub repository (`ClassVortex`).
3. Render will automatically read `render.yaml`, set the root directory to `backend`, configure Python 3.11.9, and apply the build and start commands.

### Option 2: Manual Web Service Setup
1. In the [Render Dashboard](https://dashboard.render.com), click **New +** → **Web Service**.
2. Connect your GitHub repository.
3. Configure the following critical settings:
   - **Name**: `attendvortex-api` (or preferred name)
   - **Region**: Choose the region closest to your MongoDB Atlas cluster.
   - **Root Directory**: `backend` *(CRITICAL: Must be set to `backend` since the FastAPI app and requirements.txt are inside `backend/`)*
   - **Runtime**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

> **Note on Root Directory**: If you see `ERROR: Could not open requirements file: [Errno 2] No such file or directory: 'requirements.txt'`, your Render Web Service is building from the repo root instead of `backend/`. Go to **Settings** → **Build & Deploy** → **Root Directory** in the Render service dashboard and enter `backend`.

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

## D. Frontend Deployment Setup

### Option 1: Vercel (Recommended for Next.js)
1. **Import Project into Vercel**:
   - Go to [Vercel Dashboard](https://vercel.com) and click **Add New...** → **Project**.
   - Select your repository (`ClassVortex`).
2. **Configure Project Settings**:
   - **Framework Preset**: `Next.js`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Environment Variable**: `NEXT_PUBLIC_API_URL=https://<your-backend-app>.onrender.com/api/v1`

### Option 2: Render (Next.js Web Service)
1. In the [Render Dashboard](https://dashboard.render.com), click **New +** → **Web Service**.
2. Connect your GitHub repository.
3. Configure settings:
   - **Name**: `attendvortex-frontend`
   - **Root Directory**: `frontend`
   - **Runtime**: `Node`
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: `npm run start`
   - **Environment Variable**: `NEXT_PUBLIC_API_URL=https://<your-backend-app>.onrender.com/api/v1`

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
