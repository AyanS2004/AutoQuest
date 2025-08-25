from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

class LocalRAG:
    def __init__(self, docs):
        self.docs = docs
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = None
        self.doc_embeddings = None
        self.build_index()

    def build_index(self):
        self.doc_embeddings = self.embedder.encode(self.docs, convert_to_numpy=True)
        self.index = faiss.IndexFlatL2(self.doc_embeddings.shape[1])
        self.index.add(self.doc_embeddings)

    def retrieve(self, query, k=3):
        query_vec = self.embedder.encode([query])
        D, I = self.index.search(np.array(query_vec), k)
        return [self.docs[i] for i in I[0]]
