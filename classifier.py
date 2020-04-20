from sklearn import datasets, svm
from sklearn.preprocessing import MaxAbsScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, \
    confusion_matrix, classification_report
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.multiclass import OneVsRestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, BaggingClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.exceptions import ConvergenceWarning
from numpy import mean
import warnings
import pickle


def get_left_right_classifier():
    X, y = datasets.load_svmlight_file(open('train_features_file.txt', 'rb'))

    # Preprocess data
    X = MaxAbsScaler().fit(X).transform(X)
    y = [1 if val > 0 else -1 for val in y]

    num_iterations = 10
    best_model, best_accuracy = None, None
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1)

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=ConvergenceWarning)
        model = LogisticRegression(solver='saga')
        accuracy = mean(cross_val_score(model, X_train, y_train, cv=5))
        print(f'Mean cross validation accuracy={accuracy}')

        model.fit(X_train, y_train)
        y_predictions = model.predict(X_test)

        print(f'Model test accuracy_score={accuracy_score(y_test, y_predictions)}')


if __name__ == '__main__':
    get_left_right_classifier()





