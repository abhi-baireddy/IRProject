import requests
import csv
import json
from bs4 import BeautifulSoup
from newspaper import Article

OUTPUT_FILE = "articles.csv"


def get_links(source_url, url):
    """

    :param url: url of the web page to scrape
    :return: list of links to news articles on the page
    """
    if source_url[-1] == "/":
        source_url = source_url[: len(source_url) - 1]
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    anchors = soup.find_all("a")
    anchors = [a for a in anchors if len(a.text.split()) > 5]
    urls = [a.get("href") for a in anchors]
    urls = [u for u in urls if u]
    for i in range(len(urls)):
        if not urls[i].startswith("/www"):
            if urls[i].startswith("/"):
                urls[i] = source_url + urls[i]
    urls = [url for url in urls if len(url[len(source_url) + 1:].split("/")) > 2]
    urls = [url for url in urls if url.startswith(source_url)]
    urls = list(set(urls))
    if source_url != url:
        urls = urls[:25]
    return urls


def get_article_text(source_url, urls, file=OUTPUT_FILE, source="", rating=-1 ,level=0):
    # rows = []
    articles = []
    count = 0
    urls = list(urls)
    for url in urls[:50]:
        # row = []
        try:
            article = Article(url)
            article.download()
            article.parse()
            article.nlp()
            article_json = {
                "source": source,
                "authors": list(article.authors),
                "keywords": list(article.keywords),
                "link": article.url,
                "summary": article.summary,
                "tags": list(article.tags),
                "text": article.text,
                "webpage": article.html,
                "level": level,
                "rating": rating
            }
            count += 1
            # row += [source_url, article.text, level]
            # rows.append(row)
            # OUTPUT_JSON.append(article_json)
            articles.append(article_json)
        except Exception as e:
            print("Exception occurred:", e)
            continue
    # print("Writing level {0} articles...".format(level))
    # with open(file, "a", newline="", encoding="utf-8") as f:
    #     writer = csv.writer(f)
    #     writer.writerows(rows)
    return articles, count


if __name__ == "__main__":

    # source_url = "https://www.dukechronicle.com/"
    ratings_map = {
        'left': -2,
        'lean left': -1,
        'center': 0,
        'lean right': 1,
        'right': 2
    }
    OUTPUT_JSON = []
    article_counts_json = []
    sources = []
    articles_so_far = set()
    level_0_article_count = 0
    file = r"C:\Users\abhib\Desktop\IR-Project\source_links.txt"
    with open(file, "r", encoding="utf-8") as f:
        for line in f.readlines():
            sources.append(line.strip().split('-'))
    for source in sources:
        try:
            source_url = source[2]
            rating = ratings_map[source[1]]
            source_name = source[0]
            print(f"Scraping articles from {source_name}: {source_url}")
            home_page_urls = get_links(source_url, source_url)
            articles, level_0_article_count = get_article_text(source_url, home_page_urls,
                                                     source=source_name, rating=rating,
                                                     level=0)
            print("Level 0 done.")
            OUTPUT_JSON.append(articles)

            articles_so_far = articles_so_far.union(home_page_urls)

            level_1_urls = []
            level_1_article_count = 0
            for url in home_page_urls:
                level_1_urls += get_links(source_url, url)
                if len(level_1_urls) > 50:
                    break
            level_1_urls = set(level_1_urls)
            level_1_urls -= articles_so_far
            articles_so_far = articles_so_far.union(level_1_urls)

            articles, level_1_article_count = get_article_text(source_url, level_1_urls,
                                                     source=source_name, rating=rating,
                                                     level=1)
            OUTPUT_JSON += articles
            print("Level 1 done.")

            level_2_urls = []
            level_2_article_count = 0
            for url in level_1_urls:
                level_2_urls += get_links(source_url, url)
                if len(level_2_urls) > 50:
                    break
            level_2_urls = set(level_2_urls)
            level_2_urls -= articles_so_far
            articles_so_far = articles_so_far.union(level_2_urls)
            articles, level_2_article_count = get_article_text(source_url, level_2_urls,
                                                     source=source_name, rating=rating,
                                                     level=2)
            OUTPUT_JSON += articles
            print("Level 2 done.")

            level_3_urls = []
            level_3_article_count = 0
            for url in level_2_urls:
                level_3_urls += get_links(source_url, url)
                if len(level_3_urls) > 50:
                    break
            level_3_urls = set(level_3_urls)
            level_3_urls -= articles_so_far
            articles_so_far = articles_so_far.union(level_3_urls)
            articles, level_3_article_count = get_article_text(source_url, level_3_urls,
                                                     source=source_name, rating=rating,
                                                     level=3)
            OUTPUT_JSON += articles
            print("Level 3 done.")

            level_4_urls = []
            level_4_article_count = 0
            for url in level_3_urls:
                level_4_urls += get_links(source_url, url)
                if len(level_4_urls) > 50:
                    break
            level_4_urls = set(level_4_urls)
            level_4_urls -= articles_so_far
            articles_so_far = articles_so_far.union(level_4_urls)
            articles, level_4_article_count = get_article_text(source_url, level_4_urls,
                                                     source=source_name, rating=rating,
                                                     level=4)
            OUTPUT_JSON += articles
            print("Level 4 done.")


            article_count = level_0_article_count + level_1_article_count + \
                            level_2_article_count + level_3_article_count + level_4_article_count

            print(f"Total number of articles scraped from {source_url}: {article_count} "
                  f"Homepage:"
                  f" {level_0_article_count}, Level 1: {level_1_article_count}, "
                  f"Level 2: {level_2_article_count}, Level 3: {level_3_article_count}"
                  f", Level 4: {level_4_article_count}.")
            counts = {
                "source": source_url,
                "home_page": level_0_article_count,
                "level_1": level_1_article_count,
                "level_2": level_2_article_count,
                "level_3": level_3_article_count,
                "level_4": level_4_article_count,
                "total": article_count
            }
            article_counts_json.append(counts)
        except Exception as e:
            print(f"Failed to scrape {source[0]}. Skipping.")
            print(f"Reason: {e}")
            continue

    json.dump(
        article_counts_json,
        indent=4,
        sort_keys=True,
        fp=open("article_counts.json", "w")
    )
    json.dump(
        OUTPUT_JSON,
        indent=4,
        sort_keys=True,
        fp=open("classifier_train_articles.json", "w")
    )
