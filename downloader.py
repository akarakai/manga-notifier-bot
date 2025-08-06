import requests
import logger
from io import BytesIO
import img2pdf
import time 
import random

log = logger.get_logger(__name__)

def download_pdf(urls: list[str]) -> BytesIO:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0.0.0 Safari/537.36"
        )
    }
    img_bytes_list = []

    for page_nr, url in enumerate(urls, start=1):
        log.info(f"Downloading page {page_nr}/{len(urls)}")

        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            log.warning(f"Failed to download image from {url}. Status code: {response.status_code}")
            continue

        img_bytes_list.append(response.content)

        # Random short delay between requests
        time.sleep(random.uniform(1, 3))

    if not img_bytes_list:
        raise ValueError("No valid images downloaded. Cannot create PDF.")

    pdf_buffer = BytesIO()
    pdf_buffer.write(img2pdf.convert(img_bytes_list))
    pdf_buffer.seek(0)
    log.info("PDF created successfully")

    return pdf_buffer