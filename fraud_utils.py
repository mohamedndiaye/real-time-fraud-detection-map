# -*- coding: utf-8 -*-
"""
Created on Mon Jul 22 18:29:52 2019

@author: Lambert Rosique
@source : https://github.com/miguelgfierro/sciblog_support/tree/master/Intro_to_Fraud_Detection
"""
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, accuracy_score, roc_auc_score, f1_score, log_loss, precision_score, recall_score
import numpy as np
import itertools
import matplotlib.pyplot as plt
import pandas as pd
import time
import random
import requests

# Constants
URL_API = 'http://localhost:5000'
BASELINE_MODEL = 'save/lgb.model'
FRAUD_THRESHOLD = 0.5

''' Variables '''
dataset_creditcard = 'data/creditcard.csv'
dataset_worldcities = 'data/worldcities.csv'

''' Import des données '''
# Dataset des fraudes
data_creditcard = pd.read_csv(dataset_creditcard)
# Dataset des positions géographiques des villes (pour le rendu final)
data_cities = pd.read_csv(dataset_worldcities, usecols=['city_ascii', 'country', 'lat', 'lng'])
data_cities = data_cities.rename(columns={'city_ascii': 'city', 'lat': 'latitude', 'lng': 'longitude'})

def select_random_row_cities():
    global data_cities
    return data_cities.sample(n=1)

def select_random_row_creditcard():
    global data_creditcard
    return data_creditcard.sample(n=1)

def split_train_test(X, y, test_size=0.2):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y)
    return X_train, X_test, y_train, y_test


def classification_metrics_binary(y_true, y_pred):
    """Returns a report with different metrics for a binary classification problem.
    - Accuracy: Number of correct predictions made as a ratio of all predictions. Useful when there are equal number
    of observations in each class and all predictions and prediction errors are equally important.
    - Confusion matrix: C_ij where observations are known to be in group i but predicted to be in group j. In binary
    classification true negatives is C_00, false negatives is C_10, true positives is C_11 and false positives is C_01.
    - Precision: Number of true positives divided by the number of true and false positives. It is the ability of the
    classifier not to label as positive a sample that is negative.
    - Recall: Number of true positives divided by the number of true positives and false negatives. It is the ability
    of the classifier to find all the positive samples.
    High Precision and low Recall will return few positive results but most of them will be correct. 
    High Recall and low Precision will return many positive results but most of them will be incorrect.
    - F1 Score: 2*((precision*recall)/(precision+recall)). It measures the balance between precision and recall.
    Args:
        y_true (list or np.array): True labels.
        y_pred (list or np.array): Predicted labels (binary).
    Returns:
        report (dict): Dictionary with metrics.
    Examples:
        >>> from collections import OrderedDict
        >>> y_true = [0,1,0,0,1]
        >>> y_pred = [0,1,0,1,1]
        >>> result = classification_metrics_binary(y_true, y_pred)
        >>> OrderedDict(sorted(result.items()))
        OrderedDict([('Accuracy', 0.8), ('Confusion Matrix', array([[2, 1],
               [0, 2]])), ('F1', 0.8), ('Precision', 0.6666666666666666), ('Recall', 1.0)])
    """
    m_acc = accuracy_score(y_true, y_pred)
    m_f1 = f1_score(y_true, y_pred)
    m_precision = precision_score(y_true, y_pred)
    m_recall = recall_score(y_true, y_pred)
    m_conf = confusion_matrix(y_true, y_pred)
    report = {'Accuracy': m_acc, 'Precision': m_precision,
              'Recall': m_recall, 'F1': m_f1, 'Confusion Matrix': m_conf}
    return report


def classification_metrics_binary_prob(y_true, y_prob):
    """Returns a report with different metrics for a binary classification problem.
    - AUC: The Area Under the Curve represents the ability to discriminate between positive and negative classes. An
    area of 1 represent perfect scoring and an area of 0.5 means random guessing.
    - Log loss: Also called logistic regression loss or cross-entropy loss. It quantifies the performance by
    penalizing false classifications. Minimizing the Log Loss is equivalent to minimizing the squared error but using
    probabilistic predictions. Log loss penalize heavily classifiers that are confident about incorrect classifications.
    Args:
        y_true (list or np.array): True labels.
        y_prob (list or np.array): Predicted labels (probability).
    Returns:
        report (dict): Dictionary with metrics.
    Examples:
        >>> from collections import OrderedDict
        >>> y_true = [0,1,0,0,1]
        >>> y_prob = [0.2,0.7,0.4,0.3,0.2]
        >>> result = classification_metrics_binary_prob(y_true, y_prob)
        >>> OrderedDict(sorted(result.items()))
        OrderedDict([('AUC', 0.5833333333333333), ('Log loss', 0.6113513950783531)])
        >>> y_prob = [0.2,0.7,0.4,0.3,0.3]
        >>> result = classification_metrics_binary_prob(y_true, y_prob)
        >>> OrderedDict(sorted(result.items()))
        OrderedDict([('AUC', 0.75), ('Log loss', 0.5302583734567203)])
    """
    m_auc = roc_auc_score(y_true, y_prob)
    m_logloss = log_loss(y_true, y_prob)
    report = {'AUC': m_auc, 'Log loss': m_logloss}
    return report


def binarize_prediction(y, threshold=0.5):
    """Binarize prediction based on a threshold
    Args:
        y (np.array): Array with predictions.
        threshold (float): Theshold value for binarization.
    """
    y_pred = np.where(y > threshold, 1, 0)
    return y_pred


def plot_confusion_matrix(cm, classes, normalize=False, title='Confusion matrix', cmap=plt.cm.Blues):
    """Plots a confusion matrix.
    Args:
        cm (np.array): The confusion matrix array.
        classes (list): List wit the classes names.
        normalize (bool): Flag to normalize data.
        title (str): Title of the plot.
        cmap (matplotlib.cm): Matplotlib colormap https://matplotlib.org/api/cm_api.html
    Examples:
        >>> import numpy as np
        >>> a = np.array([[10, 3, 0],[1, 2, 3],[1, 5, 9]])
        >>> classes = ['cl1', 'cl2', 'cl3']
        >>> plot_confusion_matrix(a, classes, normalize=False)
        >>> plot_confusion_matrix(a, classes, normalize=True)

    """
    cm_max = cm.max()
    cm_min = cm.min()
    if cm_min > 0:
        cm_min = 0
    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        cm_max = 1
    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=45)
    plt.yticks(tick_marks, classes)
    thresh = cm_max / 2.
    plt.clim(cm_min, cm_max)

    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i,
                 round(cm[i, j], 3),  # round to 3 decimals if they are float
                 horizontalalignment="center",
                 color="white" if cm[i, j] > thresh else "black")
    plt.ylabel('True label')
    plt.xlabel('Predicted label')
    plt.show()

def wait_random_time(minwait,maxwait):
    r = random.randint(minwait*100,maxwait*100)
    time.sleep(r/100)
    
def test_server_online():
    try:
        requests.get(URL_API)
        return True
    except:
        return False