from __future__ import division
import math
from operator import itemgetter
from collections import defaultdict
import dill
import os

# To store the term_freq and positions of the term
class TermVector:
    def __init__(self, tf, pos):
        self.tf = tf
        self.pos = pos
    def getTF(self): return self.tf
    def getPos(self): return self.pos

def unpickler(file):
    with open(file, 'rb') as f:
        return dill.load(f)

def restructureTV(termVector):
    dictDocID = defaultdict(lambda: defaultdict(list))
    for key in termVector:
        for docid in termVector[key]:
            # Stores [tf, [pos1, pos2...]]
            dictDocID[docid][key] = [termVector[key][docid].getTF(), termVector[key][docid].getPos()]
    return dictDocID

def Okapi_BM25(qNo, termVector, termStats, docInfo, D, avgDocLen):
    k1, k2, b = 1.2, 100, 0.75
    docScore = []
    dictDocID = restructureTV(termVector)
    
    queryFreq = {}
    for key in termVector:
        queryFreq[key] = queryFreq.get(key, 0) + 1
        
    for docid in dictDocID:
        bm25 = 0.0
        try:
            for key in dictDocID[docid]:
                # 1. Get Term Frequency (tfwd) - pulling from [tf, pos] list
                val = dictDocID[docid][key]
                tfwd = float(val[0]) 
                
                # 2. Get Document Length
                docLen = float(docInfo.get(docid, 0))
                
                # 3. Get Document Frequency (df) - handling lists if necessary
                df_raw = termStats.get(key, 1)
                if isinstance(df_raw, list):
                    df = float(df_raw[0])
                else:
                    df = float(df_raw)
                
                # 4. Get Query Term Frequency
                qtf = float(queryFreq.get(key, 1))
                
                # BM25 Formula with explicit float casting for all variables
                idf = math.log((float(D) - df + 0.5) / (df + 0.5) + 1)
                termWeight = ((tfwd * (k1 + 1)) / (tfwd + k1 * (1 - b + b * (docLen / float(avgDocLen)))))
                queryWeight = ((qtf * (k2 + 1)) / (qtf + k2))
                
                bm25 += idf * termWeight * queryWeight
            
            docScore.append([docid, bm25])
        except Exception as e:
            # This helps catch if a specific doc or key has bad data
            continue
    
    # Sort by score descending
    docScore.sort(key=itemgetter(1), reverse=True)
    
    # Write to file
    output_path = 'Files/Stemmed/OkapiBM25_Results_File.txt'
    with open(output_path, 'a') as f:
        for rank, ds in enumerate(docScore[:1000], 1):
            # ds[0] is docid, ds[1] is score
            f.write("%s Q0 %s %d %f Exp\n" % (str(qNo), str(ds[0]), rank, float(ds[1])))
    return len(docScore)

# --- MAIN EXECUTION ---
try:
    # Ensure directory exists
    if not os.path.exists('Files/Stemmed'):
        os.makedirs('Files/Stemmed')
    
    # Load global stats
    docInfo = unpickler('Files/Stemmed/Pickles/docInfo.p')
    D = len(docInfo)
    avgDocLen = float(sum(docInfo.values())) / D
    
    print("Initializing BM25... Total Docs: %d, Avg Length: %.2f" % (D, avgDocLen))
    
    # Clear old results
    output_file = 'Files/Stemmed/OkapiBM25_Results_File.txt'
    open(output_file, 'w').close()

    # Process all 64 queries
    for i in range(1, 65):
        try:
            termStats = unpickler('Files/Stemmed/Pickles/termStats%s.p' % i)
            termVector = unpickler('Files/Stemmed/Pickles/termVector%s.p' % i)
            
            doc_count = Okapi_BM25(i, termVector, termStats, docInfo, D, avgDocLen)
            print("Query %d: Processed %d documents" % (i, doc_count))
            
        except Exception as e:
            print("Error loading data for Query %d: %s" % (i, e))

    print("\nAll queries complete. Results saved to: %s" % output_file)

except Exception as e:
    print("Fatal Error: %s" % e)
