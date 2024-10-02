# Crawl Legal QA

This script scrapes the QA data from the [legis-pedia website](https://www.legis-pedia.com/QA). 
The data is saved in the outputs directory as legal_qa.json.

## Requirement

```
! pip install requests beautifulsoup4 pandas tenacity tqdm
```

## Arguments

* `output_dir`: Path to save the scraped data. Default value is `outputs`.
* `max_page`: Number of pages to scrape. Default value is `226`.
* `skip_main_page`: Skip scraping the main page and directly scraping the qa page if main page was already scraped.

## Run Script

```
bash run.sh
```