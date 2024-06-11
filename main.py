from typing import List, Dict, Set
from playwright.sync_api import sync_playwright, Page
import bs4
import csv
from loguru import logger


class JobScraper:
    def __init__(self, keyword: str):
        self.keyword: str = keyword
        self.jobs_db: List[Dict[str, str]] = []
        self.previous_job_links: Set[str] = set()

    def fetch_jobs(self, page: Page) -> None:
        page.goto("https://www.wanted.co.kr")
        page.wait_for_selector("button.Aside_searchButton__Xhqq3").click()
        page.wait_for_selector("input[placeholder='검색어를 입력해 주세요.']").fill(
            self.keyword
        )
        page.keyboard.press("Enter")
        page.wait_for_selector("a#search_tab_position").click()

        while True:
            page.keyboard.press("End")
            page.wait_for_timeout(3000)

            content = page.content()
            soup = bs4.BeautifulSoup(content, "html.parser")
            jobs = soup.find_all(
                "div",
                class_="JobCard_container__FqChn JobCard_container--variant-card__znjV9",
            )

            new_jobs_found = False

            for job in jobs:
                link = f"https://www.wanted.co.kr{job.find('a')['href']}"
                if link in self.previous_job_links:
                    continue

                self.previous_job_links.add(link)
                new_jobs_found = True

                title = job.find("strong", class_="JobCard_title__ddkwM").text.strip()
                company_name = job.find(
                    "span", class_="JobCard_companyName__vZMqJ"
                ).text.strip()
                reward = job.find("span", class_="JobCard_reward__sdyHn").text.strip()

                self.jobs_db.append(
                    {
                        "title": title,
                        "company_name": company_name,
                        "reward": reward,
                        "link": link,
                    }
                )

            if not new_jobs_found:
                logger.debug(f"No new jobs found for {self.keyword}")
                break

    def save_to_csv(self) -> None:
        filename = f"{self.keyword}_jobs.csv"
        logger.debug(f"Saving jobs to {filename}")
        with open(filename, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["title", "company_name", "reward", "link"])

            for job in self.jobs_db:
                writer.writerow(list(job.values()))


class JobScraperManager:
    def __init__(self, keywords: List[str]):
        self.keywords: List[str] = keywords

    def run(self) -> None:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            for keyword in self.keywords:
                logger.debug(f"Fetching jobs for {keyword}")
                scraper = JobScraper(keyword)
                scraper.fetch_jobs(page)
                scraper.save_to_csv()


if __name__ == "__main__":
    try:
        logger.debug("Start job scraper...")
        keywords = ["flutter", "python", "java"]
        manager = JobScraperManager(keywords)
        manager.run()
    except Exception as e:
        logger.exception(e)
    finally:
        logger.debug("Job scraper finished.")
