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
- **Backend**: FastAPI, SQLAlchemy, Pydantic, Redis, PostgreSQL.
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
   
   # API Keys
   GEMINI_API_KEY=your_gemini_api_key
   RESEND_API_KEY=your_resend_api_key
   
   # Security
   SECRET_KEY=your_super_secret_key
   ```

   > Note: If you change the database schema, run Alembic migrations from the `backend` folder:
   > `cd backend && alembic upgrade head`
   >
   > For an existing database that is already in sync with the current models, you can stamp the current head instead of reapplying migrations:
   > `cd backend && alembic stamp head`


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
uvicorn app.main:app --host [IP_ADDRESS] --port 8000 --reload
```



#### **2. Frontend**
Navigate to the `frontend` directory and install dependencies:
```bash
cd frontend
npm install
```

   ,
Run the **Development Server**:
```bash
npm run dev
```

4. **Access the platform**:

### 🌐 Production
- **Frontend**: [https://autolead-frontend-145662328298.asia-south1.run.app](https://autolead-frontend-145662328298.asia-south1.run.app)
- **Backend API**: [https://autolead-backend-145662328298.asia-south1.run.app](https://autolead-backend-145662328298.asia-south1.run.app)
- **API Docs**: [https://autolead-backend-145662328298.asia-south1.run.app/docs](https://autolead-backend-145662328298.asia-south1.run.app/docs)

### 💻 Local Development
- **Frontend**: [http://localhost:3000](http://localhost:3000)
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

## 🚢 Deployment

### AWS EC2 / VPS Deployment
This project is designed to be easily deployed on a standard AWS EC2 instance or any other VPS using Docker Compose.

1. **Clone the repository** on your server.
2. **Set up `.env` files**: Ensure your root `.env` is configured properly for production.
3. **Start the services**:
   ```bash
   docker-compose -f docker-compose.yml up -d --build
   ```
   *Note: This will spin up the database, redis, backend, frontend, and evolution-api.*

#### Background Tasks & Cron Job
We use FastAPI's native `BackgroundTasks` instead of Celery to conserve memory and resources. To trigger periodic follow-ups and scheduled campaigns, set up an OS-level cron job:

1. SSH into your AWS instance and edit your crontab:
   ```bash
   crontab -e
   ```
2. Add a cron expression to hit the trigger endpoint every 5 minutes:
   ```cron
   */5 * * * * curl -X POST http://localhost:8000/api/v1/campaigns/trigger-follow-ups -H "x-cron-secret: your_cron_secret" -H "Content-Length: 0" >/dev/null 2>&1
   ```
   *Make sure to replace `your_cron_secret` with the value of `CRON_SECRET` from your `.env` file.*

---

Built with ❤️ for Aurvyz.
