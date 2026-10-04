import io
import os
import random

from locust import HttpUser, between, task
from PIL import Image, ImageDraw

SIDE = int(os.getenv("TEST_IMAGE_SIZE", "1200"))  # сторона тестовой картинки, px
POOL_SIZE = 5                                     # сколько картинок генерит каждый виртуальный юзер


def _make_image(fmt: str) -> bytes:
    """Генерирует случайное тестовое изображение с фигурами."""
    img = Image.new(
        "RGB", (SIDE, SIDE),
        (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)),
    )
    draw = ImageDraw.Draw(img)
    for _ in range(30):
        x1, y1 = random.randint(0, SIDE - 100), random.randint(0, SIDE - 100)
        x2, y2 = x1 + random.randint(20, 100), y1 + random.randint(20, 100)
        draw.ellipse((x1, y1, x2, y2), fill=(random.randint(0, 255),) * 3)
    buf = io.BytesIO()
    if fmt == "JPEG":
        img.save(buf, format="JPEG", quality=85)
        return buf.getvalue()
    img.save(buf, format="PNG")
    return buf.getvalue()


class ImageUser(HttpUser):
    wait_time = between(0.2, 1.0)

    def on_start(self):
        self.pool = [("t.jpg", _make_image("JPEG"), "image/jpeg") for _ in range(POOL_SIZE)]
        self.pool += [("t.png", _make_image("PNG"), "image/png") for _ in range(POOL_SIZE)]

    @task(4)
    def grayscale(self):
        self._send("grayscale", {})

    @task(3)
    def resize(self):
        self._send("resize", {"width": random.choice([400, 800, 1200])})

    @task(2)
    def rotate(self):
        self._send("rotate", {"angle": random.choice([90, 180, 270])})

    def _send(self, operation: str, params: dict):
        name, data, mime = random.choice(self.pool)
        with self.client.post(
            "/api/transform",
            files={"file": (name, data, mime)},
            data={"operation": operation, **params},
            catch_response=True,
        ) as resp:
            ct = resp.headers.get("content-type", "")
            if resp.status_code == 200 and ct.startswith("image/"):
                resp.success()
            else:
                try:
                    detail = resp.json().get("error", "")
                except Exception:
                    detail = ""
                resp.failure(f"{resp.status_code} {detail}")
