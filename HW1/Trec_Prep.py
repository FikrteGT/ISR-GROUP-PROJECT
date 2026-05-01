QRELS_INPUT  = r'C:\Information-Retrieval\HW1\cacm_dataSet\qrels.text'
QRELS_OUTPUT = r'C:\Information-Retrieval\HW1\qrels.txt'


def createQrel():
    """
    Converts CACM qrels.text -> qrels.txt
    CACM format:  queryID  docID  0  0
    Output format: queryID 0 docID 1
    """
    with open(QRELS_INPUT, 'r') as fin, open(QRELS_OUTPUT, 'w') as fout:
        for line in fin:
            cols = line.split()
            if len(cols) >= 2:
                fout.write(f"{cols[0]} 0 {cols[1]} 1\n")
    print("qrels.txt created successfully.")


createQrel()
