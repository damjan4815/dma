import hashlib

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from propylon_document_manager.file_versions.models import FileVersion, User


@pytest.mark.django_db
class TestUserModelCRUD:
    def test_user_can_be_created(self):
        user = User.objects.create_user(
            email="alice@example.com", name="Alice", password="StrongPassw0rd!"
        )
        assert user.pk is not None
        assert User.objects.count() == 1

    def test_user_can_be_read(self):
        User.objects.create_user(
            email="alice@example.com", name="Alice", password="StrongPassw0rd!"
        )
        user = User.objects.get(email="alice@example.com")
        assert user.name == "Alice"

    def test_user_can_be_updated(self):
        user = User.objects.create_user(
            email="alice@example.com", name="Alice", password="StrongPassw0rd!"
        )
        user.name = "Alice B."
        user.save(update_fields=["name"])
        updated = User.objects.get(pk=user.pk)
        assert updated.name == "Alice B."

    def test_user_can_be_deleted(self):
        user = User.objects.create_user(
            email="alice@example.com", name="Alice", password="StrongPassw0rd!"
        )
        user.delete()
        assert User.objects.count() == 0

    def test_create_read_update_delete_user(self):
        _ = User.objects.create_user(
            email="alice@example.com", name="Alice", password="StrongPassw0rd!"
        )
        assert User.objects.count() == 1

        fetched = User.objects.get(email="alice@example.com")
        assert fetched.name == "Alice"

        fetched.name = "Alice B."
        fetched.save(update_fields=["name"])
        assert User.objects.get(pk=fetched.pk).name == "Alice B."

        fetched.delete()
        assert User.objects.count() == 0


@pytest.mark.django_db
class TestFileVersionModelCRUD:
    def _make_upload(self, name="doc.txt", content=b"hello"):
        return SimpleUploadedFile(name, content, content_type="text/plain")

    def test_file_version_can_be_created(self, user, media_storage):
        upload = self._make_upload()
        fv = FileVersion.objects.create(
            file_name=upload.name,
            version_number=1,
            created_by=user,
            file=upload,
            path="docs",
        )
        assert fv.pk is not None
        assert fv.file_size == 5

        expected_hash = hashlib.sha256(
            b"hello" + b"1" + str(user.pk).encode()
        ).hexdigest()
        assert fv.content_hash == expected_hash

    def test_file_version_can_be_read(self, user, media_storage):
        upload = self._make_upload()
        fv = FileVersion.objects.create(
            file_name=upload.name,
            version_number=1,
            created_by=user,
            file=upload,
            path="docs",
        )
        fetched = FileVersion.objects.get(pk=fv.pk)
        assert fetched.path == "docs"

    def test_file_version_can_be_updated(self, user, media_storage):
        upload = self._make_upload()
        fv = FileVersion.objects.create(
            file_name=upload.name,
            version_number=1,
            created_by=user,
            file=upload,
            path="docs",
        )
        fv.path = "docs/renamed"
        fv.save(update_fields=["path"])
        assert FileVersion.objects.get(pk=fv.pk).path == "docs/renamed"

    def test_file_version_can_be_deleted(self, user, media_storage):
        upload = self._make_upload()
        fv = FileVersion.objects.create(
            file_name=upload.name,
            version_number=1,
            created_by=user,
            file=upload,
            path="docs",
        )
        fv.delete()
        assert FileVersion.objects.count() == 0

    def test_create_read_update_delete_file_version(self, user, media_storage):
        upload = self._make_upload()
        fv = FileVersion.objects.create(
            file_name=upload.name,
            version_number=1,
            created_by=user,
            file=upload,
            path="docs",
        )

        assert fv.file_size == 5
        expected_hash = hashlib.sha256(
            b"hello" + b"1" + str(user.pk).encode()
        ).hexdigest()
        assert fv.content_hash == expected_hash

        fetched = FileVersion.objects.get(pk=fv.pk)
        assert fetched.path == "docs"

        fetched.path = "docs/renamed"
        fetched.save(update_fields=["path"])
        assert FileVersion.objects.get(pk=fv.pk).path == "docs/renamed"

        fetched.delete()
        assert FileVersion.objects.count() == 0
