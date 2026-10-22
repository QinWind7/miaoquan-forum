"""图片上传：类型白名单 + 大小上限 + uuid 重命名（防覆盖与路径穿越）。"""
import uuid
from pathlib import Path

from PIL import Image
from rest_framework.exceptions import ValidationError

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_IMAGE_MB = 5


def _ext(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    return suffix if suffix in ALLOWED_SUFFIXES else ".jpg"


def validate_image(file, max_mb: int = MAX_IMAGE_MB) -> None:
    """在写库前校验。

    必须抛 DRF 的 ValidationError（而不是 django.core.exceptions.ValidationError），
    否则不会被 DRF 的异常处理器识别，会被当成 500。
    """
    if getattr(file, "size", 0) > max_mb * 1024 * 1024:
        raise ValidationError(f"图片不能超过 {max_mb}MB")
    content_type = getattr(file, "content_type", None)
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ValidationError("仅支持 jpg / png / webp / gif 格式的图片")
    try:
        # 只信赖真实文件头，避免改扩展名绕过校验
        Image.open(file).verify()
    except Exception:
        raise ValidationError("文件不是有效的图片")
    finally:
        file.seek(0)


def avatar_upload_to(instance, filename: str) -> str:
    return f"avatar/{uuid.uuid4().hex}{_ext(filename)}"


def post_upload_to(instance, filename: str) -> str:
    return f"post/{uuid.uuid4().hex}{_ext(filename)}"


def board_upload_to(instance, filename: str) -> str:
    return f"board/{uuid.uuid4().hex}{_ext(filename)}"
