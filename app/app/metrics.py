from prometheus_client import Counter, Histogram

IMAGES_PROCESSED = Counter(
    "images_processed_total",
    "Количество обработанных изображений",
    ["operation", "result"],  # result: ok | error
)

IMAGE_PROCESSING_SECONDS = Histogram(
    "image_processing_seconds",
    "Время обработки изображения (сек)",
    ["operation"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0),
)

UPLOAD_FILE_SIZE_BYTES = Histogram(
    "upload_file_size_bytes",
    "Размер входящих файлов (байт)",
    buckets=(10_000, 100_000, 500_000, 1_000_000, 5_000_000, 10_485_760),
)
