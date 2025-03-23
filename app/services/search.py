import faiss
import numpy as np
from pydantic import BaseModel
from sqlmodel import Session, select
from ..models import Note
from ..database import engine

DIMENSIONS = 3072


class IndexEntry(BaseModel):
    id: int
    embedding: list[float]


class FaissIndexManager:
    def __init__(self):
        self.indices = {}

    def build_index(self, key: str, entries: list[IndexEntry]):
        index = faiss.IndexFlatIP(DIMENSIONS)
        id_map = []

        embeddings = np.array(
            [entry.embedding for entry in entries], dtype='float32')
        faiss.normalize_L2(embeddings)

        index.add(embeddings)
        id_map = [entry.id for entry in entries]
        self.indices[key] = (index, id_map)

    def query_index(self, key: str, query_embedding: list[float], min_results: int = 2, max_results: int = 10, min_similarity: float = 0.5) -> list[int]:
        if key not in self.indices:
            raise ValueError(f"Index for key {key} not found")

        index, id_map = self.indices[key]
        query_vector = np.array([query_embedding], dtype='float32')
        faiss.normalize_L2(query_vector)

        scores, indices = index.search(query_vector, max_results)
        results = []
        for j, (i, score) in enumerate(zip(indices[0], scores[0])):
            if i == -1:
                continue
            if j < min_results or (score >= min_similarity and j < max_results):
                results.append(id_map[i])
        return results


index_manager = FaissIndexManager()


class NoteSearchService:
    def build_all_user_indexes(self):
        with Session(engine) as session:
            query = select(Note.id, Note.user_id, Note.embedding).where(
                Note.embedding.is_not(None))
            results = session.exec(query).all()

            index = {}
            for entry in results:
                if entry.user_id not in index:
                    index[entry.user_id] = []
                index[entry.user_id].append(IndexEntry(
                    id=entry.id, embedding=entry.embedding))

            for user_id, entries in index.items():
                index_manager.build_index(f"notes_{user_id}", entries)

    def update_user_index(self, user_id: int):
        with Session(engine) as session:
            query = select(Note.id, Note.embedding).where(
                Note.embedding.is_not(None), Note.user_id == user_id)
            results = session.exec(query).all()
            index_manager.build_index(f"notes_{user_id}", [
                IndexEntry(id=id, embedding=embedding) for id, embedding in results
            ])

    def search(self, user_id: int, query_embedding: list[float], min_results: int = 2, max_results: int = 10, min_similarity: float = 0.5) -> list[int]:
        return index_manager.query_index(f"notes_{user_id}", query_embedding, min_results, max_results, min_similarity)


search_service = NoteSearchService()


def build_all_user_indexes():
    search_service.build_all_user_indexes()
