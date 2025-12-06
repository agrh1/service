import requests
from typing import Dict, Optional
from config import settings
import logging

logger = logging.getLogger(__name__)

class SeafileAPI:
    """Работа с Seafile REST API"""
    
    def __init__(self):
        self.base_url = settings.SEAFILE_URL
        self.username = settings.SEAFILE_USERNAME
        self.password = settings.SEAFILE_PASSWORD
        self.library_id = settings.SEAFILE_LIBRARY_ID
        
        self.session = requests.Session()
        self.token = None
        self.authenticated = False
    
    def login(self) -> bool:
        """Логинимся в Seafile"""
        try:
            response = self.session.post(
                f'{self.base_url}/api2/auth-token/',
                data={
                    'username': self.username,
                    'password': self.password
                },
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f'Ошибка при логине: {response.status_code}')
                return False
            
            data = response.json()
            self.token = data.get('token')
            
            if not self.token:
                logger.error('Токен не получен')
                return False
            
            self.session.headers.update({
                'Authorization': f'Token {self.token}',
                'Content-Type': 'application/json'
            })
            
            self.authenticated = True
            logger.info('Успешно аутентифицированы в Seafile')
            return True
        
        except requests.RequestException as e:
            logger.error(f'Ошибка при логине: {str(e)}')
            return False
    
    def create_folder(self, folder_name: str, parent_path: str = '/') -> Optional[Dict]:
        """Создать папку"""
        try:
            if not self.authenticated:
                if not self.login():
                    return None
            
            response = self.session.post(
                f'{self.base_url}/api2/repos/{self.library_id}/dir/',
                params={'p': parent_path, 'reloaddir': 'true'},
                data={'operation': 'mkdir', 'dir_name': folder_name},
                timeout=10
            )
            
            if response.status_code != 201:
                logger.error(f'Ошибка при создании папки: {response.status_code}')
                return None
            
            logger.info(f'Папка {folder_name} создана')
            return {'status': 'ok', 'folder_name': folder_name}
        
        except requests.RequestException as e:
            logger.error(f'Ошибка при создании папки: {str(e)}')
            return None
    
    def get_upload_link(self, folder_path: str) -> Optional[str]:
        """Получить upload ссылку"""
        try:
            if not self.authenticated:
                if not self.login():
                    return None
            
            response = self.session.get(
                f'{self.base_url}/api2/repos/{self.library_id}/upload-link/',
                params={'p': folder_path},
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f'Ошибка: {response.status_code}')
                return None
            
            upload_link = response.text.strip('"')
            logger.info(f'Upload ссылка получена для {folder_path}')
            return upload_link
        
        except requests.RequestException as e:
            logger.error(f'Ошибка: {str(e)}')
            return None
    
    def get_download_link(self, file_path: str, password: Optional[str] = None) -> Optional[str]:
        """Получить download ссылку"""
        try:
            if not self.authenticated:
                if not self.login():
                    return None
            
            data = {
               'p': file_path,
                'share_type': 'download'
            }
            
            if password:
                data['passwd'] = password
            
            response = self.session.put(
                f'{self.base_url}/api2/repos/{self.library_id}/file/shared-link/',
                json=data,
                timeout=10
            )
            
            if response.status_code not in [200, 201]:
                logger.error(f'Ошибка: {response.status_code}')
                return None
            
            share_link = response.text.strip('"')
            logger.info(f'Download ссылка получена для {file_path}')
            return share_link
        
        except requests.RequestException as e:
            logger.error(f'Ошибка: {str(e)}')
            return None
    
    def check_folder_exists(self, folder_path: str) -> bool:
        """Проверить существует ли папка"""
        try:
            if not self.authenticated:
                if not self.login():
                    return False
            
            response = self.session.get(
                f'{self.base_url}/api2/repos/{self.library_id}/dir/',
                params={'p': folder_path},
                timeout=10
            )
            
            return response.status_code == 200
        
        except requests.RequestException:
            return False
 
