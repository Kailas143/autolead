# Aurvyz Outreach Automation Platform

Production-ready AI-powered outreach automation platform.

## 🚀 Features

- **Apollo CSV Import**: Seamless lead importing with validation.
- **AI Personalization**: Gemini-powered intro lines and company outreach.
- **Campaign Automation**: Scheduled sequences with customizable delays.
- **Reply Classification**: Automatic labeling of replies (Interested, Later, etc.).
- **Smart Inbox**: Unified view of all engagement.
- **Detailed Analytics**: Track opens, clicks, and reply sentiment.

## 🧠 Tech Stack

- **Frontend**: Next.js 15 (App Router), TypeScript, Tailwind CSS, shadcn/ui.
- **Backend**: FastAPI, SQLAlchemy, Pydantic, Celery, Redis, PostgreSQL.
- **AI**: Google Gemini API.
- **Email**: Resend API.
- **Infrastructure**: Docker & Docker Compose.

## 🛠️ Local Setup

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd autolead
   ```


2. **Set up Environment Variables**:
   Create a `.env` file in the root directory and add the following:
   ```env
   DATABASE_URL=postgresql://postgres:password@db:5432/aurvyz
   REDIS_URL=redis://redis:6379/0
   CELERY_BROKER_URL=redis://redis:6379/0
   CELERY_RESULT_BACKEND=redis://redis:6379/0
   
   # API Keys
   GEMINI_API_KEY=your_gemini_api_key
   RESEND_API_KEY=your_resend_api_key
   
   # Security
   SECRET_KEY=your_super_secret_key
   ```

3. **Run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```

### 🛠️ Manual Setup (Without Docker)

If you prefer to run the components separately:

#### **1. Backend & Worker**
Navigate to the `backend` directory and install dependencies:
```bash
cd backend
pip install -r requirements.txt
```
If you want test tooling as well:
```bash
pip install -r requirements-dev.txt
```
Run the **FastAPI Server**:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Run the **Celery Worker** (in a separate terminal):
```bash
celery -A app.celery_app.celery_app worker --loglevel=info
```

#### **2. Frontend**
Navigate to the `frontend` directory and install dependencies:
```bash
cd frontend
npm install
```

Run the **Development Server**:
```bash
npm run dev
```

4. **Access the platform**:
   - Frontend: [http://localhost:3000](http://localhost:3000)
   - Backend API: [http://localhost:8000](http://localhost:8000)
   - API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## 🚢 Deployment

### Google Artifact Registry + Cloud Run
This repository now includes a production deployment path for:

GitHub/Gitea -> Jenkins or GitHub Actions -> Docker Build -> Google Artifact Registry -> Cloud Run

- `frontend/Dockerfile.prod` builds the Next.js app for production and starts it with Node.
- `backend/cloudrun.env.yaml.example` shows the backend env vars expected by Cloud Run.
- `frontend/cloudrun.env.yaml.example` shows an optional frontend env file shape.
- `Jenkinsfile` can build images, push them to Google Artifact Registry, and deploy backend and frontend services to Cloud Run.

#### Jenkins credentials and variables
Configure these in Jenkins before enabling deployment:

- `GCP_SA_CREDENTIALS_ID`: Jenkins secret file credential id containing a Google Cloud service account JSON key.
- `GCP_PROJECT_ID`: Your Google Cloud project id.
- `BACKEND_ENV_VARS_FILE_CREDENTIALS_ID`: Jenkins secret file credential id containing the backend Cloud Run env vars YAML.
- `FRONTEND_API_URL`: Public backend API URL used at frontend image build time, for example `https://backend-xyz.a.run.app/api/v1`.

Optional Jenkins environment variables:

- `GAR_REGION`: Defaults to `asia-south1`.
- `GAR_REPOSITORY`: Defaults to `autolead`.
- `CLOUD_RUN_REGION`: Defaults to `asia-south1`.
- `BACKEND_SERVICE_NAME`: Defaults to `autolead-backend`.
- `FRONTEND_SERVICE_NAME`: Defaults to `autolead-frontend`.
- `DEPLOY_BRANCH`: Defaults to `main`.

#### Google Cloud preparation
1. Create an Artifact Registry Docker repository.
2. Enable the Cloud Run and Artifact Registry APIs.
3. Create a service account with Artifact Registry write access and Cloud Run admin access.
4. Store that service account JSON in Jenkins as `GCP_SA_CREDENTIALS_ID`.
5. Create a Jenkins secret file from [backend/cloudrun.env.yaml.example](/home/dell/autolead/backend/cloudrun.env.yaml.example) filled with real values.

#### Deployment flow
1. Jenkins builds the backend image from `backend/Dockerfile`.
2. Jenkins builds the frontend image from `frontend/Dockerfile.prod`, injecting `FRONTEND_API_URL` at build time.
3. Jenkins authenticates to Google Cloud and pushes both images to Artifact Registry with `${BUILD_NUMBER}` and `latest` tags.
4. Jenkins deploys the backend image to Cloud Run using the backend env vars file.
5. Jenkins deploys the frontend image to Cloud Run.

#### Production notes
- `NEXT_PUBLIC_API_URL` is compiled into the frontend bundle at build time, so set `FRONTEND_API_URL` correctly before the frontend image is built.
- **Worker**: The backend image is deployed as a second service (`autolead-worker`) with Always-on CPU to process Celery tasks.
- **Background Tasks**: Instead of Celery Beat, use **Cloud Scheduler** to trigger periodic tasks:
  1. Create a Cloud Scheduler job (Cron: `0 * * * *`).
  2. Target: `POST` to `https://your-backend-url/api/v1/campaigns/trigger-follow-ups`.
  3. Header: `X-Cron-Secret: <your-cron-secret>`.
- The `CRON_SECRET` must be set in your backend environment variables to match the Cloud Scheduler header.

---

Built with ❤️ for Aurvyz.
