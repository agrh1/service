from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint, create_engine, func
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from config import encrypt_secret, settings

Base = declarative_base()
engine = create_engine(settings.DATABASE_URL, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


class SeafileInstance(Base):
    __tablename__ = "seafile_instances"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    base_url = Column(String, nullable=False)
    api_tokens = Column(JSON, default=list)
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)
    verify_ssl = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    repositories: List["Repository"] = relationship("Repository", back_populates="instance", cascade="all, delete-orphan")

    def set_tokens(self, tokens: List[str]):
        self.api_tokens = [encrypt_secret(token) or token for token in tokens]


class Repository(Base):
    __tablename__ = "seafile_repositories"
    __table_args__ = (UniqueConstraint("name", "instance_id", name="uq_repo_instance"),)
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    repo_id = Column(String, nullable=False)
    instance_id = Column(Integer, ForeignKey("seafile_instances.id"), nullable=False)
    upload_ttl_seconds = Column(Integer, default=3600)
    download_ttl_seconds = Column(Integer, default=7 * 24 * 3600)

    instance: SeafileInstance = relationship("SeafileInstance", back_populates="repositories")
    categories: List["CategoryMapping"] = relationship("CategoryMapping", back_populates="repository", cascade="all, delete-orphan")
    links: List["Link"] = relationship("Link", back_populates="repository")


class CategoryMapping(Base):
    __tablename__ = "category_mappings"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True)
    category = Column(String, unique=True, nullable=False)
    repository_id = Column(Integer, ForeignKey("seafile_repositories.id"), nullable=False)

    repository: Repository = relationship("Repository", back_populates="categories")


class Link(Base):
    __tablename__ = "links"
    __table_args__ = (UniqueConstraint("ticket_id", "link_type", "repository_id", "category", name="uq_ticket_link"),)
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(String, nullable=False)
    category = Column(String, nullable=False)
    repository_id = Column(Integer, ForeignKey("seafile_repositories.id"), nullable=False)
    url = Column(String, nullable=False)
    password = Column(String, nullable=True)
    link_type = Column(String, nullable=False)  # upload | download
    status = Column(String, default="active")
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    repository: Repository = relationship("Repository", back_populates="links")


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def seed_from_settings() -> None:
    from config import decrypt_secret

    with SessionLocal() as session:
        for inst_config in settings.SEAFILE_INSTANCES:
            instance = session.query(SeafileInstance).filter_by(name=inst_config.name).first()
            if not instance:
                instance = SeafileInstance(
                    name=inst_config.name,
                    base_url=str(inst_config.base_url),
                    verify_ssl=inst_config.verify_ssl,
                    username=inst_config.username,
                    password=encrypt_secret(inst_config.decrypted_password()),
                )
                session.add(instance)
            instance.base_url = str(inst_config.base_url)
            instance.verify_ssl = inst_config.verify_ssl
            instance.username = inst_config.username
            instance.password = encrypt_secret(inst_config.decrypted_password())
            instance.set_tokens(inst_config.decrypted_tokens())

        session.flush()

        repo_cache = {}
        for repo_config in settings.SEAFILE_REPOSITORIES:
            instance = session.query(SeafileInstance).filter_by(name=repo_config.instance).first()
            if not instance:
                continue
            repo = (
                session.query(Repository)
                .filter_by(name=repo_config.name, instance_id=instance.id)
                .first()
            )
            if not repo:
                repo = Repository(
                    name=repo_config.name,
                    repo_id=repo_config.repo_id,
                    instance_id=instance.id,
                    upload_ttl_seconds=repo_config.upload_ttl_seconds,
                    download_ttl_seconds=repo_config.download_ttl_seconds,
                )
                session.add(repo)
            else:
                repo.repo_id = repo_config.repo_id
                repo.upload_ttl_seconds = repo_config.upload_ttl_seconds
                repo.download_ttl_seconds = repo_config.download_ttl_seconds
            repo_cache[(repo_config.instance, repo_config.name)] = repo
            session.flush()

            for category in repo_config.categories:
                mapping = session.query(CategoryMapping).filter_by(category=category).first()
                if not mapping:
                    mapping = CategoryMapping(category=category, repository_id=repo.id)
                    session.add(mapping)
                else:
                    mapping.repository_id = repo.id

        session.commit()
