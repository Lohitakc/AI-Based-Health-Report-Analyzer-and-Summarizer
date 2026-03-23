from __future__ import annotations

import hashlib
import os
from functools import lru_cache
from pathlib import Path

from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

try:
    from langchain_chroma import Chroma
except ImportError:  # pragma: no cover - compatibility fallback
    from langchain_community.vectorstores import Chroma

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:  # pragma: no cover - compatibility fallback
    from langchain_community.embeddings import HuggingFaceEmbeddings

from app.config import CHROMA_DIR, DATA_DIR


class HashEmbeddings(Embeddings):
    def __init__(self, dim: int = 384) -> None:
        self.dim = dim

    def _embed(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        seed = list(digest) * ((self.dim // len(digest)) + 1)
        vector = [float((value / 255.0) * 2 - 1) for value in seed[: self.dim]]
        return vector

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]


class MedicalVectorStore:
    def __init__(self, persist_directory: Path | None = None) -> None:
        target_dir = persist_directory or CHROMA_DIR
        target_dir.mkdir(parents=True, exist_ok=True)

        self.embedding = self._build_embeddings()
        self.store = Chroma(
            collection_name="medical_reference",
            embedding_function=self.embedding,
            persist_directory=str(target_dir),
        )

    @staticmethod
    def _build_embeddings() -> Embeddings:
        try:
            embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={"local_files_only": True},
            )
            embeddings.embed_query("health check")
            return embeddings
        except Exception:
            if os.getenv("ALLOW_ONLINE_MODEL_DOWNLOAD", "0") == "1":
                try:
                    embeddings = HuggingFaceEmbeddings(
                        model_name="sentence-transformers/all-MiniLM-L6-v2"
                    )
                    embeddings.embed_query("health check")
                    return embeddings
                except Exception:
                    pass
            return HashEmbeddings()

    def is_empty(self) -> bool:
        snapshot = self.store.get()
        return len(snapshot.get("ids", [])) == 0

    def _load_documents(self) -> list[Document]:
        docs: list[Document] = []
        for file_path in sorted(DATA_DIR.glob("*")):
            if file_path.suffix.lower() not in {".md", ".txt"}:
                continue
            content = file_path.read_text(encoding="utf-8")
            docs.append(
                Document(
                    page_content=content,
                    metadata={"source_file": file_path.name},
                )
            )
        return docs

    def ingest(self, force_rebuild: bool = False) -> int:
        if force_rebuild:
            self.store.delete_collection()
            self.store = Chroma(
                collection_name="medical_reference",
                embedding_function=self.embedding,
                persist_directory=str(CHROMA_DIR),
            )
        elif not self.is_empty():
            return 0

        documents = self._load_documents()
        if not documents:
            return 0

        splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=80)
        chunks = splitter.split_documents(documents)
        self.store.add_documents(chunks)
        return len(chunks)

    def retrieve(self, query: str, k: int = 3) -> list[Document]:
        return self.store.similarity_search(query, k=k)


@lru_cache(maxsize=1)
def get_vector_store() -> MedicalVectorStore:
    client = MedicalVectorStore()
    client.ingest(force_rebuild=False)
    return client
