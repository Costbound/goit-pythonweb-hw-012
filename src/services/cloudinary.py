"""
Cloudinary image upload service.

This module provides integration with Cloudinary for uploading and managing
user avatar images with automatic resizing and optimization.
"""

import cloudinary
import cloudinary.uploader


class CloudinaryService:
    """
    Service for uploading images to Cloudinary.

    Handles configuration and uploading of user avatar images to Cloudinary
    with automatic transformations and URL generation.

    :param cloud_name: Cloudinary cloud name.
    :type cloud_name: str
    :param api_key: Cloudinary API key.
    :type api_key: str
    :param api_secret: Cloudinary API secret.
    :type api_secret: str
    """

    def __init__(self, cloud_name, api_key, api_secret):
        """
        Initialize Cloudinary service with credentials.

        Configures Cloudinary SDK with provided credentials and enables secure connections.

        :param cloud_name: Cloudinary cloud name.
        :type cloud_name: str
        :param api_key: Cloudinary API key.
        :type api_key: str
        :param api_secret: Cloudinary API secret.
        :type api_secret: str
        """
        self.cloud_name = cloud_name
        self.api_key = api_key
        self.api_secret = api_secret
        cloudinary.config(
            cloud_name=self.cloud_name,
            api_key=self.api_key,
            api_secret=self.api_secret,
            secure=True,
        )

    @staticmethod
    def upload_file(file, user_id) -> str:
        """
        Upload user avatar file to Cloudinary.

        Uploads the image file to Cloudinary with user-specific public ID,
        applies transformations (250x250 crop fill), and returns the optimized URL.

        :param file: File object containing the image to upload.
        :type file: UploadFile
        :param user_id: User ID for organizing uploads.
        :type user_id: int
        :return: URL of the uploaded and transformed image.
        :rtype: str
        """
        public_id = f"RestApp/{user_id}"
        r = cloudinary.uploader.upload(file.file, public_id=public_id, overwrite=True)
        src_url = cloudinary.CloudinaryImage(public_id).build_url(
            width=250, height=250, crop="fill", version=r.get("version")
        )
        return src_url
