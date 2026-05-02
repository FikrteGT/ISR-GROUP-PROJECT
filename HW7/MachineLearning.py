import numpy as np
import pandas as pd
from sklearn import linear_model, model_selection, preprocessing
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score
from sklearn.feature_selection import SelectKBest, f_classif
import csv
from collections import OrderedDict
from operator import itemgetter
from sklearn.linear_model import LogisticRegression

regr = LogisticRegression(max_iter=5000)

def createDict(dIDTest, probabilities, labels):
    probabilitiesList = list(probabilities)
    testDict = OrderedDict()

    sortedProbabilities = sorted(probabilitiesList)

    for i, prob in enumerate(sortedProbabilities):
        idx = probabilitiesList.index(prob)

        docID = dIDTest[idx][0]
        label = labels[idx]

        testDict[docID] = [(label, prob)]

    return testDict


def getNGrams(file):
    colNames = []
    with open(file, "r", encoding="utf-8") as f:
        for line in f:
            colNames.append(line.strip())
    return colNames


def getBestFeatures(X, y, csvFile, names):
    selector = SelectKBest(f_classif, k=min(10, X.shape[1]))
    selector.fit(X, y)

    selected_names = np.array(names[:-1])[selector.get_support()]
    scores = selector.scores_[selector.get_support()]

    df = pd.DataFrame({
        "Feature": selected_names,
        "Score": scores
    }).sort_values(by="Score", ascending=False)

    print("\nTop Features:")
    print(df)


def getAccuracy(txtFile, csvFile):
    names = getNGrams(txtFile)

    dataset = pd.read_csv(csvFile)
    dataset = dataset.fillna(0)

    array = dataset.values

    X = array[:, 0:len(names)-1]
    Y = array[:, len(names)-1]

    le = preprocessing.LabelEncoder()
    Y = le.fit_transform(Y)

    imputer = SimpleImputer(strategy="mean")
    X = imputer.fit_transform(X)

    # split data
    kfold = model_selection.KFold(n_splits=5, shuffle=True, random_state=42)
    train, test = next(kfold.split(X, Y))

    X_train, X_test = X[train], X[test]
    Y_train, Y_test = Y[train], Y[test]

    docIDTest = np.arange(len(Y_test))  # fallback IDs if none exist

    model = LogisticRegression(max_iter=5000)
    model.fit(X_train, Y_train)

    predictions = model.predict(X_test)

    probabilities = model.predict_proba(X_test)[:, 1]

    # ---------------- ACCURACY ----------------
    acc = accuracy_score(Y_test, predictions) * 100
    print("\nAccuracy:", acc)

    # save results.txt
    with open("results.txt", "w") as f:
        f.write(str(acc))

    # ---------------- RANKING FILE ----------------
    testDict = createDict(
        [[i] for i in docIDTest],
        probabilities,
        Y_test
    )

    testDict = sortDict(testDict)
    createPerformanceFile(testDict)

    # ---------------- FEATURE IMPORTANCE ----------------
    getBestFeatures(X, Y, csvFile, names)

    # ---------------- FINAL EVALUATION ----------------
    print("\n================ FINAL EVALUATION ================")
    print("Accuracy:", acc)
    print("Training size:", len(X_train))
    print("Test size:", len(X_test))
    print("Features:", X.shape[1])
    print("Ranking file: Ranking.csv generated")
    print("Results file: results.txt generated")
    print("==================================================\n")

def main():
    getAccuracy('scratch.txt', 'staticFeatureMatrixFull200.csv')


if __name__ == "__main__":
    main()