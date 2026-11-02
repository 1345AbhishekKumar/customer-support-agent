# 🤖 AI Customer Support Agent & Dashboard

An intelligent, autonomous customer support agent pipeline and management dashboard. It monitors an incoming Gmail support inbox, parses and classifies customer inquiries using Google Gemini with Pydantic AI, matches questions against a curated knowledge base, records events and tickets in Supabase (PostgreSQL), drafts or sends automated replies, and provides a real-time web dashboard.

---

## 📑 Table of Contents
- [Architecture & Workflow](#-architecture--workflow)
- [Account & Login Guide](#-account--login-guide)
- [Environment Configuration](#-environment-configuration)
- [How to Run](#-how-to-run)
  - [Option 1: Development Mode (Recommended)](#option-1-development-mode-recommended)
  - [Option 2: Unified Production Mode](#option-2-unified-production-mode)
  - [Background Email Poller](#background-email-poller)
- [Database Setup & Seeding](#-database-setup--seeding)
- [Helper Scripts](#-helper-scripts)
- [API Reference](#-api-reference)

---

## 🏗 Architecture & Workflow

```text
Incoming Customer Email
        │
        ▼
   [Gmail Inbox] ──(Poller / API /poll)──► [FastAPI Backend]
                                                │
                                                ├─► Classify & Guardrail Check (Gemini)
                                                ├─► Consult Knowledge Base (Supabase DB)
                                                ├─► Generate Response / Escalate (Pydantic AI)
                                                ├─► Send Reply via Gmail API
                                                ▼
                                         [Supabase Database]
                                      (tickets, messages, events)
                                                ▲
                                                │ (HTTP Basic Auth)
                                      [React + Vite Dashboard]
```

* **Backend (`app/`):** FastAPI application managing tickets, audit events, knowledge base entries, background polling, and AI response generation.
* **Frontend (`dashboard/`):** React 19 + TypeScript + Vite + Tailwind CSS v4 + shadcn/ui dashboard to inspect tickets, view raw event logs, and manage the knowledge base.
* **Database (`supabase/`):** PostgreSQL database storing `events`, `tickets`, `messages`, and `knowledge_base`.

---

## 🔐 Account & Login Guide

### 1. Dashboard Web UI Login
The web dashboard **does not use an email or Google/Supabase OAuth**. It is protected with HTTP Basic Authentication configured in your `.env` file:

* **Username:** Set by `DASHBOARD_USERNAME` (defaults to `admin`)
* **Password:** Set by `DASHBOARD_PASSWORD` in your `.env`

---

### 2. Gmail Automation vs. Testing Email Addresses

* **Support Bot Account (Automation):**
  * The Gmail account whose credentials (`GOOGLE_REFRESH_TOKEN`) are configured in `.env`.
  * This is the official support inbox that the bot monitors and replies from.
* **Testing Inquiries (Customer):**
  * **Use a different / personal email address** to send test support emails to your bot's Gmail address.
  * *Important:* Avoid sending emails from the bot's own Gmail address to itself, as Gmail's thread and inbox filters may prevent the message from appearing as a new incoming thread.

---

### 3. Supabase Account
* Supabase acts purely as your remote PostgreSQL database.
* Connects via the `DATABASE_URL` connection pooler string. It is not used for dashboard user sessions.

---

## ⚙️ Environment Configuration

Create or update your `.env` file in the root directory:

```env
# Google OAuth for Gmail API
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REFRESH_TOKEN=your-google-refresh-token

# Supabase / PostgreSQL Connection
DATABASE_URL=postgresql://postgres.your-project-id:your-db-password@aws-0-region.pooler.supabase.com:6543/postgres

# Google Gemini API
GEMINI_API_KEY=AIzaSy...
# (Optional) Model overrides:
CLASSIFIER_MODEL=google:gemini-3.5-flash-lite
AGENT_MODEL=google:gemini-3.5-flash-lite

# Email Polling Interval (in seconds)
POLL_INTERVAL_SECONDS=60

# Dashboard HTTP Basic Authentication
DASHBOARD_USERNAME=admin
DASHBOARD_PASSWORD=your_secure_password_here

# Pydantic AI
PYDANTIC_AI_NO_BANNER=true
```

---

## 🚀 How to Run

### Option 1: Development Mode (Recommended)

Run the backend and frontend in separate terminals with hot-reloading:

#### 1. Backend (FastAPI)
From the root directory:
```powershell
uv run uvicorn app.main:app --reload --port 8000
```
* **API Server:** `http://127.0.0.1:8000`
* **Swagger Docs:** `http://127.0.0.1:8000/docs`

#### 2. Frontend (Vite + React)
From the `dashboard` directory:
```powershell
cd dashboard
bun dev
```
*(Or use `npm run dev`)*
* **Frontend UI:** `http://localhost:5173`
* *(Vite proxies all `/api/*` requests directly to `http://127.0.0.1:8000`)*

---

### Option 2: Unified Production Mode

The FastAPI server in `app/main.py` automatically serves the compiled frontend static files from `dashboard/dist` if present:

1. **Build the dashboard:**
   ```powershell
   cd dashboard
   bun run build
   cd ..
   ```
2. **Launch the unified server:**
   ```powershell
   uv run uvicorn app.main:app --port 8000
   ```
3. Visit `http://127.0.0.1:8000` to access both the dashboard and API from a single port.

---

### Background Email Poller

To continuously listen for incoming Gmail messages automatically every `POLL_INTERVAL_SECONDS`:

```powershell
uv run python -m app.poller
```

> **Tip:** You can also trigger a manual check at any time without the poller by sending a POST request to `http://127.0.0.1:8000/api/poll`.

---

## 🗄️ Database Setup & Seeding

1. **Run Database Migrations:**
   Apply the SQL schema in `supabase/migrations/20261031160959_create_tables.sql` in your Supabase SQL Editor.
2. **Seed Knowledge Base:**
   Populate the database with knowledge base markdown files located in `knowledge_base/`:
   ```powershell
   uv run python scripts/seed_knowledge_base.py
   ```

---

## 🧰 Helper Scripts

* **`scripts/get_refresh_token.py`**:
  Obtain a Gmail OAuth refresh token using your `credentials.json`.
  ```powershell
  uv run python scripts/get_refresh_token.py
  ```
* **`scripts/gmail_check.py`**:
  Verify your Gmail API connection and inspect the most recent email.
  ```powershell
  uv run python scripts/gmail_check.py
  ```
* **`scripts/seed_knowledge_base.py`**:
  Parses markdown files in `knowledge_base/*.md` and inserts/updates them in the database.

---

## 📡 API Reference

All `/api/*` endpoints require HTTP Basic Authentication (`DASHBOARD_USERNAME` & `DASHBOARD_PASSWORD`):

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Public healthcheck endpoint |
| `GET` | `/api/login` | Verify basic auth credentials |
| `GET` | `/api/events` | List all message processing audit events |
| `GET` | `/api/tickets` | List all customer support tickets |
| `GET` | `/api/tickets/{id}/messages` | List full conversation thread for a ticket |
| `GET` | `/api/knowledge-base` | Retrieve all knowledge base articles |
| `PUT` | `/api/knowledge-base/{id}` | Update title or content of an article |
| `POST`| `/api/poll` | Trigger an on-demand poll of the Gmail inbox |
# customer-support-agent
