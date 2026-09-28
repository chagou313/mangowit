import base64
from unittest.mock import patch

from cloudinary.exceptions import Error as CloudinaryError
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse


PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


class ProfileUploadFailureTests(TestCase):
    def test_cloud_upload_failure_preserves_existing_avatar(self):
        user = get_user_model().objects.create_user(
            username="avatar-user",
            password="safe-test-password",
            profile_picture="profile_pics/original.png",
        )
        self.client.force_login(user)
        self.client.raise_request_exception = False
        avatar = SimpleUploadedFile(
            "replacement.png",
            PNG_1X1,
            content_type="image/png",
        )
        storage = user._meta.get_field("profile_picture").storage

        with patch.object(
            storage,
            "save",
            side_effect=CloudinaryError("upload failed"),
        ):
            response = self.client.post(
                reverse("profile"),
                {
                    "username": user.username,
                    "age": "",
                    "gender": "",
                    "phone_number": "",
                    "profile_picture": avatar,
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "头像上传失败，请稍后重试。")
        user.refresh_from_db()
        self.assertEqual(
            user.profile_picture.name,
            "profile_pics/original.png",
        )
