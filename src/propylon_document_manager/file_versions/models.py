import hashlib
import os

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models import CharField, EmailField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class UserProfileManager(BaseUserManager):
    """Class required by Django for managing our users from the management
    command.
    """

    def create_user(self, email, name, password=None):
        """Creates a new user with the given detials."""

        if not email:
            raise ValueError("Users must have an email address.")

        user: User = self.model(
            email=self.normalize_email(email),
            name=name,
        )

        user.is_superuser = False
        user.is_staff = False
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, name, password):
        """Creates and saves a new superuser with given detials."""

        user = self.create_user(email, name, password)

        user.is_superuser = True
        user.is_staff = True

        user.set_password(password)
        user.save(using=self._db)

        return user


class User(AbstractUser):
    """
    Default custom user model for Propylon Document Manager.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    # First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore
    last_name = None  # type: ignore
    email = EmailField(_("email address"), unique=True)
    username = None  # type: ignore

    objects = UserProfileManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"pk": self.id})


def user_directory_path(instance: "FileVersion", filename: str) -> str:
    return os.path.join(
        f"user_{instance.created_by_id}",
        instance.path,
        f"rev_{instance.version_number}-{filename}",
    )


class FileVersion(models.Model):
    file_name = models.fields.TextField()
    version_number = models.fields.IntegerField()
    path = models.fields.TextField()

    file = models.FileField(upload_to=user_directory_path)

    file_size = models.BigIntegerField()
    mime_type = models.TextField()
    content_hash = models.TextField()

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name="file_versions",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["file_name", "version_number", "created_by"],
                name="unique_file_version_per_user",
            )
        ]

    def save(self, *args, **kwargs):
        if not self.pk or "file" in self.get_deferred_fields():
            data = self.file.read()
            hash_data = (
                data
                + str(self.version_number).encode("utf-8")
                + str(self.created_by_id).encode("utf-8")
            )
            self.content_hash = hashlib.sha256(hash_data).hexdigest()
            self.file_size = len(data)
            import mimetypes

            self.mime_type = mimetypes.guess_type(self.file.name)[0] or ""
            self.file.seek(0)

        super().save(*args, **kwargs)
