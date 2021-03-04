from http import HTTPStatus
from pathlib import Path

from faker import Faker
from flask import Response
from flask.testing import FlaskClient

from overhave import OverhaveAppType


class TestApp:
    """ Integration tests for OverhaveApp. """

    def test_app_root_get(self, test_client: FlaskClient):
        response: Response = test_client.get("/")
        assert response.status_code == HTTPStatus.FOUND

    def test_app_get_favicon(self, test_app: OverhaveAppType, test_client: FlaskClient):
        response: Response = test_client.get("/favicon.ico")
        assert response.status_code == HTTPStatus.OK
        assert response.mimetype == "image/vnd.microsoft.icon"
        assert response.data == (Path(test_app.config["FILES_DIR"]) / "favicon.ico").read_bytes()

    def test_app_create_pr_without_publisher(
        self, test_app: OverhaveAppType, test_client: FlaskClient, test_pullrequest_id: int
    ):
        response: Response = test_client.get(f"/pull_request/{test_pullrequest_id}")
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    def test_app_create_pr_incorrect_data(
        self,
        test_app: OverhaveAppType,
        test_client: FlaskClient,
        test_pullrequest_id: int,
        test_pullrequest_published_by: str,
    ):
        response: Response = test_client.get(
            f"/pull_request/{test_pullrequest_id}?published_by={test_pullrequest_published_by}"
        )
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    def test_app_get_report_notexists(self, test_client: FlaskClient, faker: Faker):
        response: Response = test_client.get(f"/reports/{faker.word()}/index.html")
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_app_get_report_noindex(self, test_client: FlaskClient, test_report_without_index: Path):
        response: Response = test_client.get(f"/reports/{test_report_without_index.name}/index.html")
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_app_get_report(self, test_client: FlaskClient, test_report_with_index: Path):
        response: Response = test_client.get(f"/reports/{test_report_with_index.name}/index.html")
        assert response.status_code == HTTPStatus.OK
        assert response.data == (test_report_with_index / "index.html").read_bytes()
