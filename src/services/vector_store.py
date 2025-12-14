from typing import Dict, List, Optional, Union

import tqdm
from qdrant_client import QdrantClient, models

from models import VectorizableDocument
from .text_encoder import TextEncoder

class VectorStore:
    def __init__(self, storage_path: str, text_encoder: TextEncoder, sparse_vectors_name: str, dense_vectors_name:str):
        self.client = QdrantClient(path=storage_path)
        self.text_encoder = text_encoder
        self.sparse_vectors_name = sparse_vectors_name
        self.dense_vectors_name = dense_vectors_name
        
    def collection_exists(self, collection_name: str) -> bool:
        return collection_name in [col.name for col in self.client.get_collections().collections]
    
    def create_collection(self, collection_name: str, dense_vector_size: int):
        self.client.recreate_collection(
            collection_name=collection_name,
            sparse_vectors_config={
                self.sparse_vectors_name: models.SparseVectorParams(
                    index=models.SparseIndexParams(on_disk=True)
                )
            },
            vectors_config={
                self.dense_vectors_name: models.VectorParams(
                    size=dense_vector_size,
                    distance=models.Distance.COSINE,
                    on_disk=True
                )
            },
            hnsw_config=models.HnswConfigDiff(
                m=16,
                ef_construct=100,
                full_scan_threshold=10000,
                on_disk=True
            ),
            on_disk_payload=True
        )
    
    def add_documents(self, collection_name: str, documents: List[VectorizableDocument], use_sparse: bool = False, use_dense: bool = False):
        texts = [doc.text for doc in documents]

        sparse_embeddings = []
        if use_sparse:
            for text in tqdm.tqdm(texts):
                sparse_embeddings.append(self.text_encoder.encode_sparse(text))
        else:
            sparse_embeddings = None

        dense_embeddings = []
        if use_dense:
            for text in tqdm.tqdm(texts):
                dense_embeddings.append(self.text_encoder.encode_dense(text, 'retrieval.passage'))
        else:
            dense_embeddings = None
        
        points = []
        for idx, doc in enumerate(documents):
            vector_data = {}
            if use_sparse:
                vector_data[self.sparse_vectors_name] = models.SparseVector(
                    indices=sparse_embeddings[idx][0],
                    values=sparse_embeddings[idx][1]
                )
            if use_dense:
                vector_data[self.dense_vectors_name] = dense_embeddings[idx]
            
            points.append(models.PointStruct(
                id=doc.id,
                vector=vector_data,
                payload=doc.metadata
            ))
        
        if use_sparse:
            print(f"# Saving {len(points)} sparse embeddings to Qdrant")
            self.client.upsert(collection_name=collection_name, points=points)
        if use_dense:
            print(f"# Saving {len(points)} dense embeddings to Qdrant")
            self.client.upsert(collection_name=collection_name, points=points)
        return len(points)
    
    def search(self, collection_name: str, query_embedding: Union[models.NamedVector,models.NamedSparseVector], filter_criteria: Optional[Dict[str, List[str]]] = None,top_k: int = 12):
        search_filter = None

        if filter_criteria:
            must_conditions = [
                models.FieldCondition(
                    key=key,
                    match=models.MatchAny(any=values)
                )
                for key, values in filter_criteria.items()
            ]
            search_filter = models.Filter(must=must_conditions)

        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            query_filter=search_filter,
            limit=top_k
        )

        return [(res.id, res.score, res.payload) for res in results]