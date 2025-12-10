import requests
from typing import Dict, Optional, List
from requests.auth import HTTPBasicAuth
from config import settings
import logging

logger = logging.getLogger(__name__)

class IntraServiceAPI:
    """Работа с IntraService REST API"""
    
    def __init__(self):
        self.base_url = settings.INTRASERVICE_URL
        self.username = settings.INTRASERVICE_USERNAME
        self.password = settings.INTRASERVICE_PASSWORD
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(self.username, self.password)
        self.authenticated = False
    
    def login(self) -> bool:
        """Логинимся в IntraService"""
        try:
            response = self.session.get(
                f'{self.base_url}/api/',
                timeout=10
            )
            
            if response.status_code == 200:
                self.authenticated = True
                logger.info('Успешно аутентифицированы в IntraService')
                return True
            else:
                logger.error(f'Ошибка при логине: {response.status_code}')
                return False
        
        except requests.RequestException as e:
            logger.error(f'Ошибка при логине: {str(e)}')
            self.authenticated = False
            return False
    
    def get_tickets(self, limit: int = 50) -> List[Dict]:
        """Получить список заявок"""
        try:
            if not self.authenticated and not self.login():
                logger.error('Аутентификация не выполнена, пропускаем получение заявок')
                return []
            
            response = self.session.get(
                f'{self.base_url}/api/task',
                params={'limit': limit},
                timeout=10
            )
            response.raise_for_status()
            
            logger.info(f'Получено заявок: {len(response.json())}')
            return response.json() if response.text else []
        
        except requests.RequestException as e:
            logger.error(f'Ошибка при получении заявок: {str(e)}')
            return []
    
    def get_ticket_logs(self, ticket_id: int) -> str:
        """Получить логи заявки"""
        try:
            if not self.authenticated and not self.login():
                logger.error('Аутентификация не выполнена, пропускаем получение логов')
                return ''
            
            response = self.session.get(
                f'{self.base_url}/api/task/{ticket_id}/logs',
                timeout=10
            )
            response.raise_for_status()
            
            logger.info(f'Получены логи для заявки {ticket_id}')
            return response.text
        
        except requests.RequestException as e:
            logger.error(f'Ошибка при получении логов {ticket_id}: {str(e)}')
            return ''
