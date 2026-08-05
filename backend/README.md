# Kaushal Prativedan Portal API

## Local development

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# Set DATABASE_URL in .env to your Railway PostgreSQL connection string.
alembic upgrade head
python -m uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`; interactive documentation is at `/docs`.

PostgreSQL is required in every environment. Set `DATABASE_URL` to the Railway PostgreSQL connection string locally and in Railway; the application normalizes Railway's `postgres://` URL for SQLAlchemy's psycopg 3 driver.
