# EventAI - AI-Powered Event Management Platform

EventAI is an end-to-end SaaS platform that utilizes Google's Gemini AI to autonomously plan, budget, and market events. It transforms a few basic inputs into a comprehensive, dynamic event workspace.

## 🌟 Core Features

- **AI Event Analysis:** Generates risk assessments and staffing estimations based on crowd size and type.
- **Dynamic Module Generation:** Zero-hardcoding architecture that dynamically creates forms and data ledgers tailored to the event.
- **Chronological Timeline Engine:** Automatically builds and schedules a prioritized roadmap of tasks.
- **Financial Planning Engine:** Estimates granular resource costs, tracks remaining budgets, and visualizes allocation with Chart.js.
- **Marketing Assistant:** Auto-generates Instagram posts, Facebook content, WhatsApp invites, and Press Releases with 1-click clipboard integration.
- **SaaS Foundation:** Fully secure multi-tenant architecture with Event Ownership, Authentication, and Role-Based Access Control (RBAC) foundation.

## 🏗️ Architecture

EventAI is built with **Django 6.0**, **Bootstrap 5**, and the **Google Generative AI SDK**.

- **Frontend:** HTML5, Bootstrap 5, Vanilla JavaScript, Chart.js.
- **Backend:** Python 3.13, Django 6.0.
- **Database:** SQLite (Dev) / PostgreSQL (Prod ready).
- **AI Integration:** Google Gemini 1.5 Flash via `ai_engine.gemini_service`.
- **Deployment Ready:** Configured with Gunicorn, Whitenoise, and dotenv.

## 🚀 Installation & Setup

1. **Clone & Environment**
   ```bash
   git clone <repo-url>
   cd EventAI
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Variables**
   Create a `.env` file in the root directory:
   ```env
   SECRET_KEY=your-django-secret
   DEBUG=True
   GEMINI_API_KEY=your-google-gemini-key
   ```

4. **Migrate & Run**
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

## 🔒 Security & Roles
- Every event is strictly scoped to `created_by`.
- Custom `check_event_access` decorators prevent IDOR attacks.
- Robust Audit Logging tracks all system modifications.

## ☁️ Deployment (Render)
1. Set the Build Command: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
2. Set the Start Command: `gunicorn config.wsgi`
3. Configure Environment Variables in the Render dashboard.
