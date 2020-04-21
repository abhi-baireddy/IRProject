from left_right_classifier import Left_right_classifier
from articles_to_features import vectorize, get_feature_mappings
from sklearn import datasets
import json
import asyncio
import concurrent.futures
import os
import numpy as np
from collections import Counter
import matplotlib.pyplot as plt
from matplotlib.offsetbox import AnchoredText
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import difflib

def main():
    create_level_vector_files()


def create_level_vector_files():
    articles = json.load(open('classifier_train_articles.json', 'r'))
    
    if not os.path.exists('site_scores.txt'):
        def discretize(val):
            if val <= -2:
                return -1
            elif val < 2:
                return 0
            else:
                return 1

        classifier = Left_right_classifier()

        site_scores = Counter()
        all_sides_scores = {}
        num_articles_per_source = Counter()
        level_weight = 1
        predictions = parallel_classifier(articles)
        for article, prediction in zip(articles, predictions):
            site_scores[article['source']] += (1/(article['level']+1))*prediction
            num_articles_per_source[article['source']] += 1
            all_sides_scores[article['source']] = article['rating']
        for key in num_articles_per_source.keys():
            site_scores[key] /= num_articles_per_source[key]
        json.dump(dict(site_scores), open('site_scores.txt', 'w'), indent=4)
        json.dump(dict(all_sides_scores), open('all_sides_scores.txt', 'w'), indent=4)
    else:
        site_scores = json.load(open('site_scores.txt', 'r'))
        all_sides_scores = json.load(open('all_sides_scores.txt', 'r'))
        
    y_pred, y_all_sides = zip(*[(site_scores[key], all_sides_scores[key]) for key in site_scores.keys()])
    y_pred = [val/(.5*max(y_pred)) if val > 0 else val/(-.5*min(y_pred)) for val in y_pred]

    regression = LinearRegression()
    regression.fit(np.array(y_pred).reshape(-1,1), np.array(y_all_sides).reshape(-1,1))
    y_regress = [regression.intercept_[0] + regression.coef_[0]*x for x in y_pred]
    
    r2 = r2_score(y_all_sides, y_pred)

    site_rankings = [key for key,_ in sorted(site_scores.items(), key=lambda x: x[1])]
    all_sides_rankings = [key for key,_ in sorted(zip(site_rankings, [all_sides_scores[site] for site in site_rankings]), key=lambda x: x[1])]
    
    print(site_rankings)
    print(all_sides_rankings)

    print(f'Similarity of rankings={difflib.SequenceMatcher(None, site_rankings, all_sides_rankings).ratio()}')
    fig, ax = plt.subplots()

    plt.title('Calculated Score vs. AllSides Score')
    plt.ylabel('AllSides Score')
    plt.xlabel('Normalized Calculated Score')
    ax.scatter(y_pred, y_all_sides,  color='blue')
    text_box = AnchoredText(f'r={np.sqrt(r2):.2f}, r2={r2:.2f}', frameon=True, loc=4, pad=0.5)
    plt.setp(text_box.patch, facecolor='white', alpha=0.5)
    ax.add_artist(text_box)

    plt.plot(y_pred, y_regress, color='red')
    plt.show()
    


def parallel_classifier(articles):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(parallel_classifier_async(articles))

async def parallel_classifier_async(articles):
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:

        def __classify(i, article):
            prediction = Left_right_classifier().classify_article(article['text'])
            print(f'{i} {article["source"]} {article["level"]} {prediction}')
            return prediction

        loop = asyncio.get_event_loop()
        futures = [
            loop.run_in_executor(
                executor, 
                __classify, i, article)
            for i, article in enumerate(articles)
        ]
        return [prediction for prediction in await asyncio.gather(*futures)]

if __name__ == '__main__':
    main()