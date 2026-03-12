import os
from io import BytesIO
from django.core.files.base import ContentFile
from PIL import Image


THUMBNAIL_MAX_SIZE = (800, 600)   # max dimensions — resizes down, never up
WEBP_QUALITY = 82                 # 80-85 is the sweet spot: visually lossless, very small


def convert_to_webp(image_field) -> ContentFile:
    """
    Open an uploaded image field, resize if needed, convert to WebP,
    and return a ContentFile ready to be saved back to the field.
    """
    img = Image.open(image_field)

    # Convert palette or RGBA modes that don't survive WebP cleanly
    if img.mode in ('RGBA', 'LA'):
        background = Image.new('RGB', img.size, (0, 0, 0))
        if img.mode == 'RGBA':
            background.paste(img, mask=img.split()[3])
        else:
            background.paste(img, mask=img.split()[1])
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    # Resize down only — never upscale
    img.thumbnail(THUMBNAIL_MAX_SIZE, Image.LANCZOS)

    buffer = BytesIO()
    img.save(buffer, format='WEBP', quality=WEBP_QUALITY, method=6)
    buffer.seek(0)
    return ContentFile(buffer.read())


def webp_filename(original_name: str) -> str:
    """Swap any extension for .webp"""
    base = os.path.splitext(os.path.basename(original_name))[0]
    return f"{base}.webp"