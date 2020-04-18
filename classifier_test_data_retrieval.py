import requests
import csv
from bs4 import BeautifulSoup
from newspaper import Article, fulltext
import re
import os
from glob import glob
import json

def main():
    allsides_article_links_path = 'allsides_article_links.txt'
    if not os.path.exists(allsides_article_links_path):
        topics_urls = get_topic_links()
        article_links = []
        for topic_url in topics_urls:
            print(topic_url)
            article_links += get_allsides_article_links(topic_url)
        with open(allsides_article_links_path, 'w') as articles_file:
            for link in set(article_links):
                articles_file.write(f'{link}\n')
    
    news_articles_and_ratings_path = 'articles_and_ratings.csv'
    if not os.path.exists(news_articles_and_ratings_path):
        articles_and_ratings = None
        with open(allsides_article_links_path, 'r') as articles_file:
            articles_and_ratings = [get_original_link_and_rating(allsides_link) \
                                    for allsides_link in set(articles_file.read().splitlines())]
                                    
        
        with open(news_articles_and_ratings_path, 'w') as link_and_rating_file:
            for link, rating in set(articles_and_ratings):
                if link != None and rating != None:
                    link_and_rating_file.write(f'"{link}",{rating}\n')
    
    if not os.path.exists('classifier_test_articles/'):
        with open(news_articles_and_ratings_path, 'r') as articles_file:
            os.mkdir('classifier_test_articles/')
            link_rating_content = []
            for i, (link, rating) in enumerate(csv.reader(articles_file, delimiter=',', quotechar='"')):
                try:
                    print(i, link)
                    webpage = requests.get(link, timeout=20).content
                    link_rating_content.append((link, rating, webpage))
                except:
                    print('Request timed out! Skipping...')
        for i, (link, rating, webpage) in enumerate(link_rating_content):
            article_dir = f'classifier_test_articles/{i}/'
            if not os.path.exists(article_dir):
                os.mkdir(article_dir)
            open(article_dir + 'webpage', 'wb').write(webpage)
            open(article_dir + 'link', 'w').write(link)
            open(article_dir + 'rating', 'w').write(rating)

    if not os.path.exists('classifier_test_articles.json'):
        articles_info = []
        for article_dir in sorted(glob('classifier_test_articles/*/')):
            article = Article(url=open(article_dir + 'link').read())
            article.download(input_html=open(article_dir + 'webpage').read())
            article.parse()
            article.nlp()
            article_json = {'rating': int(open(article_dir + 'rating').read().strip()),
                            'link': open(article_dir + 'link').read(),
                            'text' : article.text, 
                            'authors': article.authors,
                            'summary': article.summary,
                            'keywords': list(article.keywords),
                            'tags': list(article.tags)}
            print(article.summary)
            articles_info.append(article_json)

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
        json.dump(articles_info, indent=4, sort_keys=True, fp=open('classifier_test_articles.json', 'w'))
    articles_info_json = json.load(open('classifier_test_articles.json', 'r'))
    left, center, right = 0,0,0
    for article in articles_info_json:
        if article['rating'] < 0:
            left += 1    
        elif article['rating'] == 0:
            center += 1
        else:
            right += 1

    print(f'left={left}')
    print(f'center={center}')
    print(f'right={right}')



def get_topic_links():
    topics_page = requests.get('https://www.allsides.com/topics-issues')
    soup = BeautifulSoup(topics_page.content, 'html.parser')
    urls = [a.get('href') for a in soup.find_all('a')]

    topics_url_regex = re.compile('^topics/.*')
    topics_urls = [f'https://www.allsides.com/{url}' for url in urls if topics_url_regex.match(str(url))]
    return topics_urls

def get_allsides_article_links(topic_url):
    topic_page = requests.get(topic_url)
    soup = BeautifulSoup(topic_page.content, 'html.parser')
    
    content_wrappers = soup.find('div', {'class': 'region-triptych-left'}).find_all('div',{'class': 'top-content-wrapper'})
    content_wrappers += soup.find('div', {'class': 'region-triptych-center'}).find_all('div',{'class': 'top-content-wrapper'})
    content_wrappers += soup.find('div', {'class': 'region-triptych-right'}).find_all('div',{'class': 'top-content-wrapper'})

    return [wrapper.find('a').get('href') for wrapper in content_wrappers]

ratings_map = {
    'Left' : -2,
    'Lean Left' : -1,
    'Center' : 0,
    'Lean Right' : 1,
    'Right' : 2
}
def get_original_link_and_rating(allsides_link):
    print(allsides_link)
    try:
        soup = BeautifulSoup(requests.get(allsides_link).content, 'html.parser')
        rating_text = soup.find('div', {'class' : 'article-media-bias-'}).find('a').getText()
        original_link = soup.find('div', {'class' : 'read-more-story'}).find('a').get('href')
        print(f'  {rating_text}')
        print(f'  {(original_link, ratings_map[rating_text])}')
        return original_link, ratings_map[rating_text]
    except:
        print('Exception occurred! Skipping...')
    return None, None


if __name__ == "__main__":
    main()

