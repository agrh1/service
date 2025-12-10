from __future__ import annotations

from typing import Optional

import requests


class SeafileAPI:
    """Simple Seafile API wrapper working with pre-issued API tokens."""

    def __init__(self, base_url: str, token: str, verify_ssl: bool = True):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Token {token}"})
        self.verify_ssl = verify_ssl

    def ensure_folder(self, repo_id: str, folder_path: str) -> None:
        normalized_path = folder_path if folder_path.startswith("/") else f"/{folder_path}"
        self.session.post(
            f"{self.base_url}/api2/repos/{repo_id}/dir/",
            params={"p": "/", "reloaddir": "true"},
            data={"operation": "mkdir", "dir_name": normalized_path.strip("/")},
            verify=self.verify_ssl,
            timeout=10,
        )

    def get_upload_link(self, repo_id: str, folder_path: str, ttl_seconds: int) -> Optional[str]:
        normalized_path = folder_path if folder_path.startswith("/") else f"/{folder_path}"
        response = self.session.get(
            f"{self.base_url}/api2/repos/{repo_id}/upload-link/",
            params={"p": normalized_path, "expire": ttl_seconds},
            verify=self.verify_ssl,
            timeout=10,
        )
        if response.status_code != 200:
            return None
        return response.text.strip('"')

    def get_download_link(self, repo_id: str, file_path: str, password: str, ttl_seconds: int) -> Optional[str]:
        normalized_path = file_path if file_path.startswith("/") else f"/{file_path}"
        payload = {"p": normalized_path, "share_type": "download", "passwd": password, "expire": ttl_seconds}
        response = self.session.put(
            f"{self.base_url}/api2/repos/{repo_id}/file/shared-link/",
            json=payload,
            verify=self.verify_ssl,
            timeout=10,
        )
        if response.status_code not in (200, 201):
            return None
        return response.text.strip('"')
