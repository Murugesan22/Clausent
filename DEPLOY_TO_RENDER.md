# Deploying CLAUSENT to Render via GitHub 🚀

This guide explains how to push **CLAUSENT** to GitHub and deploy it smoothly to [Render](https://render.com) as a full-stack production application.

---

## 🏗️ Architecture on Render

CLAUSENT is configured to deploy as a **unified full-stack service**:
- **Frontend:** React + Vite SPA (compiled to static production assets)
- **Backend:** FastAPI (Python 3.11) serving API endpoints under `/api` and serving the React frontend on `/`
- **Containerization:** Multi-stage `Dockerfile` (Node 20 for compiling frontend + Python 3.11-slim for backend)
- **Zero CORS issues:** Both frontend and backend share the same origin on Render (`https://<your-service>.onrender.com`).
- **Free Tier Compatible:** Uses lightweight CPU-optimized PyTorch wheels and deterministic AI fallbacks so it never exceeds Render's 512 MB RAM limit.

---

## Step 1: Push Your Code to GitHub

Open a terminal (PowerShell, Command Prompt, or Git Bash) in your project root:

```powershell
# 1. Initialize git (if not already done)
git init

# 2. Stage all project files
git add .

# 3. Create your initial commit
git commit -m "Configure full-stack CLAUSENT for Render deployment"

# 4. Create a new repository on https://github.com/new (e.g. named clausent-app)

# 5. Set the default branch to main and link your remote
git branch -M main
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/<YOUR_REPOSITORY_NAME>.git

# 6. Push to GitHub
git push -u origin main
```

> **Note:** Sensitive items (`.env`, `clausent.db`, `node_modules/`, `backend/.venv/`, and temporary uploads) are already safely excluded in `.gitignore`.

---

## Step 2: Deploy on Render

### Method A: Web Service via Dockerfile (Recommended & Simplest)

1. Sign up or log in to **[Render Dashboard](https://dashboard.render.com/)**.
2. Click **New +** in the top right and select **Web Service**.
3. Choose **Build and deploy from a Git repository** and connect your GitHub repository.
4. Fill in the following details:
   - **Name:** `clausent` (or any name you choose)
   - **Region:** Choose the region closest to you (e.g., `Singapore`, `Frankfurt`, or `Oregon`)
   - **Branch:** `main`
   - **Root Directory:** Leave blank (root of repo)
   - **Runtime:** **Docker** *(Render will automatically detect the `Dockerfile`)*
   - **Instance Type:** **Free** (0.5 CPU, 512 MB RAM)
5. Under **Environment Variables**, you can optionally add or customize:
   | Key | Default Value | Description |
   | --- | --- | --- |
   | `APP_ENV` | `production` | Sets app environment mode |
   | `DEBUG` | `False` | Disables verbose debug reload |
   | `ENABLE_LEGAL_BERT` | `False` | Keeps memory usage under 250 MB on Free Tier |
   | `SLM_PROVIDER` | `mock_local` | High-speed plain-language explanation engine |
   | `LLM_PROVIDER` | `mock_local` | Heuristic legal counsel engine (or `gemini`, `openai`) |
   | `LLM_API_KEY` | *(Optional)* | Your Gemini or OpenAI API key if using live cloud LLM |
6. Click **Deploy Web Service**.
7. Render will build the React frontend, install backend requirements, and start your container. Once live, Render displays your URL:
   ```
   https://clausent.onrender.com
   ```

---

### Method B: Render Blueprint (Infrastructure-as-Code)

If you prefer automated setup using the included [`render.yaml`](./render.yaml):
1. In the Render Dashboard, click **New +** -> **Blueprint**.
2. Connect your GitHub repository.
3. Render reads `render.yaml` automatically and configures the service, ports, and environment variables.
4. Click **Apply**.

---

## Step 3: Verify the Live Deployment

Once the build finishes and shows `Live`:
1. **Open the Web App:** Navigate to `https://<your-app-name>.onrender.com`. You should see the complete CLAUSENT interface.
2. **Verify Backend Status:** In the top navigation bar, the status pill will glow green: `AI Engine Active`.
3. **Verify API Docs:** Navigate to `https://<your-app-name>.onrender.com/docs` to test the interactive Swagger API documentation.
4. **Run a Test Analysis:**
   - Upload a test agreement (`.txt`, `.pdf`, or `.docx`) or use the built-in demo contracts.
   - Click **Run Full Analysis**.
   - Verify clause classification, risk scoring, multilingual translation, and report generation.

---

## 💡 Important Tips for Render Free Tier

1. **Spin-down Behavior:**
   - Render free web services spin down after 15 minutes of inactivity to conserve resources.
   - The first request after sleep may take ~30–50 seconds to wake up. Subsequent requests will be fast.
2. **Database Persistence:**
   - By default, SQLite stores data in the local container filesystem, which resets when the service rebuilds.
   - If you need persistent data across container redeployments:
     - In Render, create a **Free PostgreSQL Database** (`New +` -> `PostgreSQL`).
     - Copy the **Internal Database URL**.
     - In your CLAUSENT Web Service settings, add the environment variable `DATABASE_URL` with that value.
     - CLAUSENT will automatically adapt and connect to PostgreSQL.
3. **Memory Optimization:**
   - On free tier (512 MB RAM), keep `ENABLE_LEGAL_BERT=False`. The built-in deterministic legal-domain semantic representation delivers instant clause vectorization and CUAD categorization without risking out-of-memory errors.
   - If you want to use cloud LLMs (Gemini / OpenAI), simply add `LLM_PROVIDER=gemini` and `LLM_API_KEY=your_key` in Render's Environment tab.

---

## 🛠️ Local Development

To run locally across Windows, macOS, or Linux:
- **Frontend:** `npm run dev` (runs Vite dev server on `http://localhost:5173`)
- **Backend:** `cd backend && uvicorn app.main:app --reload` (runs FastAPI on `http://127.0.0.1:8000`)
- **Or Test Fullstack Container Locally:** `docker build -t clausent . && docker run -p 8000:8000 clausent`
