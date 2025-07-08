import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from propylon_document_manager.file_versions.models import FileVersion

pytestmark = pytest.mark.django_db


def make_upload(name="file.txt", content=b"data"):
    return SimpleUploadedFile(name, content, content_type="text/plain")


class TestFileVersionEndpoints:
    list_url = reverse("api:fileversion-list")

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.client = APIClient()

    def _upload(self, user, path="docs", content=b"data"):
        self.client.force_authenticate(user)
        resp = self.client.post(
            self.list_url,
            {"upload": make_upload(content=content), "path": path},
            format="multipart",
        )
        self.client.logout()
        return resp

    def test_authenticated_user_can_upload_file(self, user):
        response = self._upload(user)
        assert response.status_code == status.HTTP_201_CREATED
        assert FileVersion.objects.filter(created_by=user).exists()

    def test_uploaded_file_appears_in_list_for_owner(self, user):
        upload_resp = self._upload(user)
        file_id = upload_resp.data["id"]

        self.client.force_authenticate(user)
        list_resp = self.client.get(self.list_url)
        self.client.logout()

        assert list_resp.status_code == status.HTTP_200_OK
        returned_ids = {item["id"] for item in list_resp.data["results"]}
        assert returned_ids == {file_id}

    def test_file_owner_can_delete_file(self, user):
        upload_resp = self._upload(user)
        file_id = upload_resp.data["id"]

        self.client.force_authenticate(user)
        detail_url = reverse("api:fileversion-detail", args=[file_id])
        delete_resp = self.client.delete(detail_url)
        self.client.logout()

        assert delete_resp.status_code == status.HTTP_204_NO_CONTENT
        assert not FileVersion.objects.filter(pk=file_id).exists()

    def test_other_user_cannot_list_files(self, user, django_user_model):
        self._upload(user)
        other_user = django_user_model.objects.create_user(
            email="eve@example.com", name="Eve", password="HackMe123!"
        )

        self.client.force_authenticate(other_user)
        list_resp = self.client.get(self.list_url)
        self.client.logout()

        assert list_resp.status_code == status.HTTP_200_OK
        assert list_resp.data["results"] == []

    def test_other_user_cannot_retrieve_file(self, user, django_user_model):
        upload_resp = self._upload(user)
        file_id = upload_resp.data["id"]
        detail_url = reverse("api:fileversion-detail", args=[file_id])

        other_user = django_user_model.objects.create_user(
            email="eve@example.com", name="Eve", password="HackMe123!"
        )

        self.client.force_authenticate(other_user)
        retrieve_resp = self.client.get(detail_url)
        self.client.logout()

        assert retrieve_resp.status_code == status.HTTP_404_NOT_FOUND

    def test_other_user_cannot_delete_file(self, user, django_user_model):
        upload_resp = self._upload(user)
        file_id = upload_resp.data["id"]
        detail_url = reverse("api:fileversion-detail", args=[file_id])

        other_user = django_user_model.objects.create_user(
            email="eve@example.com", name="Eve", password="HackMe123!"
        )

        self.client.force_authenticate(other_user)
        delete_resp = self.client.delete(detail_url)
        self.client.logout()

        assert delete_resp.status_code == status.HTTP_404_NOT_FOUND

    def test_upload_and_list_visibility(self, user):
        self.client.force_authenticate(user)

        resp = self.client.post(
            self.list_url,
            {"upload": make_upload(), "path": "docs"},
            format="multipart",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        fid = resp.data["id"]

        r2 = self.client.get(self.list_url)
        assert r2.status_code == status.HTTP_200_OK
        print("r2 data", r2.data)
        assert {i["id"] for i in r2.data["results"]} == {fid}

    def test_other_user_cannot_see_or_delete(self, user, django_user_model):
        self.client.force_authenticate(user)
        upload_resp = self.client.post(
            self.list_url,
            {"upload": make_upload(), "path": "docs"},
            format="multipart",
        )
        file_id = upload_resp.data["id"]
        self.client.logout()

        other = django_user_model.objects.create_user(
            email="eve@example.com", name="Eve", password="HackMe123!"
        )
        self.client.force_authenticate(other)

        assert self.client.get(self.list_url).data["results"] == []

        detail_url = reverse("api:fileversion-detail", args=[file_id])
        assert self.client.get(detail_url).status_code == status.HTTP_404_NOT_FOUND

        assert self.client.delete(detail_url).status_code == status.HTTP_404_NOT_FOUND

    def test_owner_can_delete(self, user):
        self.client.force_authenticate(user)
        resp = self.client.post(
            self.list_url,
            {"upload": make_upload(), "path": "docs"},
            format="multipart",
        )
        file_id = resp.data["id"]
        detail_url = reverse("api:fileversion-detail", args=[file_id])
        assert self.client.delete(detail_url).status_code == status.HTTP_204_NO_CONTENT
        assert not FileVersion.objects.filter(pk=file_id).exists()
