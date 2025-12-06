from bs4 import BeautifulSoup
from typing import List, Dict
import re
import logging

logger = logging.getLogger(__name__)

class HTMLParser:
    """Парсинг HTML логов из IntraService"""
    
    @staticmethod
    def parse_logs(html_content: str) -> List[str]:
        """Парсит HTML логи"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            for script in soup(['script', 'style']):
                script.decompose()
            
            text = soup.get_text()
            lines = [line.strip() for line in text.split('\n')]
            lines = [line for line in lines if line]
            
            logger.info(f'Спарсено {len(lines)} строк')
            return lines
        
        except Exception as e:
            logger.error(f'Ошибка при парсинге: {str(e)}')
            return []
    
    @staticmethod
    def extract_errors(lines: List[str]) -> List[Dict]:
        """Извлекает ошибки из логов"""
        errors = []
        error_pattern = re.compile(r'(error|exception|failed)', re.IGNORECASE)
        
        for i, line in enumerate(lines):
            if error_pattern.search(line):
                errors.append({
                    'line_number': i,
                    'text': line,
                    'type': 'ERROR'
                })
        
        logger.info(f'Найдено ошибок: {len(errors)}')
        return errors

