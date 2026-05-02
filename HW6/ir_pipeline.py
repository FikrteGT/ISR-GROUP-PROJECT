from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import csv
import math
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import xml.etree.ElementTree as ET

try:
    from elasticsearch import Elasticsearch
except ImportError:  # pragma: no cover - optional dependency
    Elasticsearch = None


_TOKEN_RE = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class Document:
    docno: str
    body_text: str


@dataclass(frozen=True)
class Query:
    query_id: str
    query_text: str


@dataclass(frozen=True)
class ScoredDocument:
    docno: str
    score: float


class InMemoryIndex:
    def __init__(self, documents: Sequence[Document]):
        self.documents = list(documents)
        self.doc_store: Dict[str, Document] = {
            doc.docno: doc for doc in self.documents}
        self.doc_lengths: Dict[str, int] = {}
        self.term_freqs: Dict[str, Counter[str]] = {}
        self.doc_freqs: Counter[str] = Counter()
        self.collection_tf: Counter[str] = Counter()
        self.term_postings: Dict[str,
                                 List[Tuple[str, int]]] = defaultdict(list)

        for document in self.documents:
            tokens = tokenize(document.body_text)
            tf = Counter(tokens)
            self.term_freqs[document.docno] = tf
            self.doc_lengths[document.docno] = sum(tf.values())
            self.collection_tf.update(tf)
            for term in tf:
                self.doc_freqs[term] += 1
                self.term_postings[term].append((document.docno, tf[term]))

    @property
    def total_docs(self) -> int:
        return len(self.documents)

    @property
    def avg_doc_length(self) -> float:
        if not self.documents:
            return 0.0
        return sum(self.doc_lengths.values()) / len(self.documents)

    @property
    def vocab_size(self) -> int:
        return len(self.collection_tf)

    def get_tf(self, term: str, docno: str) -> int:
        return self.term_freqs.get(docno, Counter()).get(term, 0)

    def get_df(self, term: str) -> int:
        return self.doc_freqs.get(term, 0)

    def get_doc_length(self, docno: str) -> int:
        return self.doc_lengths.get(docno, 0)

    def get_collection_probability(self, term: str) -> float:
        total_terms = sum(self.collection_tf.values())
        if total_terms == 0:
            return 0.0
        return self.collection_tf.get(term, 0) / total_terms

    def score_query(self, query_text: str, model: str) -> List[ScoredDocument]:
        query_terms = tokenize(query_text)
        scores: Dict[str, float] = {doc.docno: 0.0 for doc in self.documents}

        if model in {"tfidf", "okapi_tf", "bm25"}:
            avg_len = max(self.avg_doc_length, 1e-9)
            for term in query_terms:
                postings = self.term_postings.get(term)
                if not postings:
                    continue
                df = self.get_df(term)
                if model == "tfidf":
                    idf = math.log((self.total_docs + 1) / max(df, 1))
                    for docno, tf in postings:
                        scores[docno] += tf * idf
                elif model == "okapi_tf":
                    for docno, tf in postings:
                        doc_len = self.get_doc_length(docno)
                        scores[docno] += tf / \
                            (tf + 0.5 + 1.5 * (doc_len / avg_len))
                elif model == "bm25":
                    k1 = 1.2
                    b = 0.75
                    idf = math.log(
                        (self.total_docs - df + 0.5) / (df + 0.5) + 1.0)
                    for docno, tf in postings:
                        doc_len = self.get_doc_length(docno)
                        numerator = tf * (k1 + 1.0)
                        denominator = tf + k1 * \
                            (1 - b + b * (doc_len / avg_len))
                        scores[docno] += idf * (numerator / denominator)
        elif model == "laplace":
            for doc in self.documents:
                docno = doc.docno
                doc_len = self.get_doc_length(docno)
                for term in query_terms:
                    tf = self.get_tf(term, docno)
                    denominator = max(doc_len + self.vocab_size, 1)
                    scores[docno] += math.log((tf + 1.0) / denominator)
        elif model == "jm":
            lam = 0.8
            for doc in self.documents:
                docno = doc.docno
                doc_len = self.get_doc_length(docno)
                for term in query_terms:
                    tf = self.get_tf(term, docno)
                    p_doc = tf / doc_len if doc_len else 0.0
                    p_coll = self.get_collection_probability(term)
                    p = (1 - lam) * p_doc + lam * p_coll
                    if p > 0:
                        scores[docno] += math.log(p)
        else:
            raise ValueError(f"Unsupported model: {model}")

        return sorted((ScoredDocument(docno, score) for docno, score in scores.items()), key=lambda item: item.score, reverse=True)


