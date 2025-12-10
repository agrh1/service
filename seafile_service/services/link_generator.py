from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional

from config import encrypt_secret, settings, decrypt_secret
from models import CategoryMapping, Link, Repository, SeafileInstance, SessionLocal
from services.seafile_api import SeafileAPI

logger = logging.getLogger(__name__)


class LinkGenerator:
    def __init__(self):
        self.settings = settings

    def _resolve_repository(
        self,
        session: SessionLocal,
        *,
        category: Optional[str] = None,
        repository_name: Optional[str] = None,
        instance_name: Optional[str] = None,
    ) -> Optional[Repository]:
        query = session.query(Repository).join(SeafileInstance)
        if repository_name and instance_name:
            return (
                query.filter(Repository.name == repository_name, SeafileInstance.name == instance_name)
                .first()
            )
        if category:
            mapping = session.query(CategoryMapping).filter(CategoryMapping.category == category).first()
            if mapping:
                return mapping.repository
        return None

    def _get_api_client(self, repository: Repository) -> SeafileAPI:
        instance = repository.instance
        tokens = []
        for token in instance.api_tokens or []:
            decrypted = decrypt_secret(token)
            if decrypted:
                tokens.append(decrypted)
        if not tokens:
            raise RuntimeError(f"No API tokens configured for instance {instance.name}")
        return SeafileAPI(instance.base_url, tokens[0], verify_ssl=instance.verify_ssl)

    def _save_link(
        self,
        session: SessionLocal,
        *,
        ticket_id: str,
        category: str,
        repository: Repository,
        link_type: str,
        url: str,
        password: Optional[str],
        ttl_seconds: Optional[int],
    ) -> Link:
        expires_at = None
        if ttl_seconds:
            expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        link = (
            session.query(Link)
            .filter_by(ticket_id=ticket_id, link_type=link_type, repository_id=repository.id, category=category)
            .first()
        )
        if not link:
            link = Link(
                ticket_id=ticket_id,
                category=category,
                repository_id=repository.id,
                link_type=link_type,
                status="active",
            )
            session.add(link)
        link.url = url
        link.password = encrypt_secret(password) if password else None
        link.expires_at = expires_at
        link.status = "active"
        session.commit()
        session.refresh(link)
        return link

    def generate_upload_link(
        self,
        *,
        ticket_id: str,
        category: str,
        folder_path: Optional[str] = None,
        ttl_seconds: Optional[int] = None,
        repository_name: Optional[str] = None,
        instance_name: Optional[str] = None,
    ) -> Dict:
        with SessionLocal() as session:
            repository = self._resolve_repository(
                session, category=category, repository_name=repository_name, instance_name=instance_name
            )
            if not repository:
                raise ValueError(f"Repository not found for category {category}")

            api_client = self._get_api_client(repository)
            folder = folder_path or f"/ticket_{ticket_id}"
            api_client.ensure_folder(repository.repo_id, folder)
            ttl = ttl_seconds or repository.upload_ttl_seconds or self.settings.DEFAULT_UPLOAD_TTL_SECONDS
            upload_link = api_client.get_upload_link(repository.repo_id, folder, ttl)
            if not upload_link:
                raise RuntimeError("Failed to create upload link")
            link = self._save_link(
                session,
                ticket_id=ticket_id,
                category=category,
                repository=repository,
                link_type="upload",
                url=upload_link,
                password=None,
                ttl_seconds=ttl,
            )
            return {
                "status": "ok",
                "ticket_id": ticket_id,
                "category": category,
                "upload_link": link.url,
                "expires_at": link.expires_at.isoformat() if link.expires_at else None,
            }

    def generate_download_link(
        self,
        *,
        ticket_id: str,
        category: str,
        file_path: str,
        ttl_seconds: Optional[int] = None,
        repository_name: Optional[str] = None,
        instance_name: Optional[str] = None,
    ) -> Dict:
        with SessionLocal() as session:
            repository = self._resolve_repository(
                session, category=category, repository_name=repository_name, instance_name=instance_name
            )
            if not repository:
                raise ValueError(f"Repository not found for category {category}")

            api_client = self._get_api_client(repository)
            ttl = ttl_seconds or repository.download_ttl_seconds or self.settings.DEFAULT_DOWNLOAD_TTL_SECONDS
            password = secrets.token_urlsafe(12)
            download_link = api_client.get_download_link(repository.repo_id, file_path, password, ttl)
            if not download_link:
                raise RuntimeError("Failed to create download link")

            link = self._save_link(
                session,
                ticket_id=ticket_id,
                category=category,
                repository=repository,
                link_type="download",
                url=download_link,
                password=password,
                ttl_seconds=ttl,
            )
            return {
                "status": "ok",
                "ticket_id": ticket_id,
                "category": category,
                "download_link": link.url,
                "password": password,
                "expires_at": link.expires_at.isoformat() if link.expires_at else None,
            }

    def get_status(self, *, ticket_id: str, category: Optional[str] = None) -> Dict:
        with SessionLocal() as session:
            query = session.query(Link).filter(Link.ticket_id == ticket_id)
            if category:
                query = query.filter(Link.category == category)
            links = query.all()
            return {
                "ticket_id": ticket_id,
                "links": [
                    {
                        "type": link.link_type,
                        "url": link.url,
                        "status": link.status,
                        "category": link.category,
                        "expires_at": link.expires_at.isoformat() if link.expires_at else None,
                        "password_protected": bool(link.password),
                    }
                    for link in links
                ],
            }

    def close_ticket(self, *, ticket_id: str) -> None:
        with SessionLocal() as session:
            links = session.query(Link).filter(Link.ticket_id == ticket_id).all()
            for link in links:
                link.status = "closed"
            session.commit()
