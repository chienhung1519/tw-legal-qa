import requests
from bs4 import BeautifulSoup
import pandas as pd
from tenacity import retry, wait_fixed, stop_after_attempt, before_sleep_log, RetryError
from argparse import ArgumentParser
import time
from tqdm import tqdm
import logging
from pathlib import Path


BASE_URL = "https://www.legis-pedia.com/QA"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
SLEEP_TIME = 1
WAIT_TIME = 60
ATTEMPT = 3


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_args():
    parser = ArgumentParser(description="Scrape QA data from legis-pedia")
    parser.add_argument("--output_dir", type=str, default="outputs", help="Path to save the scraped data")
    parser.add_argument("--max_page", type=int, default=226, help="Number of pages to scrape")
    parser.add_argument("--skip_main_page", action="store_true", help="Skip scraping the main page")
    return parser.parse_args()


@retry(wait=wait_fixed(WAIT_TIME), stop=stop_after_attempt(ATTEMPT), before_sleep=before_sleep_log(logger, logging.WARNING))
def fetch_url(url: str) -> str:
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.text


def extract_question_urls(soup: BeautifulSoup) -> list[str]:
    questions = soup.find_all("h3")
    return [q.find('a')['href'] for q in questions]


def extract_data(soup: BeautifulSoup, url: str) -> dict:
    try:
        title = soup.find('h1').text.strip()
    except AttributeError:
        title = None
        logger.warning(f"Failed to extract title from {url}")
    try:
        question = soup.find('p', class_='page-desc page-question-desc').text.strip()
    except AttributeError:
        question = None
        if title is None:
            logger.warning(f"Failed to extract question from {url}")
    try:
        replier = soup.find('div', class_='inline-block').text.strip()
    except AttributeError:
        replier = None
        logger.warning(f"Failed to extract replier from {url}")
    try:
        answer = soup.find('div', class_='QaAnswerOne-content-main').text.strip()
    except AttributeError:
        answer = None
        logger.warning(f"Failed to extract answer from {url}")
    return {
        "title": title, 
        "question": question, 
        "replier": replier,
        "answer": answer, 
        "url": url, 
        "text": f"{title}\n{question}\n{replier}\n{answer}\n{url}"
    }


def main():
    args = parse_args()

    # Create the output directory
    Path(args.output_path).mkdir(parents=True, exist_ok=True)

    if not args.skip_main_page:
        # Scrape the main page
        question_urls = []
        for page in tqdm(range(1, args.max_page + 1), desc="Scraping main page"):
            url = f"{BASE_URL}?page={page}"
            try:
                html = fetch_url(url)
            except RetryError as re:
                logger.error(re)
                continue
            soup = BeautifulSoup(html, "html.parser")
            question_urls.extend(extract_question_urls(soup))
            time.sleep(SLEEP_TIME)

        # Remove duplicates
        question_urls = list(set(question_urls))

        # Print the number of questions
        logger.info(f"Found {len(question_urls)} questions")

        # Save the question URLs
        Path(args.output_dir, "question_urls.txt").write_text("\n".join(question_urls))

    # Load the question URLs
    question_urls = Path(args.output_path, "question_urls.txt").read_text().strip().split("\n")

    # Scrape the QA pages
    data = []
    for url in tqdm(question_urls, desc="Scraping QA pages"):
        try:
            html = fetch_url(url)
        except RetryError as re:
            logger.error(re)
            continue
        soup = BeautifulSoup(html, "html.parser")
        data.append(extract_data(soup, url))
        time.sleep(SLEEP_TIME)

    # Print the number of questions
    logger.info(f"Scraped {len(data)} QA pages")
    
    # Save the data
    df = pd.DataFrame(data)
    df.to_json(f"{args.output_dir}/legal_qa.jsonl", orient="records", lines=True, force_ascii=False)


if __name__ == "__main__":
    main()