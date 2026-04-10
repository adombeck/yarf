"""
Image logging keyword for Robot Framework.
"""

import os
import uuid

from PIL import Image
from robot.api import logger
from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn, RobotNotRunningError

from yarf.lib.images.utils import to_base64
from yarf.vendor.RPA.Images import to_image


def _get_images_dir() -> str | None:
    """
    Return the configured image output directory, creating it if needed.

    The directory is read from the Robot Framework variable ``${YARF_IMAGE_DIR}``.
    Returns ``None`` when the variable is not set or when called outside a
    Robot Framework run (e.g. in unit tests).
    """
    try:
        images_dir = BuiltIn().get_variable_value("${YARF_IMAGE_DIR}")
    except RobotNotRunningError:
        return None
    if not images_dir:
        return None
    os.makedirs(images_dir, exist_ok=True)
    return images_dir


@keyword
def log_image(image: Image.Image | str, msg: str = "") -> None:
    """
    Log an image.

    When the Robot Framework variable ``${YARF_IMAGE_DIR}`` is set, the image
    is saved as a WebP file in that directory and referenced by a relative URL
    from the output directory, which keeps the HTML log small and lets the
    browser load images on demand.  When the variable is not set the image is
    base64-encoded and embedded inline as a fallback.

    Args:
        image: Image to log
        msg: Message to log with the image
    """
    pil_image = to_image(image)
    images_dir = _get_images_dir()

    if images_dir is not None:
        filename = f"{uuid.uuid4().hex}.webp"
        filepath = os.path.join(images_dir, filename)
        pil_image.convert("RGB").save(
            filepath, format="WEBP", quality=80, method=4
        )
        # Build a URL relative to ${OUTPUT_DIR} so it works when log.html and
        # the images/ directory are served from the same location.
        try:
            output_dir = BuiltIn().get_variable_value("${OUTPUT_DIR}")
        except RobotNotRunningError:
            output_dir = None
        if output_dir:
            src = os.path.relpath(filepath, output_dir)
        else:
            src = filepath
        image_string = (
            f'{msg}<br /><img style="max-width: 100%" src="{src}" />'
        )
    else:
        image_string = (
            f"{msg}<br />"
            '<img style="max-width: 100%" src="data:image/png;base64,'
            f'{to_base64(pil_image)}" />'
        )

    logger.info(image_string, html=True)
