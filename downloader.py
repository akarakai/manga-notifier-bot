import requests
import logger
from io import BytesIO
import img2pdf

log = logger.get_logger(__name__)

def download_pdf(urls: list[str]) -> BytesIO:
    img_bytes_list = []
    for (page_nr, url) in enumerate(urls, start=1):
        log.info(f"Downloading page {page_nr}/{len(urls)}")
        response = requests.get(url)
        if response.status_code != 200:
            log.warning(f"Failed to download image from {url}. Status code: {response.status_code}")

        image_bytes = response.content
        img_bytes_list.append(image_bytes)

    pdf_buffer =  BytesIO()
    pdf_buffer.write(img2pdf.convert(img_bytes_list))
    pdf_buffer.seek(0) # important to reset the buffer position to the beginning
    log.info("Pdf created successfully")
    return pdf_buffer
