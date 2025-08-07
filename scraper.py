from dataclasses import dataclass
import datetime
import logger as logger
import selenium.webdriver as driver
import selenium.webdriver.common.by as by
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

log = logger.get_logger(__name__)


@dataclass
class Chapter:
    title: str 
    url: str
    published_at: datetime

@dataclass
class Manga:
    title: str
    url: str
    last_chapter: Chapter = None

    def add_chapter(self, chapter: Chapter):
        self.last_chapter = chapter


class MangaScraper:

    def __init__(self):
        options = driver.FirefoxOptions()
        options.add_argument("--headless")

        self.driver = driver.Firefox(options)
        self.homepage = "https://weebcentral.com/"
        self.mangas_container_xpath = "/html/body/header/section[1]/div[2]/section/div[2]"
    
    def go_to_homepage(self):
        self.driver.get(self.homepage)

    def get_queried_mangas(self, query: str) -> list[Manga]:
        self.driver.find_element(by.By.ID, "quick-search-input").send_keys(query)
        wait = WebDriverWait(self.driver, 5)
        container = wait.until(EC.presence_of_element_located((by.By.XPATH, self.mangas_container_xpath)))
        a_list = container.find_elements(by.By.TAG_NAME, "a")
        mangas = []
        for a in a_list:
            manga_url = a.get_attribute("href")
            manga_title = a.text
            mangas.append(Manga(title=manga_title, url=manga_url))
        return mangas

    def get_last_chapter(self, manga: Manga) -> Chapter:
        self.driver.get(manga.url)
        last_chapter_div = self.driver.find_element(by.By.ID, "chapter-list").find_element(by.By.TAG_NAME, "div")
        date = last_chapter_div.find_element(by.By.TAG_NAME, "time").get_attribute("datetime")
        datetime_obj = datetime.datetime.fromisoformat(date)   
        url = last_chapter_div.find_element(by.By.TAG_NAME, "a").get_attribute("href")   
        title = last_chapter_div.find_element(by.By.TAG_NAME, "a").text.split("\n")[0].strip()
        last_chapter = Chapter(
            title=title,
            url=url,
            published_at=datetime_obj
        )
        if not manga.last_chapter:
            manga.add_chapter(last_chapter)
        
        return last_chapter
    
    def get_data_from_chapter_url(self, chapter_url: str) -> tuple[str, str]:
        """Extract manga and chapter titles from a chapter URL.
        Args:
            chapter_url (str): The URL of the chapter.
        Returns:
            tuple[str, str]: A tuple containing the manga title and chapter title.
        """
        self.driver.get(chapter_url)
        manga_title = self.driver.find_element(by.By.XPATH, "/html/body/main/section[1]/div/div[1]/a/div").text
        chapter_title = self.driver.find_element(by.By.XPATH, "/html/body/main/section[1]/div/div[1]/button[1]").text
        return manga_title, chapter_title

    
    # TODO change to chapter_url
    def get_chapter_image_urls(self, chapter: Chapter) -> list[str]:
        self.driver.get(chapter.url)
        xpath_container = "/html/body/main/section[3]"
        container = self.driver.find_element(by.By.XPATH, xpath_container)
        image_elements = container.find_elements(by.By.TAG_NAME, "img")
        image_urls = [img.get_attribute("src") for img in image_elements if img.get_attribute("src")]
        return image_urls

    def close(self):
        print("Closing the browser...")
        self.driver.quit()
