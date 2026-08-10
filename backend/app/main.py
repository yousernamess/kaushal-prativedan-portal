from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import academic_years, analytics, assessments, processing, schools, sections, students

settings = get_settings()
app = FastAPI(title="Kaushal Prativedan Portal API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(schools.router)
app.include_router(academic_years.router)
app.include_router(sections.router)
app.include_router(students.router)
app.include_router(assessments.router)
app.include_router(processing.router)
app.include_router(analytics.router)

@app.get("/health", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
