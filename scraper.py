import requests
import csv
from bs4 import BeautifulSoup
from newspaper import Article

OUTPUT_FILE = "csvfile.csv"


def get_links(source_url, url):
    """

    :param url: url of the web page to scrape
    :return: list of links to news articles on the page
    """
    if source_url[-1] == "/":
        source_url = source_url[:len(source_url) - 1]
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    anchors = soup.find_all("a")
    anchors = [a for a in anchors if len(a.text.split()) > 5]
    urls = [a.get("href") for a in anchors]
    for i in range(len(urls)):
        if urls[i].startswith("/"):
            urls[i] = source_url + urls[i]
    urls = [url for url in urls if len(url[len(source_url) + 1:].split("/")) > 2]
    urls = [url for url in urls if url.startswith(source_url)]

    return urls


def write_urls_to_file(urls, file):
    urls = get_links(source_url)
    text = "\n".join(urls)
    with open(file, "w", encoding="utf-8") \
            as f:
        f.writelines(text)


def get_article_text(source_url, urls, file=OUTPUT_FILE, level=0):
    rows = []
    for url in urls[:50]:
        row = []
        try:
            article = Article(url)
            article.download()
            article.parse()
            print(article.url)
            row += [source_url, article.text, level]
            rows.append(row)
        except:
            continue
    print("Writing level {0} articles...".format(level))
    print(rows)
    print(len(rows))
    with open(file, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerows(rows)


if __name__ == "__main__":

    with open(r"C:\Users\abhib\Desktop\IR-Project\vox-links.txt", "r", encoding="utf-8") as f:
        urls = f.readlines()
    home_page_urls = [url.strip() for url in urls]

    source_url = "https://www.vox.com/"
    # urls_in_links = []
    # for url in urls:
    #     urls_in_links.append(get_links(source_url, url))
    # for i in urls_in_links:
    #     print(len(i), i)

    # home_page_urls = get_links(source_url, source_url)
    print(len(home_page_urls))
    get_article_text(source_url, home_page_urls, level=0)
    print("Level 0 done.")

    level_1_urls = []
    for url in home_page_urls:
        level_1_urls += get_links(source_url, url)
    print(len(level_1_urls))
    get_article_text(source_url, level_1_urls, level=1)
    print("Level 1 done.")

    level_2_urls = []
    for url in level_1_urls:
        level_2_urls += get_links(source_url, url)
    print(len(level_2_urls))
    get_article_text(source_url, level_2_urls, level=2)
    print("Level 2 done.")

    level_3_urls = []
    for url in level_2_urls:
        level_3_urls += get_links(source_url, url)
    print(len(level_3_urls))
    get_article_text(source_url, level_3_urls, level=3)
    print("Level 3 done.")

    level_4_urls = []
    for url in level_3_urls:
        level_4_urls += get_links(source_url, url)
    print(len(level_4_urls))
    get_article_text(source_url, level_4_urls, level=4)
    print("Level 4 done.")

