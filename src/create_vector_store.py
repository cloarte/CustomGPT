from dotenv import load_dotenv

_ = load_dotenv(override=True)

import argparse

parser = argparse.ArgumentParser(description="Vector store creation utility")
parser.add_argument(
    "-f",
    "--force",
    action="store_true",
    help="Force recreation of vector store even if it already exists",
)
args = parser.parse_args()
print("# Force recreation of vector store:", args.force)

import os
from typing import List

from tqdm import tqdm
from transformers import AutoTokenizer
from langchain.text_splitter import TokenTextSplitter
from transformers import logging as hf_logging

hf_logging.set_verbosity_error()

from services import VectorStore
from services import TextEncoder
from services import PlagueService
from models import VectorizableDocument

# Define constants for collection and vector names
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
SPARSE_VECTORS_NAME = os.getenv("COLLECTION_SPARSE_VECTORS_NAME")
DENSE_VECTORS_NAME = os.getenv("COLLECTION_DENSE_VECTORS_NAME")


def get_safe_filename(filename: str, word_limit=5):
    words = filename.split()
    limited_name = " ".join(words[:word_limit])
    safe_filename = "".join(
        c for c in limited_name if c.isalnum() or c in (" ", "_", "-")
    ).rstrip()
    return safe_filename


def main():
    plagues = PlagueService().get_plagues()

    # Initialize the text encoder with sparse and dense models
    text_encoder = TextEncoder(
        sparse_model_name=os.getenv("SPARSE_EMBEDDINGS_MODEL_NAME"),
        dense_model_name=os.getenv("DENSE_EMBEDDINGS_MODEL_NAME"),
    )

    # Initialize the vector store with storage path and encoder
    vector_store = VectorStore(
        "qdrant_storage", text_encoder, SPARSE_VECTORS_NAME, DENSE_VECTORS_NAME
    )
    print("# Initializing VectorStore")

    # Check if the collection already exists
    collection_exists = vector_store.collection_exists(COLLECTION_NAME)

    current_id = 0
    if not collection_exists or args.force:
        # Create a new collection if it doesn't exist or if forced
        vector_store.create_collection(
            COLLECTION_NAME, dense_vector_size=text_encoder.get_dense_embedding_size()
        )

        print("# Preparing documents for sparse embeddings")
        documents_for_sparse_embeddings = []
        for plague_data in plagues:
            current_id += 1
            documents_for_sparse_embeddings.append(
                VectorizableDocument(
                    id=current_id,
                    text=plague_data.keywords,
                    metadata={
                        "scientific_name": plague_data.scientific_name,
                        "common_names": plague_data.common_names,
                        "source_url": plague_data.source_url,
                        "es_cuarentenaria": plague_data.is_quarantine
                    },
                )
            )

        print(
            f"# Total vectorizable documents for sparse embeddings: {len(documents_for_sparse_embeddings)}"
        )

        # Add sparse embeddings to the vector store
        print("# Building sparse embeddings...")
        vector_store.add_documents(
            COLLECTION_NAME, documents_for_sparse_embeddings, use_sparse=True
        )

        # Define chunking parameters for splitting text into smaller pieces
        chunk_size = 400
        chunk_overlap = 80

        # Initialize tokenizer for dense embeddings
        tokenizer = AutoTokenizer.from_pretrained(
            os.getenv("DENSE_EMBEDDINGS_MODEL_NAME"), trust_remote_code=True
        )

        # Initialize text splitter using the tokenizer
        text_splitter = TokenTextSplitter.from_huggingface_tokenizer(
            tokenizer=tokenizer, chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )

        if not os.path.exists("data/content_chunks"):
            os.makedirs("data/content_chunks", exist_ok=True)

        # Prepare documents for dense embeddings
        documents_for_dense_embeddings: List[VectorizableDocument] = []
        for plague_data in plagues:
            content_chunks = text_splitter.split_text(plague_data.content)
            for content_chunk in content_chunks:

                # Save content chunks to a file for debugging or inspection
                safe_filename = get_safe_filename(plague_data.scientific_name)
                with open(
                    f"data/content_chunks/{safe_filename}.txt",
                    "a",
                    encoding="utf-8",
                ) as f:
                    f.write(content_chunk + "\n")
                    f.write(f"Text Len: {len(content_chunk)}\n")
                    f.write("-" * 80 + "\n")

                current_id += 1
                documents_for_dense_embeddings.append(
                    VectorizableDocument(
                        id=current_id,
                        text=content_chunk,
                        metadata={
                            "scientific_name": plague_data.scientific_name,
                            "common_names": plague_data.common_names,
                            "source_url": plague_data.source_url,
                            "content_chunk": content_chunk,
                            "es_cuarentenaria": plague_data.is_quarantine
                        },
                    )
                )

        print(
            f"# Total vectorizable documents for dense embeddings: {len(documents_for_dense_embeddings)}"
        )

        # Add dense embeddings to the vector store
        print("# Building dense embeddings")
        vector_store.add_documents(
            COLLECTION_NAME, documents_for_dense_embeddings, use_dense=True
        )

    else:
        # Skip creation if the collection already exists
        print(f"# Collection '{COLLECTION_NAME}' already exists. Skipping creation.")


if __name__ == "__main__":
    main()
