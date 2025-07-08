from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from propylon_document_manager.file_versions.api.views import (
    FileDownloadViewSet,
    FileVersionViewSet,
    UserViewSet,
)

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register(r"file_versions", FileVersionViewSet)
router.register(r"users", UserViewSet, basename="user")

router.register(r"files", FileDownloadViewSet, basename="files")

app_name = "api"
urlpatterns = router.urls
