import logging
import re
from typing import Dict, Iterable, List

from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


class EventLogParser:
    """Парсинг HTML системного eventlog.ivp."""

    def __init__(self, patterns: Iterable[str]):
        self.patterns = [re.compile(p, re.IGNORECASE) for p in patterns]

    @staticmethod
    def _extract_text(html_content: str) -> List[str]:
        soup = BeautifulSoup(html_content, "html.parser")
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text("\n")
        lines = [line.strip() for line in text.split("\n")]
        return [line for line in lines if line]

    def parse_entry(self, html_content: str, event_id: int) -> List[Dict]:
        lines = self._extract_text(html_content)
        if not self.patterns:
            return [self._build_entry(event_id, line) for line in lines]

        filtered = [line for line in lines if any(p.search(line) for p in self.patterns)]
        logger.info("Event %s: найдено %s строк по шаблонам", event_id, len(filtered))
        return [self._build_entry(event_id, line) for line in filtered]

    @staticmethod
    def _build_entry(event_id: int, text: str) -> Dict:
        return {"event_id": event_id, "text": text}
