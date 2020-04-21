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

    # Preprocess
    extreme_threshold = 16
    center_threshold = 8
    def discretize(val):
        if val < -extreme_threshold:
            return -2
        elif val < -center_threshold:
            return -1
        elif val < center_threshold:
            return 0
        elif val < extreme_threshold:
            return 1
        else:
            return 2
    
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
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1)

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=ConvergenceWarning)
        model = load_model()
        model.fit(X_train, y_train)
    y_predictions = model.predict(X_test)

    print(f'Model test accuracy_score={accuracy_score(y_test, y_predictions)}')
    print(classification_report(y_test, y_predictions, target_names=['left','lean left', 'center', 'lean right', 'right']))
    
    conf_matrix = confusion_matrix(y_test, y_predictions)
    print('Confusion Matrix')
    print(conf_matrix)
    print(f'  Left marked as right = {(sum(conf_matrix[0][3:]) + sum(conf_matrix[1][3:]))/(sum(conf_matrix[0]) + sum(conf_matrix[1]))}')
    print(f'  Right marked as left = {(sum(conf_matrix[3][:2]) + sum(conf_matrix[4][:2]))/(sum(conf_matrix[3]) + sum(conf_matrix[4]))}')
    