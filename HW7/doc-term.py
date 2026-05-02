
from elasticsearch_dsl import query, Search
from elasticsearch import Elasticsearch
import csv
import os
from string import digits
import string
from enchant.tokenize import get_tokenizer
import numpy
import enchant
from bs4 import BeautifulSoup
import dill
import time
import pandas
import numpy as np
from sklearn.feature_extraction.text import CountVectorizerk
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn import linear_model
from sklearn import model_selection

# FIXED OLD IMPORT
from sklearn.impute import SimpleImputer

from sklearn.metrics import accuracy_score
from sklearn import preprocessing
from operator import itemgetter
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.naive_bayes import GaussianNB
from collections import OrderedDict
import nltk
es = Elasticsearch(
    "https://localhost:9200",
    basic_auth=("elastic", "=n_K04+d1hF7948K80o*"),
    verify_certs=False
)

# nltk.download("words")
words = set(nltk.corpus.words.words())

textList = []
labelList = []
docIDList = []

d = enchant.Dict("en_US")


def getText(path):
    for filename in os.listdir(path):
        if filename != '.DS_Store':
            print(filename)

            file = open(path + filename, "r", encoding="ISO-8859-1")
            page = file.read()
            file.close()

            validPage = "<root>" + page + "</root>"
            soup = BeautifulSoup(validPage, "html.parser")

            label = soup.label.get_text()
            docID = soup.emailid.get_text()

            texts = soup.find_all("text")

            text = ""
            for txt in texts:
                text += txt.get_text().strip()

            english_text = " ".join(
                w for w in nltk.wordpunct_tokenize(text)
                if w.lower() in words or not w.isalpha()
            )

            textList.append(english_text)
            labelList.append(label)
            docIDList.append(docID)


def main():

    stoplist = open("stoplist.txt", "r", encoding="utf-8")
    stopwords = []

    for word in stoplist.readlines():
        stopwords.append(word.strip())

    stoplist.close()

    f = open("textListSpam.p", "rb")
    textList = dill.load(f)
    f.close()

    f = open("LabelList.p", "rb")
    LabelList = dill.load(f)
    f.close()

    f = open("docIDList.p", "rb")
    docIDList = dill.load(f)
    f.close()

    Y = numpy.array(LabelList)
    dID = numpy.array(docIDList)

    vectorizer = CountVectorizer(stop_words=stopwords)
    sparseMatrix = vectorizer.fit_transform(textList)

    kfold = model_selection.KFold(
        n_splits=5,
        random_state=None,
        shuffle=False
    )

    train, test = next(kfold.split(sparseMatrix, Y))

    docIDTest = dID[test]

    le = preprocessing.LabelEncoder()
    Y = le.fit_transform(Y)

    print(Y)

    regr = linear_model.LogisticRegression(max_iter=1000)

    regr.fit(sparseMatrix[train], Y[train])

    predictions = regr.predict(sparseMatrix[test])

    print("Accuracy:", accuracy_score(Y[test], predictions) * 100)


main()