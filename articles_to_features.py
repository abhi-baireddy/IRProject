import spacy
from textblob import TextBlob, WordList
from textblob.tokenizers import SentenceTokenizer
import json
import os

from collections import Counter

def main():
    feature_mappings = get_feature_mappings()
    with open('features_file.txt', 'w') as feature_file:
        for i, article in enumerate(get_articles()):
            print(f'{i} {article["title"]} vectorizing...')
            feature_file.write(vectorize(feature_mappings, article['title'] + '\n' + article['text'], article['rating']) + '\n')
    
def get_articles():
    return json.load(open('classifier_test_articles.json'))

def get_feature_mappings():
    feature_mapping_path = 'feature_mappings.json'
    if not os.path.exists(feature_mapping_path):
        all_keywords = set()
        for i, article in enumerate(get_articles()):
            print(f'{i} {article["title"]}')
            all_keywords |= set(WordList(article['keywords']).lemmatize().upper())
        feature_mappings = {word : i for i, word in enumerate(all_keywords)}
        json.dump(feature_mappings, open(feature_mapping_path, 'w'))
    else:
        feature_mappings = json.load(open(feature_mapping_path, 'r'))
    return feature_mappings
    
def vectorize(feature_mappings, article_text, rating):
    textblob = TextBlob(article_text)
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


    vector_string = str(rating)
    for feature_i, count in sorted(feature_counter.items()):
        vector_string += f' {feature_i}:{count}'
    return vector_string
    





if __name__ == '__main__':
    main()