from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.auth import hash_password
from app.models import User, UserRole
from app.routers import academic_years, analytics, assessments, auth, processing, schools, sections, students, users

settings = get_settings()
app = FastAPI(title="Kaushal Prativedan Portal API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(schools.router)
app.include_router(academic_years.router)
app.include_router(sections.router)
app.include_router(students.router)
app.include_router(assessments.router)
app.include_router(processing.router)
app.include_router(analytics.router)


@app.on_event("startup")
def seed_first_admin():
    """Create the initial admin account if no users exist."""
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            admin = User(
                email=settings.admin_email,
                hashed_password=hash_password(settings.admin_password),
                full_name=settings.admin_name,
                role=UserRole.ADMIN,
                is_active=True,
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()


@app.get("/health", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
