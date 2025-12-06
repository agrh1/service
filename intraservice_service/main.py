from tasks import app, poll_intraservice_api
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info('Запуск IntraService сервиса')
    app.start()

