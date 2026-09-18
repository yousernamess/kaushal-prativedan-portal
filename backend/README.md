# Kaushal Prativedan Portal API

## Local development

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# Set DATABASE_URL in .env to your local PostgreSQL connection string.
alembic upgrade head
python -m uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`; interactive documentation is at `/docs`.

PostgreSQL is required in every environment. Set `DATABASE_URL` to your local PostgreSQL connection string (Windows host on port 5432; if running from WSL, use the Windows host IP from `ip route show default` instead of `localhost` — see README). The application normalizes `postgres://` URLs for SQLAlchemy's psycopg 3 driver.
