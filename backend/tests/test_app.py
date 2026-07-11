import os
import io
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.services.audio_validator import AudioValidator, AudioValidationError
from app.services.scoring import ScoringEngine

# 1. Database Setup for Testing (SQLite in-memory)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_temp.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module", autouse=True)
def mock_redis():
    with patch("app.api.monitoring.Redis") as mock:
        mock_instance = MagicMock()
        mock_instance.ping.return_value = True
        mock.from_url.return_value = mock_instance
        yield mock


@pytest.fixture(scope="module", autouse=True)
def init_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("./test_temp.db"):
        try:
            os.remove("./test_temp.db")
        except Exception:
            pass


@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# 2. Test Audio Validator
def test_audio_validator_size_limit(tmp_path):
    large_file = tmp_path / "large.wav"
    # Write 11MB file
    with open(large_file, "wb") as f:
        f.seek(11 * 1024 * 1024 - 1)
        f.write(b"\0")
        
    with pytest.raises(AudioValidationError) as excinfo:
        AudioValidator.validate_file_size(str(large_file))
    assert "exceeds 10MB" in str(excinfo.value)


def test_audio_validator_invalid_signature(tmp_path):
    dummy_file = tmp_path / "dummy.txt"
    with open(dummy_file, "wb") as f:
        f.write(b"NOT_A_VALID_HEADER_DATA_STREAM")
        
    with pytest.raises(AudioValidationError) as excinfo:
        AudioValidator.validate_file_signature(str(dummy_file), "audio/wav")
    assert "Unsupported or corrupted" in str(excinfo.value)


# 3. Test Scoring Engine
def test_scoring_engine_calculations():
    # Simulate a 35s recording of 10 words
    mock_words = [
        {"word": "Hello", "start": 1.0, "end": 1.5, "probability": 0.98},
        {"word": "world", "start": 1.6, "end": 2.2, "probability": 0.95},
        {"word": "this", "start": 3.0, "end": 3.4, "probability": 0.45},  # Low confidence/mispronounced
        {"word": "is", "start": 3.5, "end": 3.7, "probability": 0.92},
        {"word": "a", "start": 3.8, "end": 3.9, "probability": 0.99},
        {"word": "production", "start": 4.0, "end": 4.8, "probability": 0.96},
        {"word": "ready", "start": 4.9, "end": 5.4, "probability": 0.88},
        {"word": "AI", "start": 6.5, "end": 7.0, "probability": 0.72},     # Unclear
        {"word": "assessment", "start": 7.1, "end": 7.9, "probability": 0.97},
        {"word": "app", "start": 8.0, "end": 8.5, "probability": 0.99},
    ]
    
    scores, enriched = ScoringEngine.calculate_scores(
        words_data=mock_words,
        audio_duration=35.0,
        reference_text="Hello world this is a production ready AI assessment app"
    )
    
    # Assert correctness
    assert scores["overall_score"] > 0
    assert scores["accuracy_score"] > 0
    assert scores["fluency_score"] > 0
    assert scores["completeness_score"] == 100.0  # All 10 words matched
    
    # Verify word classifications
    assert enriched[2]["is_mispronounced"] is True  # 45 < 65
    assert enriched[7]["is_unclear"] is True        # 60 is between 65 and 80


# 4. Test API Router Endpoints
def test_api_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["services"]["api"] == "online"


def test_api_metrics(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "api_requests_total" in response.text


def test_api_auth_register_and_login(client):
    # Register
    reg_response = client.post(
        "/api/v1/auth/register",
        json={"email": "test@aurapronounce.in", "password": "securepassword123"}
    )
    assert reg_response.status_code == 201
    reg_data = reg_response.json()
    assert "access_token" in reg_data
    assert reg_data["email"] == "test@aurapronounce.in"

    # Login JSON
    login_response = client.post(
        "/api/v1/auth/login-json",
        json={"email": "test@aurapronounce.in", "password": "securepassword123"}
    )
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()


def test_upload_missing_consent(client):
    # Triggering upload without consent checkbox should reject HTTP 400
    response = client.post(
        "/upload",
        data={
            "consent": "false",
            "session_id": "test_session_id",
            "purpose": "pronunciation_assessment"
        },
        files={"file": ("test.wav", io.BytesIO(b"DUMMY_BINARY_DATA"), "audio/wav")}
    )
    assert response.status_code == 400
    assert "DPDP consent" in response.json()["detail"]