MODEL_LABELS = {
    "tfidf": "TF-IDF",
    "okapi_tf": "Okapi TF",
    "bm25": "BM25",
    "laplace": "Laplace",
    "jm": "Jelinek-Mercer",
}


def tokenize(text: str) -> List[str]:
    return _TOKEN_RE.findall(text.lower())


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _read_text_file(path: str | Path) -> str:
    with open(path, 'r', encoding='utf-8', errors='ignore') as fh:
        content = fh.read()
    return content.lstrip('\ufeff')


def _looks_like_cacm(text: str) -> bool:
    return "\n.I " in text or text.startswith(".I ")


def _parse_cacm_documents(content: str) -> List[Document]:
    documents: List[Document] = []
    current_docno: Optional[str] = None
    current_section: Optional[str] = None
    sections: Dict[str, List[str]] = defaultdict(list)

    def flush() -> None:
        nonlocal current_docno, current_section, sections
        if not current_docno:
            return
        title = " ".join(sections.get("T", []))
        body_parts = []
        for key in ("T", "A", "B", "W", "K", "N"):
            body_parts.extend(sections.get(key, []))
        body_text = clean_text(" ".join(body_parts))
        if body_text:
            documents.append(
                Document(docno=current_docno, body_text=body_text))
        current_docno = None
        current_section = None
        sections = defaultdict(list)

    for raw_line in content.splitlines():
        line = raw_line.rstrip("\n")
        if line.startswith(".I "):
            flush()
            current_docno = line.split(maxsplit=1)[1].strip()
            continue
        if line.startswith(".") and len(line) > 1 and line[1].isalpha():
            current_section = line[1].upper()
            continue
        if current_docno and current_section:
            sections[current_section].append(line.strip())

    flush()
    return documents


def _parse_cacm_queries(content: str) -> List[Query]:
    queries: List[Query] = []
    current_qid: Optional[str] = None
    current_section: Optional[str] = None
    sections: Dict[str, List[str]] = defaultdict(list)

    def flush() -> None:
        nonlocal current_qid, current_section, sections
        if not current_qid:
            return
        query_text = clean_text(" ".join(sections.get("W", [])))
        if query_text:
            queries.append(Query(query_id=current_qid, query_text=query_text))
        current_qid = None
        current_section = None
        sections = defaultdict(list)

    for raw_line in content.splitlines():
        line = raw_line.rstrip("\n")
        if line.startswith(".I "):
            flush()
            raw_qid = line.split(maxsplit=1)[1].strip()
            current_qid = raw_qid.zfill(2) if raw_qid.isdigit() else raw_qid
            continue
        if line.startswith(".") and len(line) > 1 and line[1].isalpha():
            current_section = line[1].upper()
            continue
        if current_qid and current_section:
            sections[current_section].append(line.strip())

    flush()
    return queries


def parse_documents(xml_path: str | Path) -> List[Document]:
    content = _read_text_file(xml_path)
    if _looks_like_cacm(content):
        return _parse_cacm_documents(content)

    documents: List[Document] = []
    # Read file and wrap with a root tag to support collections without a single root element
    import re as _re
    # remove XML declarations so wrapping is valid
    content = _re.sub(r'<\?xml[^>]*\?>', '', content, flags=_re.I)
    content_wrapped = f"<root>\n{content}\n</root>"
    root = ET.fromstring(content_wrapped)

    def _child_text(node: ET.Element, tag: str) -> str:
        # attempt common casings
        return (node.findtext(tag) or node.findtext(tag.upper()) or node.findtext(tag.lower()) or "").strip()

    for node in root.iter():
        if node.tag.lower() == "doc":
            docno = _child_text(node, "docno")
            title = clean_text(_child_text(node, "title"))
            body = clean_text(_child_text(node, "text"))
            combined = clean_text(f"{title} {body}")
            if docno and combined:
                documents.append(Document(docno=docno, body_text=combined))
    return documents


