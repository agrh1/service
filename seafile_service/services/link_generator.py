import os
from urllib.parse import urljoin

from dotenv import load_dotenv
from seafileapi import SeafileAPI

load_dotenv()


class LinkGenerator:
    """
    Генератор ссылок на файлы/папки в внешнем Seafile.
    Ожидает, что в .env заданы:
      SEAFILE_URL         – базовый URL сервера, например https://seafile.example.com/
      SEAFILE_USERNAME    – логин (email) пользователя
      SEAFILE_PASSWORD    – пароль пользователя
      SEAFILE_LIBRARY_ID  – ID библиотеки (repo_id), куда складываем файлы
    """

    def __init__(self) -> None:
        server_url = os.getenv("SEAFILE_URL")
        login_name = os.getenv("SEAFILE_USERNAME")
        password = os.getenv("SEAFILE_PASSWORD")
        library_id = os.getenv("SEAFILE_LIBRARY_ID")

        if not (server_url and login_name and password and library_id):
            raise RuntimeError(
                "Seafile config is incomplete. "
                "Check SEAFILE_URL, SEAFILE_USERNAME, SEAFILE_PASSWORD, SEAFILE_LIBRARY_ID in .env"
            )

        # SeafileAPI принимает позиционные аргументы: login_name, password, server_url
        self.api = SeafileAPI(login_name, password, server_url)
        # авторизация (получение токена)
        self.api.auth()

        self.server_url = server_url.rstrip("/") + "/"
        self.library_id = library_id

    def _get_repo(self):
        """Возвращает объект библиотеки (репозитория) по ID."""
        return self.api.repos.get_repo(self.library_id)

    def create_folder_if_not_exists(self, path: str) -> None:
        """
        Создаёт папку в библиотеке, если её ещё нет.
        path – путь внутри библиотеки, например '/tickets/1234'
        """
        repo = self._get_repo()
        if not path.startswith("/"):
            path = "/" + path
        try:
            repo.mkdir(path)
        except Exception:
            # Если папка уже есть или другая не критичная ошибка – просто игнорируем
            pass

    def generate_download_link(self, path: str, ttl: int = 3600) -> str:
        """
        Генерирует временную ссылку для скачивания файла/папки.
        path – путь внутри библиотеки, например '/tickets/1234/report.pdf'
        ttl  – время жизни ссылки в секундах.
        """
        repo = self._get_repo()
        if not path.startswith("/"):
            path = "/" + path

        share_link = repo.generate_share_link(path, expire=ttl)
        # share_link обычно уже полный URL, но на всякий случай соберём от базового
        return urljoin(self.server_url, share_link)

    def generate_upload_link(self, path: str, ttl: int = 3600) -> str:
        """
        Генерирует временную ссылку для загрузки файлов в указанную папку.
        path – путь папки внутри библиотеки, например '/tickets/1234'
        """
        repo = self._get_repo()
        if not path.startswith("/"):
            path = "/" + path

        upload_link = repo.generate_upload_link(path, expire=ttl)
        return urljoin(self.server_url, upload_link)

