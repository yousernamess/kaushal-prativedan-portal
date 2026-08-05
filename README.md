Kaushal Prativedan Portal

Stack
- React + TypeScript
- FastAPI
- PostgreSQL
- Railway
- SQLAlchemy
- Alembic
- OpenCV

Development

Backend
cd backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head
uvicorn app.main:app --reload

Frontend
cd frontend
npm install
npm run dev