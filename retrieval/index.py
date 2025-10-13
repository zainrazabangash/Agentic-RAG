from __future__ import annotations
import os, csv, re, json
from dataclasses import dataclass
from typing import List
from sentence_transformers import SentenceTransformer
import chromadb

@dataclass
class Hit:
    doc_id: str
    tenant: str
    visibility: str
    text: str
    score: float
    pii_flag: bool = False

def load_manifest(base_dir: str) -> list[dict]:
    mpath = os.path.join(base_dir, "data", "manifest.csv")
    with open(mpath, encoding="utf-8") as f:
        return list(csv.DictReader(f))

def load_tenant_acl(base_dir: str) -> dict:
    """Load tenant ACL to get PII flags for documents"""
    acl_path = os.path.join(base_dir, "data", "tenant_acl.csv")
    acl = {}
    with open(acl_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            acl[row["doc_id"]] = row["pii"] == "Y"
    return acl

def read_doc(base_dir: str, rel_path: str) -> str:
    with open(os.path.join(base_dir, rel_path), encoding="utf-8") as f:
        return f.read()

class Retriever:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.client = chromadb.PersistentClient(path=os.path.join(base_dir, ".chroma"))
        self.manifest = load_manifest(base_dir)
        self.tenant_acl = load_tenant_acl(base_dir)

    def _ns(self, tenant_id: str) -> str:
        return f"tenant_{tenant_id}"

    def build_or_update(self):
        """Idempotently creates per-tenant indices and a public index"""
        by_tenant = {}
        for row in self.manifest:
            by_tenant.setdefault(row["tenant"], []).append(row)
        for t, rows in by_tenant.items():
            ns = self._ns(t if t!="PUB" else "public")
            coll = self.client.get_or_create_collection(name=ns)
            ids, docs, metas = [], [], []
            for r in rows:
                ids.append(r["doc_id"])
                docs.append(read_doc(self.base_dir, r["path"]))
                vis = "public" if ("PUB_" in r["doc_id"] or r["tenant"]=="PUB") else "private"
                pii_flag = self.tenant_acl.get(r["doc_id"], False)
                metas.append({
                    "doc_id": r["doc_id"], 
                    "tenant": (t if t!="PUB" else "public"), 
                    "visibility": vis, 
                    "path": r["path"],
                    "pii": pii_flag
                })
            coll.upsert(ids=ids, documents=docs, metadatas=metas)

    def search(self, query: str, tenant_id: str, top_k: int = 6) -> List[Hit]:
        """Search both tenant-specific and public namespaces"""
        hits: list[Hit] = []
        def q(ns):
            coll = self.client.get_or_create_collection(ns)
            res = coll.query(query_texts=[query], n_results=top_k)
            docs = res.get("documents", [[]])[0]
            metas = res.get("metadatas", [[]])[0]
            dists = res.get("distances", [[]])[0]
            for text, meta, dist in zip(docs, metas, dists):
                score = 1.0/(1.0+float(dist)) if dist is not None else 0.5
                pii_flag = meta.get("pii", False)
                hits.append(Hit(
                    doc_id=meta["doc_id"], 
                    tenant=meta["tenant"], 
                    visibility=meta["visibility"], 
                    text=text, 
                    score=score,
                    pii_flag=pii_flag
                ))
        q(self._ns(tenant_id))
        q(self._ns("public"))
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:top_k]
