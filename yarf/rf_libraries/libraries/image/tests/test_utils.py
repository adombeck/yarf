import os
from unittest.mock import ANY, Mock, call, patch

import pytest

from yarf.rf_libraries.libraries.image.utils import log_image


class TestImageUtils:
    @patch("yarf.rf_libraries.libraries.image.utils._get_images_dir")
    @patch("yarf.rf_libraries.libraries.image.utils.to_image")
    @patch("yarf.rf_libraries.libraries.image.utils.logger")
    def test_log_image_saves_file_when_yarf_image_dir_set(
        self, mock_logger, mock_to_image, mock_get_images_dir, tmp_path
    ):
        """
        When ${YARF_IMAGE_DIR} is set, the image should be saved as a WebP
        file and referenced by a relative URL — not embedded as base64.
        """
        images_dir = tmp_path / "images"
        images_dir.mkdir()
        mock_get_images_dir.return_value = str(images_dir)

        image = Mock()
        pil_image = Mock()
        pil_image.convert.return_value = pil_image
        mock_to_image.return_value = pil_image

        with patch(
            "yarf.rf_libraries.libraries.image.utils.BuiltIn"
        ) as mock_builtin:
            mock_builtin.return_value.get_variable_value.return_value = str(tmp_path)
            log_image(image, "Debug message")

        # The image should have been converted to RGB and saved as WebP.
        pil_image.convert.assert_called_once_with("RGB")
        save_call = pil_image.convert.return_value.save.call_args
        saved_path = save_call.args[0]
        assert saved_path.startswith(str(images_dir))
        assert saved_path.endswith(".webp")
        assert save_call.kwargs.get("format") == "WEBP"

        # The log message must reference the file by a relative path, not base64.
        mock_logger.info.assert_called_once_with(ANY, html=True)
        logged_html = mock_logger.info.call_args.args[0]
        assert logged_html.startswith("Debug message")
        # Path should be relative to OUTPUT_DIR (tmp_path), so starts with "images/"
        assert 'src="images/' in logged_html
        assert "base64" not in logged_html

    @patch("yarf.rf_libraries.libraries.image.utils._get_images_dir")
    @patch("yarf.rf_libraries.libraries.image.utils.to_base64")
    @patch("yarf.rf_libraries.libraries.image.utils.to_image")
    @patch("yarf.rf_libraries.libraries.image.utils.logger")
    def test_log_image_falls_back_to_base64_when_yarf_image_dir_not_set(
        self, mock_logger, mock_to_image, mock_base64, mock_get_images_dir
    ):
        """
        When ${YARF_IMAGE_DIR} is not set, the image should be base64-encoded
        and embedded inline.
        """
        mock_get_images_dir.return_value = None
        mock_base64.return_value = "FAKEBASE64"

        image = Mock()
        mock_to_image.return_value = image

        log_image(image, "Debug message")

        mock_base64.assert_called_once_with(image)
        mock_logger.info.assert_called_once_with(ANY, html=True)
        logged_html = mock_logger.info.call_args.args[0]
        assert logged_html.startswith("Debug message")
        assert "base64" in logged_html
