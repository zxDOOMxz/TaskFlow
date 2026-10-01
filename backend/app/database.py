from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

from app.config import get_settings

settings = get_settings()

# Supabase Connection Pooler has quirks with SQLAlchemy's connection pooling
# and introspection. When using the pooler, disable SQLAlchemy's internal pool
# (NullPool) and driver-specific features such as prepared statements.
_connect_args = {}
_pool_class = None
if "pooler.supabase.com" in settings.database_url:
    _pool_class = NullPool
    # psycopg (v3) supports prepare_threshold; psycopg2 does not.
    if settings.database_url.startswith("postgresql+psycopg://"):
        _connect_args["prepare_threshold"] = 0

engine = create_engine(
    settings.database_url,
    future=True,
    connect_args=_connect_args,
    poolclass=_pool_class,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
