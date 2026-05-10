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

### Backend (Google Cloud Run)
1. Build and push the backend image to GCR/AR.
2. Deploy to Cloud Run with `DATABASE_URL` pointing to your Cloud SQL instance.

### Frontend (Vercel)
1. Connect your repo to Vercel.
2. Set `NEXT_PUBLIC_API_URL` to your Cloud Run URL.

### Database (Neon/Postgres)
1. Set up a PostgreSQL instance on Neon or Google Cloud SQL.

---

Built with ❤️ for Aurvyz.
