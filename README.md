# Kaushal Prativedan Portal

Science Assessment Management System for NGOs/schools to automate OMR-based evaluation.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, TypeScript, Vite, TailwindCSS, shadcn/ui, React Router, TanStack Query, React Hook Form |
| Backend | FastAPI, SQLAlchemy 2.0, Alembic, Pydantic |
| Database | PostgreSQL (local install) |
| OMR | OpenCV (existing module, treated as black box) |

## Project Structure

```
kaushal-prativedan-portal/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── core/
│   │   │   ├── config.py        # Settings (env-driven)
│   │   │   └── database.py      # Engine, session, Base
│   │   └── routers/
│   │       ├── schools.py       # School CRUD + bulk delete
│   │       ├── academic_years.py # Academic Year CRUD
│   │       ├── sections.py      # Section CRUD + bulk create
│   │       ├── students.py      # Student CRUD + CSV import/export
│   │       └── assessments.py   # Assessment + Question CRUD
│   ├── alembic/                 # Migrations
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/router.tsx       # Routes
│   │   ├── components/
│   │   │   ├── common/          # CrudPage, FormDialog, DataTable, etc.
│   │   │   ├── layout/          # Sidebar, TopNav, AppLayout
│   │   │   └── ui/              # Button (shadcn-style)
│   │   ├── lib/
│   │   │   ├── api.ts           # Axios instance
│   │   │   ├── master-data.ts   # Types + API helpers
│   │   │   └── utils.ts         # cn() utility
│   │   ├── pages/
│   │   │   ├── master-data-page.tsx  # Tabbed Master Data
│   │   │   ├── schools-page.tsx
│   │   │   ├── academic-years-page.tsx
│   │   │   ├── sections-page.tsx
│   │   │   ├── students-page.tsx
│   │   │   ├── assessments-page.tsx  # Placeholder
│   │   │   ├── process-omr-page.tsx  # Placeholder
│   │   │   ├── reports-page.tsx      # Placeholder
│   │   │   └── dashboard-page.tsx    # Placeholder
│   │   └── styles/globals.css
│   └── package.json
├── omrExtractor/               # Git submodule (OMR engine)
├── templates/                  # OMR template files
├── output/                     # Reports, uploads
├── .env                        # Environment variables
├── TASKS.md                    # Milestone tracking
├── API.md                      # API documentation
├── DATABASE.md                 # Database schema
├── PROJECT_SPEC.md             # Project specification
├── AI_RULES.md                 # Development rules
└── README.md                   # This file
```

## Setup

### Quick Start (first time on a new machine)

```powershell
# 1. Clone the repo (includes the omrExtractor submodule)
git clone --recurse-submodules <repo-url>
cd kaushal-prativedan-portal

# 2. Run the setup script (Windows PowerShell)
.\setup.ps1
```

The script automatically:
- Initializes the `omrExtractor` git submodule
- Creates `.env` files from `.env.example` templates
- Sets up the Python virtual environment and installs backend + omrExtractor dependencies
- Runs database migrations (`alembic upgrade head`)
- Installs frontend packages (`npm install`)

> **After running the script**, open `backend/.env` and set `DATABASE_URL` to your PostgreSQL connection string (see below).

### Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL (local install; see the WSL note below)
- Git (with submodule support)

### Manual Setup (if you skip the script)

```powershell
# 1. Clone with submodules
git clone --recurse-submodules <repo-url>
cd kaushal-prativedan-portal

# 2. Backend
cd backend
copy .env.example .env        # then edit DATABASE_URL
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r ..\omrExtractor\requirements.txt   # pillow, matplotlib, etc.
alembic upgrade head
uvicorn app.main:app --reload

# 3. Frontend (separate terminal)
cd frontend
copy .env.example .env
npm install
npm run dev
```

> If you cloned **without** `--recurse-submodules`, run `git submodule update --init --recursive` to fetch the `omrExtractor` submodule. Without it, the backend will fail to start.

### Environment Variables

> **Important:** `.env` files are **not** committed to git (they contain secrets).
> After cloning/pulling, you **must** create them from the `.env.example` templates:
>
> ```bash
> cp backend/.env.example backend/.env   # then edit DATABASE_URL
> cp frontend/.env.example frontend/.env  # usually works as-is
> ```

**Backend** (`backend/.env`):
```
DATABASE_URL=postgresql+psycopg://postgres:password@host:port/dbname
CORS_ORIGINS=http://localhost:5173
```

> **WSL note:** the local PostgreSQL runs on the Windows host. If you run the
> backend from WSL, `localhost` will not work — use the Windows host IP shown
> by `ip route show default` (e.g. `172.26.224.1`). This IP can change after a
> Windows reboot, so re-check it if the backend suddenly cannot connect.

**Frontend** (`.env` in frontend/):
```
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Current Status

### Completed

- **Milestone 1** — Foundation (FastAPI, React, PostgreSQL, Alembic)
- **Milestone 2** — Master Data (Schools, Academic Years, Sections, Students)
  - Full CRUD with validation
  - CSV import/export with row-level errors
  - Bulk section creation
  - School delete with bulk student removal
  - UX overhaul (dropdowns, cascading selects, empty states, loading states)
- **Milestone 3** — Assessments (backend only)
  - Assessment CRUD with questions
  - Soft delete, duplicate, baseline/endline types

### In Progress

- Assessment frontend page (placeholder)

### Not Started

- Milestone 4: Process OMR
- Milestone 5: OMR Integration
- Milestone 6: Analytics
- Milestone 7: Reports
- Milestone 8: Dashboard
- Milestone 9: Deployment

## API

See [API.md](API.md) for full endpoint documentation.

## Database

See [DATABASE.md](DATABASE.md) for schema details.

## Development Rules

See [AI_RULES.md](AI_RULES.md) for coding guidelines.

## Git

- Branch: `v1` (active development)
- Branch: `master` (initial commit)
- Commit after every completed feature
- Never leave the project in a broken state