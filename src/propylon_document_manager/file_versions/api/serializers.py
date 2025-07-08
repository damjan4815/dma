import re

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from ..models import FileVersion

AuthUser = get_user_model()


class FileVersionSerializer(serializers.ModelSerializer):
    upload = serializers.FileField(write_only=True, required=True)

    class Meta:
        model = FileVersion
        fields = [
            "id",
            "file_name",
            "version_number",
            "path",
            "file_size",
            "mime_type",
            "content_hash",
            "created_at",
            "created_by_id",
            "upload",
        ]
        read_only_fields = [
            "id",
            "file_name",
            "version_number",
            "file_size",
            "mime_type",
            "content_hash",
            "created_at",
            "created_by_id",
        ]
        write_only_fields = ["upload"]

    def validate_path(self, value: str) -> str:
        if "\x00" in value:
            raise serializers.ValidationError("Path cannot contain null byte")

        if value.startswith("/"):
            raise serializers.ValidationError("Path cannot start with /")

        if re.search(r'[\\:\*\?"<>|]', value):
            raise serializers.ValidationError(
                'Path contains forbidden characters: \\ : * ? " < > |'
            )

        if len(value) > 255:
            raise serializers.ValidationError("Path exceeds 255 characters")

        if not re.match(r"^[\w\-./]+$", value):
            raise serializers.ValidationError(
                "Path may only contain letters, digits, underscore (_), hyphen (-), forward-slash (/),or dot"
            )

        return value

    def create(self, validated_data: dict):
        upload = validated_data.pop("upload")
        user = self.context["request"].user
        name = upload.name

        last = (
            FileVersion.objects.filter(file_name=name, created_by=user)
            .order_by("-version_number")
            .first()
        )
        next_version = last.version_number + 1 if last else 1
        instance = FileVersion.objects.create(
            file_name=name,
            version_number=next_version,
            created_by=user,
            file=upload,
            path=validated_data.get("path"),
        )
        return instance

    def perform_destroy(self, instance):
        if instance.created_by != self.request.user:
            return
        instance.delete()


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=[
            UniqueValidator(
                queryset=AuthUser.objects.all(), message="Email already exists"
            )
        ],
        help_text="User email address (used for login)",
    )
    name = serializers.CharField(
        required=False, allow_blank=True, help_text="User full name"
    )
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text="Password must be at least 8 characters long",
    )

    class Meta:
        model = AuthUser
        fields = ["id", "email", "name", "password"]
        read_only_fields = ["id"]

    def create(self, validated_data: dict):
        password = validated_data.pop("password")
        user = AuthUser.objects.create_user(
            email=validated_data["email"],
            password=password,
            name=validated_data.get("name", ""),
        )
        return user
