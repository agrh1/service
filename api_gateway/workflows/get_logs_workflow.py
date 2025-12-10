import asyncio
from typing import Dict, Optional, List
from dataclasses import dataclass
import logging
import aiohttp

logger = logging.getLogger(__name__)

@dataclass
class GetLogsWorkflowRequest:
    ticket_id: int
    link_types: str = 'both'

@dataclass
class GetLogsWorkflowResponse:
    status: str
    ticket_id: int
    logs: Optional[Dict] = None
    links: Optional[Dict] = None
    errors: List[str] = None

class GetLogsWorkflow:
    """Полный workflow"""
    
    def __init__(self, intraservice_url: str, seafile_service_url: str):
        self.intraservice_url = intraservice_url
        self.seafile_service_url = seafile_service_url
        self.max_retries = 3
        self.retry_delay = 2
    
    async def execute(self, request: GetLogsWorkflowRequest) -> GetLogsWorkflowResponse:
        """Выполнить workflow"""
        
        logger.info(f'Начало workflow для заявки {request.ticket_id}')
        
        errors = []
        
        try:
            # Шаг 1: Получить логи
            logs = await self._get_logs_from_intraservice(request.ticket_id)
            if not logs:
                errors.append('Failed to get logs')
            
            # Шаг 2: Генерировать ссылки
            links = await self._generate_links_in_seafile(
                request.ticket_id,
                request.link_types
            )
            if not links:
                errors.append('Failed to generate links')

            status = 'ok' if not errors else 'partial'

            return GetLogsWorkflowResponse(
                status=status,
                ticket_id=request.ticket_id,
                logs=logs,
                links=links,
                errors=errors if errors else None
            )
        
        except Exception as e:
            logger.error(f'Ошибка: {str(e)}')
            return GetLogsWorkflowResponse(
                status='error',
                ticket_id=request.ticket_id,
                errors=[str(e)]
            )
    
    async def _get_logs_from_intraservice(self, ticket_id: int, retry_count: int = 0) -> Optional[Dict]:
        """Получить логи с retry"""
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f'{self.intraservice_url}/api/task/{ticket_id}/logs'
                
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        logger.info(f'Логи получены для {ticket_id}')
                        return {'data': await response.text()}
                    else:
                        raise Exception(f'HTTP {response.status}')
        
        except Exception as e:
            logger.error(f'Попытка {retry_count + 1}: {str(e)}')
            
            if retry_count < self.max_retries:
                await asyncio.sleep(self.retry_delay)
                return await self._get_logs_from_intraservice(ticket_id, retry_count + 1)
            else:
                logger.error(f'Не удалось получить логи после {self.max_retries} попыток')
                return None
    
    async def _generate_links_in_seafile(
        self,
        ticket_id: int,
        link_types: str = 'both',
        retry_count: int = 0
    ) -> Optional[Dict]:
        """Генерировать ссылки с retry"""
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f'{self.seafile_service_url}/api/generate-links'
                
                async with session.post(
                    url,
                    json={'ticket_id': ticket_id, 'link_types': link_types},
                    timeout=10
                ) as response:
                    if response.status in [200, 201]:
                        data = await response.json()
                        logger.info(f'Ссылки сгенерированы для {ticket_id}')
                        return data
                    else:
                        raise Exception(f'HTTP {response.status}')
        
        except Exception as e:
            logger.error(f'Попытка {retry_count + 1}: {str(e)}')
            
            if retry_count < self.max_retries:
                await asyncio.sleep(self.retry_delay)
                return await self._generate_links_in_seafile(
                    ticket_id,
                    link_types,
                    retry_count + 1
                )
            else:
                return None
 
