from PIL import Image

MAX_UPLOAD_BYTES = 10 * 1024 * 1024   # 10 МБ — лимит входящего файла
MAX_IMAGE_PIXELS = 40_000_000         # защита от «декомпрессионных бомб»
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}
ALLOWED_OPERATIONS = {"resize", "grayscale", "rotate"}
ALLOWED_ANGLES = {90, 180, 270}
MAX_WIDTH = 10000                     # разумный предел для resize

# Порог срабатывания Pillow на слишком большие картинки
Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS
