import logging
from io import BytesIO

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from PIL import Image, UnidentifiedImageError

from app import metrics
from app.config import (
    ALLOWED_ANGLES,
    ALLOWED_CONTENT_TYPES,
    ALLOWED_OPERATIONS,
    MAX_IMAGE_PIXELS,
    MAX_UPLOAD_BYTES,
    MAX_WIDTH,
)

logger = logging.getLogger("app.transform")
router = APIRouter()


def _resize_by_width(img: Image.Image, width: int) -> Image.Image:
    if width < 1 or width > MAX_WIDTH:
        raise HTTPException(status_code=400, detail=f"width должен быть от 1 до {MAX_WIDTH}")
    ratio = width / img.width
    height = max(1, round(img.height * ratio))
    return img.resize((width, height), Image.LANCZOS)


def _to_grayscale(img: Image.Image) -> Image.Image:
    return img.convert("L")


def _rotate(img: Image.Image, angle: int) -> Image.Image:
    if angle not in ALLOWED_ANGLES:
        raise HTTPException(status_code=400, detail="angle должен быть 90, 180 или 270")
    return img.rotate(-angle, expand=True)


@router.post("/api/transform")
async def transform(
    file: UploadFile | None = File(None),
    operation: str = Form(...),
    width: int | None = Form(None),
    angle: int | None = Form(None),
) -> Response:
    if operation not in ALLOWED_OPERATIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Неизвестная операция '{operation}'. Доступно: {', '.join(sorted(ALLOWED_OPERATIONS))}",
        )

    if file is None or not (file.filename or "").strip():
        raise HTTPException(status_code=400, detail="Файл не передан")

    content_type = file.content_type or ""
    if content_type.split(";")[0].strip().lower() not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Поддерживаются только JPEG и PNG",
        )

    # Читаем на 1 байт больше лимита, чтобы точно поймать превышение
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) == 0:
        raise HTTPException(status_code=400, detail="Пустой файл")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Файл больше 10 МБ")

    metrics.UPLOAD_FILE_SIZE_BYTES.observe(len(data))

    try:
        img = Image.open(BytesIO(data))
        img.load()
    except UnidentifiedImageError:
        metrics.IMAGES_PROCESSED.labels(operation=operation, result="error").inc()
        raise HTTPException(status_code=415, detail="Файл не является корректным изображением")
    except Image.DecompressionBombError:
        metrics.IMAGES_PROCESSED.labels(operation=operation, result="error").inc()
        raise HTTPException(status_code=413, detail="Слишком большое изображение по числу пикселей")
    except Exception:
        logger.exception("Не удалось декодировать изображение")
        metrics.IMAGES_PROCESSED.labels(operation=operation, result="error").inc()
        raise HTTPException(status_code=415, detail="Не удалось декодировать изображение")

    if img.width * img.height > MAX_IMAGE_PIXELS:
        metrics.IMAGES_PROCESSED.labels(operation=operation, result="error").inc()
        raise HTTPException(status_code=413, detail="Слишком большое изображение по числу пикселей")

    params = {"width": width, "angle": angle}
    with metrics.IMAGE_PROCESSING_SECONDS.labels(operation=operation).time():
        try:
            if operation == "resize":
                result = _resize_by_width(img, width)  # type: ignore[arg-type]
            elif operation == "grayscale":
                result = _to_grayscale(img)
            else:
                result = _rotate(img, angle)  # type: ignore[arg-type]
        except HTTPException:
            metrics.IMAGES_PROCESSED.labels(operation=operation, result="error").inc()
            raise
        except Exception:
            logger.exception("Ошибка обработки изображения")
            metrics.IMAGES_PROCESSED.labels(operation=operation, result="error").inc()
            raise HTTPException(status_code=500, detail="Внутренняя ошибка обработки")

    out = BytesIO()
    fmt = "JPEG" if img.format == "JPEG" else "PNG"
    save_kwargs = {"quality": 92} if fmt == "JPEG" else {}
    result.save(out, format=fmt, **save_kwargs)

    metrics.IMAGES_PROCESSED.labels(operation=operation, result="ok").inc()
    ext = "jpg" if fmt == "JPEG" else "png"
    return Response(
        content=out.getvalue(),
        media_type=content_type.split(";")[0].strip().lower(),
        headers={"Content-Disposition": f'attachment; filename="result.{ext}"'},
    )
