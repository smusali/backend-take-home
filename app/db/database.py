"""
Database connection and session management.

Provides database engine, session factory, and FastAPI dependency
for database session injection.
"""

from typing import Generator
from contextlib import contextmanager
import time

from sqlalchemy import create_engine, event, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError, DisconnectionError

from app.core.config import get_settings


def create_db_engine() -> Engine:
    """
    Create and configure SQLAlchemy engine.
    
    Returns:
        Configured SQLAlchemy engine with connection pooling
    """
    settings = get_settings()
    
    connect_args = {}
    
    # SQLite specific configuration
    if settings.DATABASE_URL.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args=connect_args,
        pool_pre_ping=True,  # Verify connections before using
        pool_size=20,  # Maximum number of connections to keep open
        max_overflow=40,  # Maximum overflow connections
        pool_recycle=3600,  # Recycle connections after 1 hour
        echo=settings.DEBUG,  # Log SQL queries in debug mode
    )
    
    # Add connection retry logic
    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        """Handle new database connections."""
        connection_record.info["pid"] = id(dbapi_conn)
    
    @event.listens_for(engine, "checkout")
    def receive_checkout(dbapi_conn, connection_record, connection_proxy):
        """Verify connection is alive on checkout."""
        pid = connection_record.info.get("pid")
        if pid is not None and pid != id(dbapi_conn):
            connection_record.dbapi_connection = None
            raise DisconnectionError(
                "Connection record belongs to pid %s, "
                "attempting to check out in pid %s" % (pid, id(dbapi_conn))
            )
    
    return engine


def create_session_factory(engine: Engine) -> sessionmaker:
    """
    Create session factory bound to engine.
    
    Args:
        engine: SQLAlchemy engine
        
    Returns:
        Session factory
    """
    return sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )


# Lazy initialization of engine and session factory
_engine: Engine | None = None
_session_factory: sessionmaker | None = None


def get_engine() -> Engine:
    """
    Get or create the global database engine.
    
    Returns:
        SQLAlchemy engine instance
    """
    global _engine
    if _engine is None:
        _engine = create_db_engine()
    return _engine


def get_session_factory() -> sessionmaker:
    """
    Get or create the global session factory.
    
    Returns:
        Session factory
    """
    global _session_factory
    if _session_factory is None:
        _session_factory = create_session_factory(get_engine())
    return _session_factory


# Backward compatibility - use functions instead of direct access
engine = property(lambda self: get_engine())
SessionLocal = property(lambda self: get_session_factory())


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database session injection.
    
    Yields:
        Database session
        
    Example:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    session_factory = get_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database session.
    
    Useful for non-FastAPI contexts (scripts, background tasks).
    
    Yields:
        Database session
        
    Example:
        with get_db_context() as db:
            items = db.query(Item).all()
    """
    session_factory = get_session_factory()
    db = session_factory()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db(retries: int = 5, delay: int = 2) -> None:
    """
    Initialize database with retry logic.
    
    Creates all tables defined in models. Useful for development
    and testing. In production, use Alembic migrations instead.
    
    Args:
        retries: Number of connection attempts
        delay: Delay between retries in seconds
        
    Raises:
        OperationalError: If database connection fails after all retries
    """
    from app.db.base import Base
    
    engine = get_engine()
    for attempt in range(retries):
        try:
            Base.metadata.create_all(bind=engine)
            return
        except OperationalError as e:
            if attempt < retries - 1:
                time.sleep(delay)
                continue
            raise e


def close_db() -> None:
    """
    Close database connections and dispose of engine.
    
    Should be called during application shutdown.
    """
    global _engine
    if _engine is not None:
        _engine.dispose()
        _engine = None
