"""
  This is the db connection module for the application.
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from core.config import settings

# Create the engine
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Reflects all existing tables from Supabase into metadata
metadata = MetaData()
metadata.reflect(bind=engine)

def get_db():
  """Return a database session."""
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()