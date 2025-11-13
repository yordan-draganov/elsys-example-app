import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import shutil
from main import app, STORAGE_DIR
from io import BytesIO

client = TestClient(app)

TEST_STORAGE_DIR = Path("test_storage")


@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Setup and teardown for each test - create and clean test storage."""
    TEST_STORAGE_DIR.mkdir(exist_ok=True)
    
    import main
    original_storage = main.STORAGE_DIR
    main.STORAGE_DIR = TEST_STORAGE_DIR
    
    yield
    
    if TEST_STORAGE_DIR.exists():
        shutil.rmtree(TEST_STORAGE_DIR)
    
    main.STORAGE_DIR = original_storage


def test_root_endpoint():
    """Test 1: Root endpoint returns correct information."""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert data["message"] == "File Storage API"
    assert "endpoints" in data
    assert isinstance(data["endpoints"], list)
    assert len(data["endpoints"]) >= 5


def test_health_check():
    """Test 2: Health check endpoint returns healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["service"] == "File Storage API"


def test_store_and_retrieve_file():
    """Test 3: Store a file and retrieve it successfully."""
    test_filename = "test_file.txt"
    test_content = b"Hello, this is a test file!"
    
    files = {"file": (test_filename, BytesIO(test_content), "text/plain")}
    response = client.post("/files", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "File stored successfully"
    assert data["filename"] == test_filename
    assert data["size"] == len(test_content)
    
    response = client.get(f"/files/{test_filename}")
    assert response.status_code == 200
    assert response.content == test_content


def test_list_files():
    """Test 4: List files endpoint returns correct file list."""
    response = client.get("/files")
    assert response.status_code == 200
    initial_data = response.json()
    initial_count = initial_data["count"]
    
    test_filename = "list_test.txt"
    test_content = b"Test content for listing"
    files = {"file": (test_filename, BytesIO(test_content), "text/plain")}
    client.post("/files", files=files)
    
    response = client.get("/files")
    assert response.status_code == 200
    data = response.json()
    
    assert data["count"] == initial_count + 1
    assert test_filename in data["files"]


def test_file_not_found():
    """Test 5: Retrieving non-existent file returns 404."""
    response = client.get("/files/nonexistent_file.txt")
    assert response.status_code == 404
    
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_metrics_endpoint():
    """Test 6: Metrics endpoint returns correct statistics."""
    test_filename = "metrics_test.txt"
    test_content = b"Test content for metrics" * 100
    files = {"file": (test_filename, BytesIO(test_content), "text/plain")}
    client.post("/files", files=files)
    
    response = client.get("/metrics")
    assert response.status_code == 200
    
    data = response.json()
    assert "files_stored_total" in data
    assert "files_current" in data
    assert "total_storage_bytes" in data
    assert "total_storage_mb" in data
    assert "timestamp" in data
    
    assert data["total_storage_bytes"] > 0


def test_duplicate_file_upload():
    """Test 8: Uploading the same file twice overwrites it."""
    test_filename = "duplicate_test.txt"
    test_content_1 = b"First version"
    test_content_2 = b"Second version - updated"
    
    files = {"file": (test_filename, BytesIO(test_content_1), "text/plain")}
    response = client.post("/files", files=files)
    assert response.status_code == 200
    
    files = {"file": (test_filename, BytesIO(test_content_2), "text/plain")}
    response = client.post("/files", files=files)
    assert response.status_code == 200
    
    response = client.get(f"/files/{test_filename}")
    assert response.status_code == 200
    assert response.content == test_content_2


def test_empty_file_upload():
    """Test 9: Empty file can be uploaded."""
    test_filename = "empty_file.txt"
    test_content = b""
    
    files = {"file": (test_filename, BytesIO(test_content), "text/plain")}
    response = client.post("/files", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert data["size"] == 0
    assert data["filename"] == test_filename