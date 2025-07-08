from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from ..models import FileVersion, User

AuthUser = get_user_model()


class FileVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileVersion
        fields = "__all__"


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

    def update(self, instance: User, validated_data: dict):
        if "password" in validated_data:
            instance.set_password(validated_data.pop("password"))
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        return instance
