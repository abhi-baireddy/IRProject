import asyncio
import concurrent.futures
import requests
import csv
from newspaper import Article, fulltext
import re
import os
from glob import glob
import json

def main():
    dataset_path = 'ad_fontes_media_dataset.csv'
    dataset_dir = 'classifier_test_articles'

    allsides_dataset_path = 'allsides_articles_and_ratings.csv'
    allsides_dataset_dir = 'allsides_test_set'

    get_dataset(dataset_path, dataset_dir, 1)
    get_dataset(allsides_dataset_path, allsides_dataset_dir, 0)
    
    

def get_dataset(csv_file, dataset_directory, start_column):
    if not os.path.exists(dataset_directory):
        # Fake a browser session to avoid 403 errors
        with open(csv_file, 'r') as articles_file:            
            os.mkdir(dataset_directory)
            links_and_ratings = [(row[start_column], row[start_column+1]) for row in csv.reader(articles_file, delimiter=',', quotechar='"')]
            links_ratings_content = parallel_requests(links_and_ratings)

        for i, (link, rating, webpage) in enumerate(links_ratings_content):
            article_dir = f'{dataset_directory}/{i}/'
            if not os.path.exists(article_dir):
                os.mkdir(article_dir)
            open(article_dir + 'webpage', 'wb').write(webpage)
            open(article_dir + 'link', 'w').write(link)
            open(article_dir + 'rating', 'w').write(rating)

    if not os.path.exists(f'{dataset_directory}.json'):
        articles_info = []
        error_regex = re.compile('^(Are you a robot)|(ERROR)|(403)|(Page Not Found)|(Access Denied)(Site Not Configured).*')
        for article_dir in sorted(glob(f'{dataset_directory}/*/')):
            article = Article(url=open(article_dir + 'link').read())
            article.download(input_html=open(article_dir + 'webpage').read())
            article.parse()
            article.nlp()
            if error_regex.match(article.title):
                continue

            article_json = {'title' : article.title,
                            'rating': float(open(article_dir + 'rating').read().strip()),
                            'link': open(article_dir + 'link').read(),
                            'text' : article.text, 
                            'authors': article.authors,
                            'summary': article.summary,
                            'keywords': list(article.keywords),
                            'tags': list(article.tags)}
            print(article.title)
            if article.title == '':
                print(f'  {article.text}')
            articles_info.append(article_json)
            with open(article_dir + 'title', 'w') as file:
                file.write(article.title)
            with open(article_dir + 'text', 'w') as file:
                file.write(article.text)
            with open(article_dir + 'authors', 'w') as file:
                for author in article.authors:
                    file.write(f'{author}\n')
            with open(article_dir + 'summary', 'w') as file:
                file.write(article.summary)
            with open(article_dir + 'keywords', 'w') as file:
                for keyword in article.keywords:
                    file.write(f'{keyword}\n')
            with open(article_dir + 'tags', 'w') as file:
                for tag in article.tags:
                    file.write(f'{tag}\n')
        json.dump(articles_info, indent=4, sort_keys=True, fp=open(f'{dataset_directory}.json', 'w'))
    articles_info_json = json.load(open(f'{dataset_directory}.json', 'r'))
    left, right = 0,0
    for article in articles_info_json:
        if article['rating'] < 0:
            left += 1    
        else:
            right += 1

    print(f'left={left}')
    print(f'right={right}')

def parallel_requests(urls_and_ratings):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(parallel_requests_async(urls_and_ratings))

async def parallel_requests_async(urls_and_ratings):
    headers = {'user-agent' : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36'}
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:

        def __get_request(i, url, rating):
            try:
                print(f'{i} {url}')
                return url, rating, requests.get(url, timeout=20, headers=headers)
            except Exception as e:
                print(e)
                print('Timed out retrieving ' + url)
            return None

        loop = asyncio.get_event_loop()
        futures = [
            loop.run_in_executor(
                executor, 
                __get_request,
                i,
                url,
                rating)
            for i, (url, rating) in enumerate(urls_and_ratings)
        ]
        return [(response[0], response[1], response[2].content) \
                 for response in await asyncio.gather(*futures) if response != None]


if __name__ == "__main__":
    main()

