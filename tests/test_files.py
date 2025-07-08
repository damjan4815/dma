import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def make_upload(name="report.txt", content=b"ABC"):
    return SimpleUploadedFile(name, content, content_type="text/plain")


class TestFileDownloadVariants:
    file_upload_url = reverse("api:fileversion-list")  # POST

    def _by_id(self, pk: int) -> str:
        return reverse("api:files-detail", args=[pk])

    def _by_url(self, path: str, file_name: str, revision: int | None = None) -> str:
        return (
            f"/api/files/{path}/{file_name}/"
            if not revision
            else f"/api/files/{path}/{file_name}/?revision={revision}"
        )

    def _by_hash(self, hash: str) -> str:
        return f"/api/files/cas/{hash}/"

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.client = APIClient()

    def _upload(self, user, path="docs", content=b"ABC"):
        self.client.force_authenticate(user)
        r = self.client.post(
            self.file_upload_url,
            {"upload": make_upload(content=content), "path": path},
            format="multipart",
        )
        self.client.logout()
        return r.data

    def test_download_by_id_returns_correct_content(self, user):
        data = self._upload(user, content=b"ABC")
        file_id = data["id"]

        self.client.force_authenticate(user)
        response = self.client.get(self._by_id(file_id))
        self.client.logout()

        assert response.status_code == status.HTTP_200_OK
        assert b"".join(response.streaming_content) == b"ABC"

    def test_download_by_path_and_name_returns_latest(self, user):
        _ = self._upload(user, content=b"v1")
        data2 = self._upload(user, content=b"v2")

        self.client.force_authenticate(user)
        response = self.client.get(self._by_url(data2["path"], data2["file_name"]))
        self.client.logout()

        assert response.status_code == status.HTTP_200_OK
        assert b"".join(response.streaming_content) == b"v2"

    def test_download_by_path_and_revision(self, user):
        self._upload(user, content=b"v1")
        self._upload(user, content=b"v2")

        self.client.force_authenticate(user)
        response = self.client.get(self._by_url("docs", "report.txt", revision=1))
        self.client.logout()

        assert response.status_code == status.HTTP_200_OK
        assert b"".join(response.streaming_content) == b"v1"

    def test_download_by_hash_returns_correct_content(self, user):
        data = self._upload(user, content=b"hashcontent")
        self.client.force_authenticate(user)
        response = self.client.get(self._by_hash(data["content_hash"]))
        self.client.logout()

        assert response.status_code == status.HTTP_200_OK
        assert b"".join(response.streaming_content) == b"hashcontent"

    def test_other_user_cannot_access_file(self, user, django_user_model):
        data = self._upload(user)
        file_id = data["id"]
        file_hash = data["content_hash"]
        fname = data["file_name"]
        path = data["path"]

        eve = django_user_model.objects.create_user(
            email="eve@example.com", name="Eve", password="HackMe!"
        )

        self.client.force_authenticate(eve)
        assert self.client.get(self._by_id(file_id)).status_code == 404
        assert self.client.get(self._by_url(path, fname)).status_code == 404
        assert self.client.get(self._by_hash(file_hash)).status_code == 404

    def test_download_by_id_by_url_by_hash_and_permissions(
        self, user, django_user_model
    ):
        data = self._upload(user)
        file_id = data["id"]
        file_hash = data["content_hash"]
        fname = data["file_name"]
        path = "docs"

        self.client.force_authenticate(user)
        print("url ", self._by_id(file_id))
        r_id = self.client.get(self._by_id(file_id))
        assert r_id.status_code == status.HTTP_200_OK
        self.client.logout()

        self.client.force_authenticate(user)
        print("url ", self._by_url(path, fname))
        r_path = self.client.get(self._by_url(path, fname))
        assert r_path.status_code == status.HTTP_200_OK
        self.client.logout()

        self.client.force_authenticate(user)
        r_hash = self.client.get(self._by_hash(file_hash))
        assert r_hash.status_code == status.HTTP_200_OK
        self.client.logout()

        eve = django_user_model.objects.create_user(
            email="eve@example.com", name="Eve", password="HackMe!"
        )
        self.client.force_authenticate(eve)
        assert (
            self.client.get(self._by_id(file_id)).status_code
            == status.HTTP_404_NOT_FOUND
        )
        assert (
            self.client.get(self._by_url(path, fname)).status_code
            == status.HTTP_404_NOT_FOUND
        )
        assert (
            self.client.get(self._by_hash(file_hash)).status_code
            == status.HTTP_404_NOT_FOUND
        )
