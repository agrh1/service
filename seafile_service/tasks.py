from __future__ import annotations

import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from config import settings
from models import Link, SessionLocal

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone="UTC")


def cleanup_expired_links() -> None:
    with SessionLocal() as session:
        now = datetime.utcnow()
        expired = (
            session.query(Link)
            .filter(
                Link.link_type == "download",
                Link.status == "active",
                Link.expires_at.isnot(None),
                Link.expires_at < now,
            )
            .all()
        )
        for link in expired:
            logger.info("Marking expired link", extra={"link_id": link.id, "ticket_id": link.ticket_id})
            link.status = "expired"
        session.commit()


def purge_closed_tickets() -> None:
    with SessionLocal() as session:
        closed_links = session.query(Link).filter(Link.status == "closed").all()
        for link in closed_links:
            logger.info("Removing closed link", extra={"link_id": link.id, "ticket_id": link.ticket_id})
            session.delete(link)
        session.commit()


def start_scheduler() -> None:
    if not settings.ENABLE_SCHEDULER:
        logger.info("Scheduler disabled by configuration")
        return
    if scheduler.running:
        return
    scheduler.add_job(cleanup_expired_links, "interval", minutes=30, id="cleanup_expired_links", replace_existing=True)
    scheduler.add_job(purge_closed_tickets, "interval", minutes=60, id="purge_closed_tickets", replace_existing=True)
    scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown()
