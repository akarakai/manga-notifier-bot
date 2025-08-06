from dataclasses import dataclass
import datetime
import selenium.webdriver as driver
import selenium.webdriver.chrome as chrome
import selenium.webdriver.common.by as by
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


@dataclass
class Manga:
    title: str
    url: str

@dataclass
class Chapter:
    manga: Manga
    title: str 
    url: str
    published_at: datetime


class MangaScraper:
    def __init__(self):
        self.driver = driver.Firefox()
        self.homepage = "https://weebcentral.com/"
        self.mangas_container_xpath = "/html/body/header/section[1]/div[2]/section/div[2]"
    
    def go_to_homepage(self):
        self.driver.get(self.homepage)

    def get_queried_mangas(self, query: str) -> list[Manga]:
        self.driver.find_element(by.By.ID, "quick-search-input").send_keys(query)
        wait = WebDriverWait(self.driver, 1)
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
        return Chapter(
            manga=manga,
            title=title,
            url=url,
            published_at=datetime_obj
        )

    def close(self):
        print("Closing the browser...")
        self.driver.quit()


def main(): 
    scraper = MangaScraper()
    scraper.go_to_homepage()
    mangas = scraper.get_queried_mangas("One Piece")
    first = mangas[0]
    last_chapter = scraper.get_last_chapter(first)
    scraper.close()

if __name__ == "__main__":
    main()