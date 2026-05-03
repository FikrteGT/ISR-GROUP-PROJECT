from __future__ import division
import string
from stemming.porter2 import stem
from string import digits
import re
import time
from collections import OrderedDict
import dill

#To store the term_freq and positions of the term
class TermVector:
    def __init__(self, tf, pos):
        self.tf = tf
        self.pos = pos

    def getTF(self):
        return self.tf

    def getPos(self):
        return self.pos

def unpickler(file):
    f = open(file, 'rb')
    ds = dill.load(f)
    f.close()
    return ds

def parseCatalog(file):
    catalog = {}
    catalogFile = open(file, 'r')
    for line in catalogFile.readlines():
        content = line.strip().split(',')
        catalog[content[0]] = content[1:]
    return catalog

def queryMaker():
    queries = []
    with open('Files/query.text', 'r') as f:
        current_query = []
        for line in f:
            line = line.strip()
            if line.startswith('.I'):
                if current_query:
                    queries.append(' '.join(current_query))
                    current_query = []
            elif line.startswith('.W'):
                pass  # start collecting query text
            elif line and not line.startswith('.'):
                current_query.append(line)
        if current_query:
            queries.append(' '.join(current_query))
    return queries

def queryProcessor(query):
    with open("Files/common_words") as sfile:
        stopWords = sfile.readlines()
    stopWords = filter(None, stopWords)
    keywords = ""
    flag = 0
    for word in query.split():
        for sWord in stopWords:
            if (word == sWord.strip()):
                flag = 1
                break
        if (flag != 1):
            keywords += word + " "
        flag = 0
    keywords = keywords.translate(str.maketrans('', '', string.punctuation))
    return keywords.strip()

def getInfo(key, catalog, termMap, docMap):
    keyInfo = OrderedDict()
    invList = OrderedDict()
    docDict = OrderedDict()
    termid = termMap.get(key)
    if termid is None:
        return invList, keyInfo
    indexFile = open("Files/Unstemmed/invertedFile0.txt", 'r')
    offset = catalog.get(str(termid))[0]
    indexFile.seek(int(offset))
    line = indexFile.readline()
    df = line.split(':')[0].split(',')[1]
    ttf = line.split(':')[0].split(',')[2]
    keyInfo[key] = [df, ttf]
    remStr = line.split(':')[1].split(';')
    for item in remStr:
        docno = item.split(',')[0]
        docID = docMap.get(int(docno))
        tf = int(item.split(',')[1])
        pos = [int(e) for e in item.split(',')[2:len(item.split(','))]]
        docDict[docID] = TermVector(tf, pos)
    invList[key] = docDict
    indexFile.close()
    return invList, keyInfo

def getParameters(query, qNo):
    keywords = queryProcessor(query)
    termVector = OrderedDict()
    termStats = OrderedDict()
    for key in keywords.split():
        key = key.lower()
        invList, keyInfo= getInfo(key, catalog, termMap, docMap)
        termVector.update(invList)
        termStats.update(keyInfo)
    f = open('Files/Unstemmed/Pickles/termStats%s.p' % qNo, 'wb')
    dill.dump(termStats, f)
    f.close()
    f = open('Files/Unstemmed/Pickles/termVector%s.p' % qNo, 'wb')
    dill.dump(termVector, f)
    f.close()

start_time = time.time()
docInfo = unpickler('Files/Unstemmed/Pickles/docInfo.p')
catalog = parseCatalog('Files/Unstemmed/catalogFile.txt')
termMap = unpickler('Files/Unstemmed/Pickles/termMap.p')
docMap = unpickler('Files/Unstemmed/Pickles/docMap.p')
# getInfo('govern', catalog, termMap, docMap)
queries = queryMaker()
qNo = 0
for query in queries:
    qNo += 1
    getParameters(query, qNo)
    print("Created %d termVector" % qNo)
temp = time.time() - start_time
print(temp)
hours = temp // 3600
temp = temp - 3600 * hours
minutes = temp // 60
seconds = temp - 60 * minutes
print('%d:%d:%d' % (hours, minutes, seconds))
