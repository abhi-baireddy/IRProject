import spacy
from textblob import TextBlob, WordList
from textblob.tokenizers import SentenceTokenizer
import json
import nltk
import os
import pickle

from collections import Counter

def main():
    articles = json.load(open('classifier_test_articles.json'))
    feature_mappings = get_feature_mappings(articles)
    with open('features_file.txt', 'w') as feature_file:
        for i, article in enumerate(articles):
            print(f'{i} {article["title"]} vectorizing...')
            feature_file.write(vectorize(feature_mappings, article) + '\n')


def get_feature_mappings(articles):
    all_keywords = set()
    for i, article in enumerate(articles):
        print(f'{i} {article["title"]}')
        all_keywords |= set(WordList(article['keywords']).lemmatize().upper())
    return {word : i for i, word in enumerate(all_keywords)}
    
def vectorize(feature_mappings, article):
    textblob = TextBlob(article['title'] + '\n' + article['text'])
    keywords_in_doc = set(word for word in textblob.words.lemmatize().upper() if word in feature_mappings)
    feature_counter = Counter(feature_mappings[word] for word in keywords_in_doc)
    
    num_sentences_with_word = Counter()
    for sentence in textblob.sentences:
        for word in sentence.words.lemmatize().upper():
            if word in keywords_in_doc:
                num_sentences_with_word[word] += 1
                feature_counter[len(feature_mappings) + feature_mappings[word]] += sentence.polarity
                feature_counter[2*len(feature_mappings) + feature_mappings[word]] += sentence.subjectivity
    
    for word, n in num_sentences_with_word.items():
        feature_counter[len(feature_mappings) + feature_mappings[word]] /= n
        feature_counter[2*len(feature_mappings) + feature_mappings[word]] /= n


    vector_string = f'{article["rating"]}'
    for feature_i, count in sorted(feature_counter.items()):
        vector_string += f' {feature_i}:{count}'
    return vector_string
    





if __name__ == '__main__':
    main()