from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import allocation, audit, constraints, metrics, rooms, sectors, teams


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    from app.database import SessionLocal
    from app.models import Sector

    db = SessionLocal()
    try:
        if db.query(Sector).count() == 0:
            from app.seed import seed

            seed(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Sistema Inteligente de Gestão e Otimização de Espaços Corporativos",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rooms.router)
app.include_router(sectors.router)
app.include_router(teams.router)
app.include_router(constraints.router)
app.include_router(allocation.router)
app.include_router(metrics.router)
app.include_router(audit.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "espacos-corporativos-api"}


@app.get("/health")
def health():
    return {"status": "healthy"}
