import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


class TestUsersEndpoints:
    register_url = reverse("api:user-list")
    me_url = reverse("api:user-me")

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.client = APIClient()

    def test_user_can_register(self):
        payload = {
            "email": "bob@example.com",
            "name": "Bob",
            "password": "Sup3rS3cret!",
        }
        resp = self.client.post(self.register_url, payload)
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["email"] == payload["email"]

    def test_user_me_endpoint_returns_own_profile(self, user):
        self.client.force_authenticate(user)
        response = self.client.get(self.me_url)
        self.client.logout()

        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == user.email
        assert response.data["name"] == user.name

    def test_user_me_endpoint_requires_authentication(self):
        response = self.client.get(self.me_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_register_with_duplicate_email(self, user):
        payload = {
            "email": user.email,
            "name": "Someone",
            "password": "AnotherPass123!",
        }
        response = self.client.post(self.register_url, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

    def test_register_user(self):
        payload = {
            "email": "bob@example.com",
            "name": "Bob",
            "password": "Sup3rS3cret!",
        }
        resp = self.client.post(self.register_url, payload)
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["email"] == payload["email"]

    def test_self_retrieve(self, user):
        self.client.force_authenticate(user)

        r1 = self.client.get(self.me_url)
        assert r1.status_code == status.HTTP_200_OK
