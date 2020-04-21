from sklearn import datasets
from sklearn.preprocessing import MaxAbsScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.exceptions import ConvergenceWarning
from numpy import mean, array
from articles_to_features import vectorize, get_feature_mappings
from newspaper import Article
import warnings
import pickle
import io
import os
import requests


def load_training_data():
    X, y = datasets.load_svmlight_file(open('features_file.txt', 'rb'))
    true_center = mean(y)
    # Preprocess
    left_threshold = 7.5
    right_threshold = 7.5
    def discretize(val):
        if val < -left_threshold:
            return -1
        elif val < right_threshold:
            return 0
        else:
            return 1
    
    return MaxAbsScaler().fit(X).transform(X), [discretize(val) for val in y]

def load_test_data():
    X, y = datasets.load_svmlight_file(open('allsides_vectors.txt', 'rb'))

    # Preprocess
    def discretize(val):
        if val <= -2:
            return -1
        elif val < 2:
            return 0
        else:
            return 1
    
    return MaxAbsScaler().fit(X).transform(X), [discretize(val) for val in y]

def load_model():
    return LogisticRegression(solver='saga', random_state=0)  

def load_trained_model():
    if not os.path.exists('left_right_model.pkl'):
        X, y = load_training_data()
        model = load_model()
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ConvergenceWarning)
            model.fit(X, y)
        pickle.dump(model, open('left_right_model.pkl', 'wb'))
    else:
        model = pickle.load(open('left_right_model.pkl', 'rb'))
    return model

class Left_right_classifier(object):
    def __init__(self):
        self.__model = load_trained_model()

    def classify_article_from_url(self, x_article_url):
        return self.classify_html_article(requests.get(x_article_url).content)

    def classify_html_article(self, x_article_html):
        article = Article(url='')
        article.download(input_html=x_article_html)
        article.parse()
        return self.classify_article(article.text, article.title)

    def classify_article(self, x_article_text, x_article_title=''):
        vectorized = vectorize(get_feature_mappings(), x_article_title + '\n' + x_article_text, 0)
        return self.classify_vectorized_article(vectorized)

    def classify_vectorized_article(self, x_vec):
        if isinstance(x_vec, str):
            x_vec, _ = datasets.load_svmlight_file(io.BytesIO(x_vec.encode()), n_features=len(self.__model.coef_[0]))
        return self.__model.predict(x_vec)[0]

if __name__ == '__main__':
    X, y = load_training_data()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=0)

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=ConvergenceWarning)
        model = load_model()
        model.fit(X_train, y_train)
    y_predictions = model.predict(X_test)

    print(f'Model test accuracy_score={accuracy_score(y_test, y_predictions)}')
    print(classification_report(y_test, y_predictions, target_names=['left', 'center', 'right']))
    
    conf_matrix = confusion_matrix(y_test, y_predictions)
    print('Confusion Matrix')
    print(conf_matrix)

    print(f'  Left marked as right = {conf_matrix[0][2]/sum(conf_matrix[0])}')
    print(f'  Right marked as left = {conf_matrix[2][0]/sum(conf_matrix[2])}')
    print()
    print(f'  Center marked as right = {conf_matrix[1][2]/sum(conf_matrix[1])}')
    print(f'  Center marked as left = {conf_matrix[1][0]/sum(conf_matrix[1])}')
    
    print()
    classifier = Left_right_classifier()
    print(classifier.classify_article_from_url('https://www.vox.com/2020/4/20/21225016/protests-stay-at-home-orders-trump-conservative-group-michigan'))
    print(classifier.classify_article_from_url('https://www.cnn.com/2020/04/20/politics/aoc-2022-senate-schumer/index.html'))
    print(classifier.classify_article_from_url('https://www.vox.com/covid-19-coronavirus-us-response-trump/2020/4/19/21227175/coronavirus-trump-who-information-china-embeds-december'))
    print(classifier.classify_article_from_url('https://www.vice.com/en_us/article/4agzpn/texas-anti-lockdown-protesters-are-coming-for-fauci-now'))

    print(classifier.classify_article_from_url('https://www.infowars.com/trump-to-press-you-and-the-obama-administration-were-duped-for-years-by-china/'))
    print(classifier.classify_article_from_url('https://www.dailywire.com/news/poll-people-have-no-idea-joe-biden-is-talking-about-coronavirus'))
    print(classifier.classify_article_from_url('https://www.louderwithcrowder.com/opinion-sorry-democrats-its-not-the-republicans-who-are-nazis/'))
    print(classifier.classify_article_from_url('https://dailycaller.com/2020/04/20/alexandria-ocasio-cortez-oil-drop-tweet-lost-jobs/'))