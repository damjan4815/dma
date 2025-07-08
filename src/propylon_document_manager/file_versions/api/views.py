from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin, ListModelMixin, RetrieveModelMixin
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response

from ..models import FileVersion
from .serializers import FileVersionSerializer, UserSerializer

User = get_user_model()


class FileVersionViewSet(
    CreateModelMixin, ListModelMixin, RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = FileVersion.objects.all()
    serializer_class = FileVersionSerializer
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        return FileVersion.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ["create"]:
            return [permissions.AllowAny()]
        if self.action in ["self", "update_self", "list", "retrieve"]:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]

    @extend_schema(responses=UserSerializer, summary="Retrieve own user")
    @action(detail=False, methods=["get"], url_path="self")
    def self(self, request: Request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @extend_schema(
        request=UserSerializer, responses=UserSerializer, summary="Update own user"
    )
    @action(detail=False, methods=["put", "patch"], url_path="self")
    def update_self(self, request: Request):
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
