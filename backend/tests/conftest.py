import os

os.environ["DATABASE_URL"] = "sqlite:///./test_espacos.db"

import pytest

from app.database import SessionLocal, reset_db
from app.seed import seed as seed_data


@pytest.fixture()
def db_session():
    """Banco de dados limpo e semeado com o cenário sintético padrão para cada teste."""
    reset_db()
    session = SessionLocal()
    seed_data(session)
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def empty_db_session():
    """Banco de dados limpo, sem seed — para testes que montam seu próprio cenário."""
    reset_db()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
