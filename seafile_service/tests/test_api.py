import importlib
import json
import sys
from pathlib import Path

import pytest
import responses
from cryptography.fernet import Fernet

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


def build_test_app(tmp_path: Path):
    key = Fernet.generate_key().decode()
    instance_conf = [
        {
            "name": "main",
            "base_url": "http://seafile.local",
            "api_tokens": ["enc:" + Fernet(key.encode()).encrypt(b"apitoken").decode()],
            "verify_ssl": False,
        }
    ]
    repo_conf = [
        {
            "name": "default",
            "repo_id": "repo1",
            "instance": "main",
            "categories": ["general"],
            "upload_ttl_seconds": 3600,
            "download_ttl_seconds": 604800,
        }
    ]

    import os

    os.environ["ENCRYPTION_KEY"] = key
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path/'test.db'}"
    os.environ["SEAFILE_INSTANCES"] = json.dumps(instance_conf)
    os.environ["SEAFILE_REPOSITORIES"] = json.dumps(repo_conf)
    os.environ["ENABLE_SCHEDULER"] = "False"

    import config

    importlib.reload(config)
    import models

    importlib.reload(models)
    import api

    importlib.reload(api)
    return api.app


@pytest.fixture()
def client(tmp_path):
    app = build_test_app(tmp_path)
    with app.test_client() as client:
        yield client


@responses.activate
def test_create_upload_and_status(client):
    responses.add(
        responses.POST,
        "http://seafile.local/api2/repos/repo1/dir/",
        status=201,
    )
    responses.add(
        responses.GET,
        "http://seafile.local/api2/repos/repo1/upload-link/",
        status=200,
        body='"http://seafile.local/upload"',
    )

    response = client.post(
        "/api/create-upload",
        json={"ticket_id": "123", "category": "general"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["upload_link"] == "http://seafile.local/upload"
    assert "X-Correlation-Id" in response.headers

    status_response = client.post("/api/status", json={"ticket_id": "123"})
    assert status_response.status_code == 200
    status_data = status_response.get_json()
    assert len(status_data["links"]) == 1
    assert status_data["links"][0]["type"] == "upload"


@responses.activate
def test_create_download_default_ttl_and_password(client):
    responses.add(
        responses.PUT,
        "http://seafile.local/api2/repos/repo1/file/shared-link/",
        status=200,
        body='"http://seafile.local/download"',
    )

    response = client.post(
        "/api/create-download",
        json={"ticket_id": "124", "category": "general", "file_path": "/ticket_124/report.pdf"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["download_link"] == "http://seafile.local/download"
    assert data["password"]

    request_body = json.loads(responses.calls[0].request.body)
    assert request_body["expire"] == 604800
    assert request_body["passwd"] == data["password"]
