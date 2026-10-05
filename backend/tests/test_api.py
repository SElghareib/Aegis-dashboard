import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, get_db
from app.main import app
from fastapi.testclient import TestClient

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create test client with overridden database dependency"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data


def test_register_user(client):
    """Test user registration"""
    user_data = {
        "email": "test@example.com",
        "password": "securepassword123",
        "full_name": "Test User"
    }
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert "id" in data


def test_login_user(client, db_session):
    """Test user login"""
    # First register a user
    user_data = {
        "email": "login@example.com",
        "password": "securepassword123",
        "full_name": "Login User"
    }
    client.post("/api/v1/auth/register", json=user_data)
    
    # Then login
    login_data = {
        "email": "login@example.com",
        "password": "securepassword123"
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, db_session):
    """Test login with wrong password"""
    # First register a user
    user_data = {
        "email": "wrongpass@example.com",
        "password": "correctpassword",
        "full_name": "Test User"
    }
    client.post("/api/v1/auth/register", json=user_data)
    
    # Try login with wrong password
    login_data = {
        "email": "wrongpass@example.com",
        "password": "wrongpassword"
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 401


def test_create_workspace(client, db_session):
    """Test workspace creation"""
    # Register and login
    user_data = {
        "email": "workspace@example.com",
        "password": "password123",
        "full_name": "Workspace User"
    }
    client.post("/api/v1/auth/register", json=user_data)
    
    login_data = {
        "email": "workspace@example.com",
        "password": "password123"
    }
    login_response = client.post("/api/v1/auth/login", json=login_data)
    token = login_response.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create workspace
    workspace_data = {
        "name": "Test Workspace",
        "description": "A test workspace"
    }
    response = client.post("/api/v1/workspaces/", json=workspace_data, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == workspace_data["name"]


def test_list_workspaces(client, db_session):
    """Test listing workspaces"""
    # Register and login
    user_data = {
        "email": "list@example.com",
        "password": "password123",
        "full_name": "List User"
    }
    client.post("/api/v1/auth/register", json=user_data)
    
    login_data = {
        "email": "list@example.com",
        "password": "password123"
    }
    login_response = client.post("/api/v1/auth/login", json=login_data)
    token = login_response.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # List workspaces (should have personal workspace)
    response = client.get("/api/v1/workspaces/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1  # At least personal workspace
