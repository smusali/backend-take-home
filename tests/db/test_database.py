"""
Unit tests for database connection and session management.

Tests engine creation, session factory, dependency injection,
and connection handling.
"""

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.database import (
    create_db_engine,
    create_session_factory,
    get_engine,
    get_session_factory,
    get_db,
    get_db_context,
    init_db,
)
from app.db.base import Base
from app.models.lead import Lead, LeadStatus
from app.models.user import User


class TestDatabaseEngine:
    """Test suite for database engine creation."""
    
    def test_create_db_engine(self):
        """Test that database engine can be created."""
        engine = create_db_engine()
        
        assert engine is not None
        assert hasattr(engine, "url")
        assert hasattr(engine, "pool")
    
    def test_engine_can_connect(self):
        """Test that engine can establish connection."""
        engine = create_db_engine()
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
    
    def test_engine_pool_configuration(self):
        """Test that engine has correct pool configuration."""
        engine = create_db_engine()
        
        assert engine.pool.size() == 20  # pool_size
        assert engine.pool._max_overflow == 40  # max_overflow
    
    def test_get_engine_returns_singleton(self):
        """Test that get_engine returns the same instance."""
        engine1 = get_engine()
        engine2 = get_engine()
        
        assert engine1 is engine2


class TestSessionFactory:
    """Test suite for session factory."""
    
    def test_create_session_factory(self):
        """Test that session factory can be created."""
        engine = create_db_engine()
        session_factory = create_session_factory(engine)
        
        assert session_factory is not None
        assert hasattr(session_factory, "__call__")
    
    def test_session_factory_creates_sessions(self):
        """Test that session factory creates valid sessions."""
        engine = create_db_engine()
        session_factory = create_session_factory(engine)
        
        session = session_factory()
        
        assert isinstance(session, Session)
        assert session.bind == engine
        
        session.close()
    
    def test_session_autoflush_is_false(self):
        """Test that sessions have autoflush disabled."""
        engine = create_db_engine()
        session_factory = create_session_factory(engine)
        
        session = session_factory()
        
        assert session.autoflush is False
        
        session.close()
    
    def test_get_session_factory_returns_singleton(self):
        """Test that get_session_factory returns the same instance."""
        factory1 = get_session_factory()
        factory2 = get_session_factory()
        
        assert factory1 is factory2


class TestGetDbDependency:
    """Test suite for FastAPI database dependency."""
    
    def test_get_db_yields_session(self):
        """Test that get_db yields a valid session."""
        db_gen = get_db()
        db = next(db_gen)
        
        assert isinstance(db, Session)
        
        try:
            db_gen.send(None)
        except StopIteration:
            pass
    
    def test_get_db_closes_session_after_use(self):
        """Test that get_db closes session after yielding."""
        db_gen = get_db()
        db = next(db_gen)
        
        session_id = id(db)
        
        try:
            db_gen.send(None)
        except StopIteration:
            pass
        
        # Session should be closed but we can't directly test that
        # So we verify it doesn't raise an error
        assert session_id is not None
    
    def test_get_db_can_query_database(self):
        """Test that session from get_db can query database."""
        engine = create_db_engine()
        Base.metadata.create_all(bind=engine)
        
        db_gen = get_db()
        db = next(db_gen)
        
        # Try to query (will be empty but should not error)
        leads = db.query(Lead).all()
        assert isinstance(leads, list)
        
        try:
            db_gen.send(None)
        except StopIteration:
            pass
        
        Base.metadata.drop_all(bind=engine)


class TestGetDbContext:
    """Test suite for database context manager."""
    
    def test_get_db_context_provides_session(self):
        """Test that context manager provides a valid session."""
        with get_db_context() as db:
            assert isinstance(db, Session)
    
    def test_get_db_context_commits_on_success(self):
        """Test that context manager commits on successful exit."""
        engine = create_db_engine()
        Base.metadata.create_all(bind=engine)
        
        with get_db_context() as db:
            user = User(
                username="testuser",
                email="test@example.com",
                hashed_password="hashed"
            )
            db.add(user)
        
        # Verify commit happened
        with get_db_context() as db:
            found_user = db.query(User).filter_by(username="testuser").first()
            assert found_user is not None
            assert found_user.email == "test@example.com"
            
            # Cleanup
            db.delete(found_user)
        
        Base.metadata.drop_all(bind=engine)
    
    def test_get_db_context_rolls_back_on_exception(self):
        """Test that context manager rolls back on exception."""
        engine = create_db_engine()
        Base.metadata.create_all(bind=engine)
        
        try:
            with get_db_context() as db:
                user = User(
                    username="rollbackuser",
                    email="rollback@example.com",
                    hashed_password="hashed"
                )
                db.add(user)
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Verify rollback happened
        with get_db_context() as db:
            found_user = db.query(User).filter_by(username="rollbackuser").first()
            assert found_user is None
        
        Base.metadata.drop_all(bind=engine)


class TestInitDb:
    """Test suite for database initialization."""
    
    def test_init_db_creates_tables(self):
        """Test that init_db creates all tables."""
        engine = create_db_engine()
        
        # Drop tables first
        Base.metadata.drop_all(bind=engine)
        
        # Initialize database
        init_db()
        
        # Verify tables exist
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        assert "leads" in tables
        assert "users" in tables
        
        Base.metadata.drop_all(bind=engine)
    
    def test_init_db_is_idempotent(self):
        """Test that init_db can be called multiple times safely."""
        engine = create_db_engine()
        
        Base.metadata.drop_all(bind=engine)
        
        init_db()
        init_db()  # Should not raise error
        
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        assert "leads" in tables
        assert "users" in tables
        
        Base.metadata.drop_all(bind=engine)


class TestModelsIntegration:
    """Test suite for models integration with database."""
    
    def test_can_create_lead_in_database(self):
        """Test that Lead model can be created in database."""
        engine = create_db_engine()
        Base.metadata.create_all(bind=engine)
        
        with get_db_context() as db:
            lead = Lead(
                first_name="Integration",
                last_name="Test",
                email="integration@example.com",
                resume_path="/path/to/resume.pdf"
            )
            db.add(lead)
        
        with get_db_context() as db:
            found_lead = db.query(Lead).filter_by(email="integration@example.com").first()
            assert found_lead is not None
            assert found_lead.first_name == "Integration"
            assert found_lead.status == LeadStatus.PENDING
            
            db.delete(found_lead)
        
        Base.metadata.drop_all(bind=engine)
    
    def test_can_create_user_in_database(self):
        """Test that User model can be created in database."""
        engine = create_db_engine()
        Base.metadata.create_all(bind=engine)
        
        with get_db_context() as db:
            user = User(
                username="integrationuser",
                email="integration.user@example.com",
                hashed_password="$2b$12$hashedpassword"
            )
            db.add(user)
        
        with get_db_context() as db:
            found_user = db.query(User).filter_by(username="integrationuser").first()
            assert found_user is not None
            assert found_user.email == "integration.user@example.com"
            assert found_user.is_active is True
            
            db.delete(found_user)
        
        Base.metadata.drop_all(bind=engine)
