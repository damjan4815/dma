from django.contrib.auth import get_user_model
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import permissions, viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import action
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
)
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from ..models import FileVersion
from .serializers import FileVersionSerializer, UserSerializer

User = get_user_model()


class FileVersionViewSet(
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    DestroyModelMixin,
    viewsets.GenericViewSet,
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


class FileDownloadViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [SessionAuthentication, TokenAuthentication]

    def get_queryset(self):
        return FileVersion.objects.filter(created_by=self.request.user)

    @extend_schema(
        summary="Download file by ID",
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.BINARY, description="Binary file download"
            ),
            404: OpenApiResponse(description="File not found"),
        },
    )
    def retrieve(self, request, pk=None):
        file_version = get_object_or_404(self.get_queryset(), pk=pk)
        return FileResponse(
            file_version.file, as_attachment=True, filename=file_version.file_name
        )

    @extend_schema(
        summary="Download file by path and name",
        parameters=[
            OpenApiParameter(
                name="revision",
                description="File version number",
                required=False,
                type=int,
                location="query",
            )
        ],
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.BINARY, description="Binary file download"
            ),
            404: OpenApiResponse(description="File not found"),
        },
    )
    @action(detail=False, methods=["get"], url_path=r"(?P<path>.+)/(?P<filename>[^/]+)")
    def download_by_url(self, request, path=None, filename=None):
        revision = request.query_params.get("revision")
        path = path
        filename = filename

        qs = self.get_queryset().filter(path=path, file_name=filename)
        if revision is not None:
            qs = qs.filter(version_number=revision)
        else:
            qs = qs.order_by("-version_number")

        file_version = qs.first()
        if not file_version:
            raise Http404("File not found")
        return FileResponse(
            file_version.file, as_attachment=True, filename=file_version.file_name
        )

    @extend_schema(
        summary="Download file by content hash",
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.BINARY, description="Binary file download"
            ),
            404: OpenApiResponse(description="File not found"),
        },
    )
    @action(detail=False, methods=["get"], url_path=r"cas/(?P<hash>[0-9a-fA-F]{64})")
    def download_by_hash(self, request, hash=None):
        file_version = self.get_queryset().filter(content_hash=hash).first()
        if not file_version:
            raise Http404("File not found")
        return FileResponse(
            file_version.file, as_attachment=True, filename=file_version.file_name
        )


class UserViewSet(CreateModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = [SessionAuthentication, TokenAuthentication]

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]
        if self.action == "me":
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]

    @extend_schema(responses=UserSerializer, summary="Get own profile")
    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
