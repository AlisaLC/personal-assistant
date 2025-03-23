import annoy
from pydantic import BaseModel
from sqlmodel import Session, select
from ..models import Note
from ..database import engine

DIMENSIONS = 3072
TREE_COUNT = 10


class IndexEntry(BaseModel):
    id: int
    embedding: list[float]


class AnnoyIndexManager:
    def __init__(self):
        self.indices = {}

    def build_index(self, key: str, entries: list[IndexEntry]):
        index = annoy.AnnoyIndex(DIMENSIONS, 'angular')
        for entry in entries:
            index.add_item(entry.id, entry.embedding)
        index.build(TREE_COUNT)
        self.indices[key] = index

    def query_index(self, key: str, query_embedding: list[float], max_results: int = 10, min_similarity: float = 0.5) -> list[int]:
        if key not in self.indices:
            raise ValueError(f"Index for key {key} not found")
        results = self.indices[key].get_nns_by_vector(
            query_embedding, max_results, include_distances=True)
        return [self.entries[i] for i in results if results[i][1] >= min_similarity]


index_manager = AnnoyIndexManager()


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
            index_manager.build_index(f"notes_{user_id}", [IndexEntry(
                id=id, embedding=embedding) for id, embedding in results])

    def search(self, user_id: int, query_embedding: list[float], max_results: int = 10, min_similarity: float = 0.5) -> list[int]:
        return index_manager.query_index(f"notes_{user_id}", query_embedding, max_results, min_similarity)


search_service = NoteSearchService()


def build_all_user_indexes():
    search_service.build_all_user_indexes()
