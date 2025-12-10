import requests
import requests_mock

from config import settings
from services.intraservice_api import IntraServiceAPI


def test_get_open_tickets_filters_status_and_logs_in(capsys):
    session = requests.Session()
    api = IntraServiceAPI(session=session)
    base = settings.INTRASERVICE_URL.rstrip('/')

    with requests_mock.Mocker() as mocker:
        mocker.get(f"{base}/api/", text="ok", status_code=200)
        mocker.get(
            f"{base}/api/task",
            json=[{"id": 1, "name": "Task"}],
            status_code=200,
        )

        tickets = api.get_open_tickets(status_ids=[1], limit=10)

    assert tickets == [{"id": 1, "name": "Task"}]

    # after login cookie should be present
    assert api.session.cookies.get("seaf_user") == settings.INTRASERVICE_SEAF_USER


def test_comment_methods(requests_mock):
    session = requests.Session()
    api = IntraServiceAPI(session=session)
    base = settings.INTRASERVICE_URL.rstrip('/')

    requests_mock.get(f"{base}/api/", text="ok", status_code=200)
    requests_mock.get(
        f"{base}/api/task/7/comment",
        json=[{"id": 1, "text": "hi"}],
        status_code=200,
    )
    requests_mock.post(f"{base}/api/task/7/comment", status_code=200)

    comments = api.get_comments(7)
    assert comments[0]["text"] == "hi"

    assert api.add_comment(7, "new comment", is_internal=True) is True
