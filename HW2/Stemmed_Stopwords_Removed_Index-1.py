from stemming.porter2 import stem
import time
from bs4 import BeautifulSoup
import os
import re
import regex
from collections import defaultdict
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

#To store the terms, termMaps(termid to term), file names of files that contain the term, with offset and length
class Catalog:
    def __init__(self):
        self.terms = {}
        self.termMap = {}
    def addTerm(self, term, offset, length, fileName, termid):
        if term not in self.terms:
            self.terms[term] = {}
            self.termMap[term] = termid
        self.terms[term][fileName] = CatalogTerm(term, offset, length)

    def removeTerm(self, term):
        del self.terms[term]
        del self.termMap[term]

#To store the term, its offset in file and the length of the block.
class CatalogTerm:
    def __init__(self, term, offset, length):
        self.term = term
        self.offset = offset
        self.length = length

#To get the tokens from a given text
def tokenizer(text):
    posToken = []
    i = 0
    tokens = re.split(r"[^\w\.]*", text)
    for token in tokens:
        token = re.sub(r'\.(?=\s)', '', token)
        if token.__contains__('.'):
            chars = token.split('.')
            for c in chars:
                if not c.isdigit():
                    if len(c) > 1:
                        token = re.sub(r'\.', ' ', token)
                        break
                else:
                    break
        token = token.lower()
        token = stem(token)
        if token != '':
            i += 1
            posToken.append([token, i])
    return posToken


def constructDict(tokens, docID):
    termDict = defaultdict(lambda: defaultdict(TermVector))
    for token in tokens:
        if (token[2] == docID):
            if token[0] not in stopWords:
                if token[0] in termDict:
                    if docID in termDict[token[0]]:
                        termDict[token[0]][docID].tf = termDict[token[0]][docID].getTF() + 1

                        termDict[token[0]][docID].pos.append(token[1])
                    else:
                        termDict[token[0]][docID] = TermVector(1, [token[1]])
                else:
                    docDict = defaultdict(TermVector)
                    docDict[docID] = TermVector(1, [token[1]])
                    termDict[token[0]] = docDict
        else:
            docID = token[2]
            if token[0] not in stopWords:
                if token[0] in termDict:
                    termDict[token[0]][docID] = TermVector(1, [token[1]])
                else:
                    docDict = defaultdict(TermVector)
                    docDict[docID] = TermVector(1, [token[1]])
                    termDict[token[0]] = docDict
    return termDict


def cleanUpDocs(file):
    page = file.read()
    validPage = "<root>" + page + "</root>"
    soup = BeautifulSoup(validPage, 'xml')
    docs = soup.find_all('DOC')
    return docs


def getText(doc):
    text = ""
    texts = doc.find_all('TEXT')
    for txt in texts:
        text += txt.get_text().strip() + " "
    text = cleanText(text)
    return text


def cleanText(text):
    text = regex.sub(r"[^\P{P}\-.,%]+", "", text)
    text = text.replace("`", " ")
    text = text.replace("-", " ")
    text = text.replace(",", " ")
    text = re.sub(r'\.\.+', ' ', text)
    return text


def parseCACM(path):
    docs = []
    current = None
    section = None
    with open(path, 'r', errors='ignore') as f:
        for line in f:
            line = line.rstrip('\n')
            if line.startswith('.I '):
                if current is not None:
                    docs.append(current)
                current = {'docno': line[3:].strip(), 'text': []}
                section = None
            elif line.startswith('.'):
                section = line[:2]
                if section not in ('.T', '.W', '.A', '.B', '.N'):
                    section = None
            elif section is not None and current is not None:
                current['text'].append(line)
    if current is not None:
        docs.append(current)
    return docs


def getDocLen(text):
    count = 0
    for line in text.splitlines():
        word = re.sub(r'\s+', ' ', line).strip().split(' ')
        count += len(word)
    return count


def stemTxt(text):
    stemText = ""
    for word in text.split():
        if word.endswith("."):
            stemText += stem(word[:len(word) - 1].lower()) + " "
        else:
            stemText += stem(word.lower()) + " "
    return stemText


def getTokens():
    docs = parseCACM(os.path.join('Files', 'cacm.all'))
    tokens = []
    docInfo = {}
    flag = 1
    countDoc = 0
    fileCount = len(docs)
    invFile = 1
    for fileIter, doc in enumerate(docs, start=1):
        docNo = doc['docno']
        print('Processing ' + str(fileIter) + ' out of ' + str(fileCount) + ' docs: ' + docNo)
        countDoc += 1
        text = cleanText(' '.join(doc['text']))
        docLen = getDocLen(text)
        docInfo[docNo] = docLen
        posTokens = tokenizer(text)
        for token in posTokens:
            token.append(docNo)
        tokens += posTokens
        if countDoc == 1000:
            countDoc = 0
            invFile = indexer(tokens, flag, invFile)
            tokens = []
            flag = 0

    if countDoc < 1000 and tokens:
        invFile = indexer(tokens, flag, invFile)

    #Resolve: Writing termMap and docMap in txt file
    pickler('Files/Stemmed/Pickles/termMap.p', catalog.termMap)
    writeHashMap(catalog.termMap, 'termMap.txt')
    
    pickler('Files/Stemmed/Pickles/docMap.p', docMap)
    writeHashMap(docMap, 'docMap.txt')
    
    pickler('Files/Stemmed/Pickles/docInfo.p', docInfo)
    writeHashMap(catalog.termMap, 'termMap.txt')
    
    pickler('Files/Stemmed/Pickles/docMap.p', docMap)
    writeHashMap(docMap, 'docMap.txt')
    
    pickler('Files/Stemmed/Pickles/docInfo.p', docInfo)


