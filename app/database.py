"""
Configuration SQLAlchemy pour SQLite.

Le fichier .db vit dans /app/data, qui est monté en volume Docker
(voir docker-compose.yml) donc les données survivent aux redémarrages
du container.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "insta_tracker.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# check_same_thread=False : nécessaire car FastAPI peut utiliser plusieurs
# threads, alors que SQLite est par défaut mono-thread.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency FastAPI : fournit une session DB et la ferme proprement après usage."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
