from elasticsearch import Elasticsearch
#es = Elasticsearch(hosts=["http://localhost:9200"])
import time
from elasticsearch_dsl import Search
import Canonicalizer
import warnings
from elasticsearch import ElasticsearchWarning

warnings.filterwarnings("ignore")
es = Elasticsearch(
    "https://localhost:9200",
    basic_auth=("elastic", "e7kUbdwwZ82mdCtw*9Je"),
    verify_certs=False
)
def scroller(docID):
    for id in docID:
        id = id.strip()
        outlinks = set()
        res = es.get(index="hw3_crawl", id=id)
        outlinks = set(res['_source'].get("outlinks").strip().split('\n'))
        for ol in outlinks:
            ol = ol.strip()
            if ol in linkgraphTemp:
                linkgraphTemp[ol].add(id)
            else:
                linkgraphTemp[ol] = set()
                linkgraphTemp[ol].add(id)

canon = Canonicalizer.Canonicalizer
start_time = time.time()

linkgraphTemp = {}
linkGraph = {}
sinkNodes = set()
s = Search(using=es, index="hw3_crawl")
s = s.source([])
docID = set(h.meta.id for h in s.scan())
scroller(docID)


for ol in linkgraphTemp:
    if ol in docID:
        linkGraph[ol] = linkgraphTemp.get(ol)
    if ol == '':
        for link in linkgraphTemp.get(ol):
            sinkNodes.add(link)

print(sinkNodes)
print(len(sinkNodes))

outputFile = open("C:\\Users\\pc\\Desktop\\ISR-assignment\\Information-Retrieval-master\\HW4\\linkgraph.txt", "w")
for ol in linkGraph:
    line = ol
    for il in linkGraph[ol]:
        line += ' ' + il
    outputFile.write(line +'\n')
outputFile.close()

temp = time.time()-start_time
print(temp)
hours = temp//3600
temp = temp - 3600*hours
minutes = temp//60
seconds = temp - 60*minutes
print('%d:%d:%d' %(hours,minutes,seconds))