def writeHashMap(hashMap, fileName):
    outPath = os.path.join('Files', 'Stemmed', 'Maps', fileName)
    os.makedirs(os.path.dirname(outPath), exist_ok=True)
    with open(outPath, 'a+') as mapFile:
        for key, value in hashMap.items():
            mapFile.write(str(key) + ',' + str(value) + '\n')


def pickler(path, ds):
    f = open(path, 'wb')
    dill.dump(ds, f)
    f.close()

def calcTTF(termdict, term):
    ttf = 0
    for docid in termdict[term]:
        ttf += termdict[term][docid].getTF()
    return ttf


def calcDF(termdict, term):
    df = 0
    for docid in termdict[term]:
        df += 1
    return df

docNoSet = {}
def loadCatalog(termDict, fileName, invFileNo, catalogFile = None):
    fName = '%s%s.txt' %(fileName, invFileNo)
    invFile = open(fName, "a+")
    for term in termDict:
        termDict[term] = OrderedDict(sorted(termDict[term].items(), key=lambda x: x[1].tf, reverse=True))
        offset = invFile.tell()
        ttf = calcTTF(termDict, term)
        df = calcDF(termDict, term)
        if catalogFile != None:
            termid = catalog.termMap[term]
            catalog.removeTerm(term)
        else:
            if term not in catalog.termMap:
                termid = len(catalog.termMap) + 1
            else:
                termid = catalog.termMap[term]
        inputStr = [str(termid)]
        inputStr.append(',')
        inputStr.append(str(df))
        inputStr.append(',')
        inputStr.append(str(ttf))
        inputStr.append(':')
        for docno in termDict[term]:

            if catalogFile != None:
                docid = docno
            else:
                if docno not in docNoSet:
                    docid = len(docMap) + 1
                    docNoSet[docno] = docid
                    docMap[docid] = docno
                else:
                    docid = docNoSet[docno]
            inputStr.append(str(docid))
            inputStr.append(',')
            inputStr.append(str(termDict[term][docno].getTF()))
            inputStr.append(',')
            inputStr.append(','.join(str(e) for e in termDict[term][docno].getPos()))
            inputStr.append(';')
        inputStr[len(inputStr) - 1] = '\n'
        writeStr = ''.join(inputStr)
        length = len(writeStr)
        catalog.addTerm(term, offset, length, fName, termid)

        #Resolve: Storing termid in catalog and outputting catalog for each partial index
        if(catalogFile != None):
            catalogFile.write(str(termid) + ',' +str(offset)+','+str(length) +'\n')
        else: 
            tempCatalogFile = open('Files/Stemmed/catalogFile%d.txt' % (invFileNo), 'a+')
            tempCatalogFile.write(str(termid) + ',' +str(offset)+','+str(length) +'\n')
            tempCatalogFile.close()
            
        invFile.write(writeStr)
    invFile.close()
    return invFileNo + 1

#Resolve: seek and read by length
def loadInvList(offset, length, invFile, term, docMap = None):
    invList = OrderedDict()
    invFile.seek(offset)
    s = invFile.read(length)
    docDict = OrderedDict()
    remStr = s.split(':')[1].split(';')
    for item in remStr:
        docno = item.split(',')[0]
        if(docMap != None):
            docID = docMap.get(int(docno))
        else:
            docID = docno
        tf = int(item.split(',')[1])
        pos = [int(e) for e in item.split(',')[2:len(item.split(','))]]
        docDict[docID] = TermVector(tf, pos)
    invList[term] = docDict
    return invList

def mergeInvFiles():
    termDict = OrderedDict()
    catalogFile = open('Files/Stemmed/catalogFile.txt', 'a+')
    for term in catalog.terms:
        for file in catalog.terms[term]:
            invFile = open(file)
            invList = loadInvList(catalog.terms[term][file].offset, catalog.terms[term][file].length, invFile, term) #Resolve: seek and read by length
            invFile.close()
            if term not in termDict:
                termDict[term] = invList[term]
            else:
                for docId in invList[term]:
                    if docId in termDict[term]:
                        termDict[term][docId].tf = termDict[term][docId].getTF() + 1
                        termDict[term][docId].pos.extend(invList[term][docId].pos)
                    else:
                        termDict[term][docId] = TermVector(invList[term][docId].tf, invList[term][docId].pos)
        termDict[term] = OrderedDict(sorted(termDict[term].items(), key = lambda x: x[1].tf, reverse = True)) # Resolve: Sort by descending TF
        if len(termDict) == 1000:
            loadCatalog(termDict, "Files/Stemmed/invertedFile", 0, catalogFile)
            termDict ={}
    if len(termDict) > 0:
        loadCatalog(termDict, "Files/Stemmed/invertedFile", 0, catalogFile)

    catalogFile.close()

def indexer(tokens, flag, invFile):
    if not tokens:
        return invFile
    docID = tokens[0][2]

    termDict = constructDict(tokens, docID)
    invFile = loadCatalog(termDict, "Files/Stemmed/invertedFile", invFile)

    return invFile

docMap = {}
catalog = Catalog()
with open("Files/common_words") as sfile:
    stopWords = sfile.readlines()
stopWords = set(map(str.strip, stopWords))

def main():
    start_time = time.time()
    getTokens()
    mergeInvFiles()
    temp = time.time() - start_time
    print(temp)
    hours = temp // 3600
    temp = temp - 3600 * hours
    minutes = temp // 60
    seconds = temp - 60 * minutes
    print('%d:%d:%d' % (hours, minutes, seconds))

if __name__ == "__main__":
    main()

