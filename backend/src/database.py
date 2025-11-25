

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

Base = declarative_base()

engine = create_engine("sqlite:///news_database.db", echo=True)
Base.metadata.create_all(engine)

SessionLocal = sessionmaker(bind=engine)

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()