def parse_queries(xml_path: str | Path) -> List[Query]:
    content = _read_text_file(xml_path)
    if _looks_like_cacm(content):
        return _parse_cacm_queries(content)

    # Read file and wrap with a root tag to support query files missing a single root
    import re as _re
    content = _re.sub(r'<\?xml[^>]*\?>', '', content, flags=_re.I)
    content_wrapped = f"<root>\n{content}\n</root>"
    root = ET.fromstring(content_wrapped)

    def _child_text(node: ET.Element, tag: str) -> str:
        return (node.findtext(tag) or node.findtext(tag.upper()) or node.findtext(tag.lower()) or "").strip()

    queries: List[Query] = []
    for node in root.iter():
        if node.tag.lower() == "top":
            query_id = _child_text(node, "num")
            query_text = clean_text(_child_text(node, "title"))
            if query_id and query_text:
                queries.append(Query(query_id=query_id, query_text=query_text))
    return queries


def parse_qrels(qrels_path: str | Path) -> Dict[str, Dict[str, int]]:
    relevance: Dict[str, Dict[str, int]] = defaultdict(dict)
    with open(qrels_path, "r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            parts = line.split()
            if len(parts) < 4:
                continue
            # CACM qrels are listed as query_id doc_id 0 0; treat listed pairs as relevant.
            if parts[2] == "0" and parts[3] == "0":
                query_id, docno, label = parts[0], parts[1], 1
            else:
                query_id, docno, label = parts[0], parts[2], int(parts[3])
            relevance[query_id][docno] = label
    return dict(relevance)


def build_feature_rows(index: InMemoryIndex, queries: Sequence[Query], qrels: Dict[str, Dict[str, int]], model_names: Sequence[str] = ("tfidf", "okapi_tf", "bm25", "laplace", "jm")) -> List[Dict[str, object]]:
    rows: Dict[Tuple[str, str], Dict[str, object]] = {}
    for query in queries:
        for model_name in model_names:
            ranked = index.score_query(query.query_text, model_name)
            for scored_document in ranked[:100]:
                key = (query.query_id, scored_document.docno)
                row = rows.setdefault(
                    key,
                    {
                        "QID-DocID": f"{query.query_id}-{scored_document.docno}",
                        "Label": qrels.get(query.query_id, {}).get(scored_document.docno, 0),
                    },
                )
                row[MODEL_LABELS[model_name]] = scored_document.score
    return list(rows.values())


def write_feature_matrix_csv(rows: Sequence[Dict[str, object]], output_path: str | Path) -> None:
    fieldnames = ["QID-DocID", "TF-IDF", "Okapi TF",
                  "BM25", "Laplace", "Jelinek-Mercer", "Label"]
    with open(output_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "QID-DocID": row.get("QID-DocID", ""),
                "TF-IDF": row.get("TF-IDF", 0.0),
                "Okapi TF": row.get("Okapi TF", 0.0),
                "BM25": row.get("BM25", 0.0),
                "Laplace": row.get("Laplace", 0.0),
                "Jelinek-Mercer": row.get("Jelinek-Mercer", 0.0),
                "Label": row.get("Label", 0),
            })


def write_trec_results(index: InMemoryIndex, queries: Sequence[Query], model: str, output_path: str | Path, top_k: int = 100) -> None:
    with open(output_path, "w", encoding="utf-8") as handle:
        for query in queries:
            ranked = index.score_query(query.query_text, model)[:top_k]
            for rank, scored_document in enumerate(ranked, start=1):
                handle.write(
                    f"{query.query_id} Q0 {scored_document.docno} {rank} {scored_document.score:.6f} Exp\n")


class ElasticsearchIndexAdapter:
    def __init__(self, index_name: str = "cranfield"):
        if Elasticsearch is None:
            raise RuntimeError("elasticsearch package is not installed")
        self.client = Elasticsearch()
        self.index_name = index_name

    def exists(self) -> bool:
        return bool(self.client.indices.exists(index=self.index_name))

    def create_index(self) -> None:
        if self.exists():
            return
        self.client.indices.create(
            index=self.index_name,
            mappings={
                "properties": {
                    "docno": {"type": "keyword"},
                    "body_text": {"type": "text"},
                    "doc_len": {"type": "integer"},
                }
            },
        )

    def index_documents(self, documents: Sequence[Document]) -> None:
        self.create_index()
        for document in documents:
            self.client.index(
                index=self.index_name,
                id=document.docno,
                document={"docno": document.docno, "body_text": document.body_text, "doc_len": len(
                    tokenize(document.body_text))},
                refresh=False,
            )
        self.client.indices.refresh(index=self.index_name)
