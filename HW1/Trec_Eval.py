from collections import OrderedDict
import math

relevanceJudgements = {}


def retrieveQueryResults(rankList):
    queryResults = OrderedDict()
    with open(rankList, 'r') as f:
        for line in f:
            items = line.split()
            if len(items) < 3:
                continue
            queryID    = items[0]
            documentID = items[2]
            if queryID in queryResults:
                queryResults[queryID].append(documentID)
            else:
                queryResults[queryID] = [documentID]
    return queryResults


def getRelevanceJudgements(qrel):
    global relevanceJudgements
    relevanceJudgements = {}
    with open(qrel, 'r') as f:
        for line in f:
            cols = line.split()
            if len(cols) < 4:
                continue
            queryID    = cols[0]
            documentID = cols[2]
            relevance  = cols[3].strip()
            if relevance == '1':
                if queryID in relevanceJudgements:
                    relevanceJudgements[queryID].append(documentID)
                else:
                    relevanceJudgements[queryID] = [documentID]


def designateVals(lst, val, rank):
    if rank in lst:
        lst[rank].append(val)
    else:
        lst[rank] = [val]
    return lst


def printMeanVals(lst, desc, kVals=[], qid=''):
    if not kVals:
        if len(lst) == 0:
            return
        print(desc + ': ' + str("{:.4f}".format(math.fsum(lst) / len(lst))))
    else:
        for k in kVals:
            if k not in lst or len(lst[k]) == 0:
                continue
            if qid:
                print(desc + str(k) + ' for ' + qid + ': ' + str("{:.4f}".format(math.fsum(lst[k]) / len(lst[k]))))
            else:
                print(desc + str(k) + ': ' + str("{:.4f}".format(math.fsum(lst[k]) / len(lst[k]))))


def calculateMetrics(queryResults, option):
    kVals = [5, 10, 20, 50, 100]
    AP, RP, NDCG = [], [], []
    P, R, F1 = {}, {}, {}

    with open("details.txt", 'w') as f:
        for queryID in queryResults:
            relevanceScore = []
            PTemp, RTemp, F1Temp = {}, {}, {}
            psum, rank, relevantNumber, rp = 0, 0, 0, 0

            results = queryResults[queryID]

            if queryID not in relevanceJudgements:
                continue
            relevantDocuments = relevanceJudgements[queryID]

            for document in results:
                rank += 1
                isRelevant = 0
                if document in relevantDocuments:
                    relevantNumber += 1
                    isRelevant = 1
                if rank <= len(relevantDocuments):
                    rp = relevantNumber

                precision = relevantNumber / rank
                if isRelevant:
                    psum += precision
                recall = 0 if not relevantDocuments else relevantNumber / len(relevantDocuments)

                if rank in kVals:
                    P     = designateVals(P,     precision, rank)
                    PTemp = designateVals(PTemp, precision, rank)
                    f1 = (2 * precision * recall) / (precision + recall) if relevantNumber > 0 else 0
                    F1     = designateVals(F1,     f1, rank)
                    F1Temp = designateVals(F1Temp, f1, rank)
                    R     = designateVals(R,     recall, rank)
                    RTemp = designateVals(RTemp, recall, rank)

                relevanceScore.append(isRelevant)
                f.write(f"{queryID} {document} {rank} {isRelevant} "
                        f"{precision:.4f} {recall:.4f}\n")

            j, dc_value = 0, 0.0
            for score in relevanceScore:
                j += 1
                dc_value += score / math.log(1.0 + j)

            j, idc_value = 0, 0.0
            for score in sorted(relevanceScore, reverse=True):
                j += 1
                idc_value += score / math.log(1.0 + j)

            ndcg = 0.0 if idc_value == 0.0 else dc_value / idc_value
            rPrecision  = rp / len(relevantDocuments)
            avgPrecision = 0.0 if not relevantNumber else psum / len(relevantDocuments)

            RP.append(rPrecision)
            NDCG.append(ndcg)
            AP.append(avgPrecision)

            if option == 1:
                print(f'--- Query {queryID} ---')
                print(f'Average Precision : {avgPrecision:.4f}')
                print(f'R-Precision       : {rPrecision:.4f}')
                print(f'nDCG              : {ndcg:.4f}')
                print('Precision@ Values')
                printMeanVals(PTemp, '  P@', kVals, queryID)
                print('Recall@ Values')
                printMeanVals(RTemp, '  R@', kVals, queryID)
                print('F1@ Values')
                printMeanVals(F1Temp, '  F1@', kVals, queryID)
                print()

    print('========== SUMMARY (all queries) ==========')
    printMeanVals(AP,   'Mean Average Precision (MAP)')
    printMeanVals(RP,   'Mean R-Precision')
    printMeanVals(NDCG, 'Mean nDCG')
    print('\nPrecision@ Values')
    printMeanVals(P,  '  Mean P@', kVals)
    print('\nRecall@ Values')
    printMeanVals(R,  '  Mean R@', kVals)
    print('\nF1@ Values')
    printMeanVals(F1, '  Mean F1@', kVals)


def main():
    cmd = input('Enter command: ')
    cmd_params = cmd.split()

    if len(cmd_params) == 4:
        # trec_eval -q qrels.txt rankList.txt
        queryResults = retrieveQueryResults(cmd_params[3])
        getRelevanceJudgements(cmd_params[2])
        calculateMetrics(queryResults, 1)
    else:
        # trec_eval qrels.txt rankList.txt
        queryResults = retrieveQueryResults(cmd_params[2])
        getRelevanceJudgements(cmd_params[1])
        calculateMetrics(queryResults, 2)


main()
