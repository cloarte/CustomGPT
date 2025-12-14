from dotenv import load_dotenv

_ = load_dotenv(override=True)

import os
import json
import requests
from collections import OrderedDict, defaultdict

from FlagEmbedding import FlagReranker
from qdrant_client.models import NamedVector, NamedSparseVector, SparseVector
from transformers import logging as hf_logging

hf_logging.set_verbosity_error()

from repositories import CabiSpeciesRepository
from services import VectorStore
from services import QueryProcessor
from services import TextEncoder

# Define constants for collection and vector names
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
SPARSE_VECTORS_NAME = os.getenv("COLLECTION_SPARSE_VECTORS_NAME")
DENSE_VECTORS_NAME = os.getenv("COLLECTION_DENSE_VECTORS_NAME")


def main():
    """
    Main function to demonstrate the usage of a text encoder, vector store, and query processor
    for keyword-based and semantic search.
    """
    # Initialize the `TextEncoder` with sparse and dense model names.
    text_encoder = TextEncoder(
        sparse_model_name=os.getenv("SPARSE_EMBEDDINGS_MODEL_NAME"),
        dense_model_name=os.getenv("DENSE_EMBEDDINGS_MODEL_NAME"),
    )

    # Initialize the `VectorStore` with storage location and vector names.
    vector_store = VectorStore(
        "qdrant_storage", text_encoder, SPARSE_VECTORS_NAME, DENSE_VECTORS_NAME
    )
    print("# VectorStore initialized")

    # Check if the specified collection exists in the vector store.
    collection_exists = vector_store.collection_exists(COLLECTION_NAME)
    print(
        f"# Does collection '{COLLECTION_NAME}' exists?",
        "Yes" if collection_exists else "No",
    )

    # If the collection does not exist, execute the create_vector_store.py script.
    if not collection_exists:
        print(
            f"# The collection '{COLLECTION_NAME}' does not exist. Please execute create_vector_store.py to create it..."
        )
        return

    # Initialize the `QueryProcessor` with the dense model name.
    query_processor = QueryProcessor(os.getenv("DENSE_EMBEDDINGS_MODEL_NAME"))

    cabi_species_repository = CabiSpeciesRepository()
    cabi_species = cabi_species_repository.get_all_cabi_species()
    seed_keywords = [cabi_specie.scientific_name for cabi_specie in cabi_species]

    # Initialize the Reranker with the specified model name.
    reranker = FlagReranker(os.getenv("RERANKER_MODEL_NAME"), use_fp16=False)

    while True:
        # Ask the user for input
        query = input("Enter your query (or type 'exit' to quit): ").strip()

        # Exit condition
        if query.lower() in {"exit", "quit"}:
            print("Exiting keyword extraction.")
            break

        print("# Query:", query)

        extracted_terms = query_processor.extract_keywords(query, seed_keywords)
        print("# Extracted Keywords:", extracted_terms)

        # Encode the extracted keywords into a sparse vector representation.
        query_indices, query_values = text_encoder.encode_sparse(extracted_terms)
        keyword_query_embedding = NamedSparseVector(
            name=SPARSE_VECTORS_NAME,
            vector=SparseVector(indices=query_indices, values=query_values),
        )

        # Perform a keyword-based search in the vector store.
        keyword_search_results = vector_store.search(
            COLLECTION_NAME, keyword_query_embedding, top_k=12
        )

        print("# Keyword Search Results:")
        for result in keyword_search_results:
            print(
                f" - [Score: {result[1]:.2f}] {result[2]['scientific_name']} ({result[2]['source_url']})"
            )

        # Extract valid source URLs from the keyword search results.
        valid_sources_urls = [
            result[2]["source_url"] for result in keyword_search_results
        ]

        # Encode the original query into a dense vector representation.
        query_embeddings = text_encoder.encode_dense(query, "retrieval.query")
        semantic_query_embedding = NamedVector(
            name=DENSE_VECTORS_NAME,
            vector=query_embeddings,
        )

        # Perform a semantic search in the vector store with filter criteria.
        filter_criteria = {"source_url": valid_sources_urls}

        semantic_search_results = vector_store.search(
            COLLECTION_NAME,
            semantic_query_embedding,
            filter_criteria=filter_criteria,
            top_k=12,
        )

        avg_score = sum(result[1] for result in semantic_search_results) / len(
            semantic_search_results
        )
        sentence_pairs = [
            [query, result[2]["content_chunk"]]
            for result in semantic_search_results
            if result[1] > avg_score
        ]
        scores = reranker.compute_score(sentence_pairs, normalize=True)
        ranked_semantic_search_results = [
            item
            for score, item in sorted(
                zip(scores, semantic_search_results), key=lambda x: x[0], reverse=True
            )
        ]

        # Print the results of both keyword-based and semantic searches.

        context_contents = []
        context_sources = []
        context_sources_description = []
        for result in ranked_semantic_search_results:
            context_sources.append(result[2]["source_url"])
            context_source_description = "- {} ({})".format(
                result[2]["scientific_name"], result[2]["source_url"]
            )
            context_sources_description.append(context_source_description)

            scientific_name = result[2]["scientific_name"]
            common_names = result[2]["common_names"]
            semantic_score = f"{result[1]:.2f}"
            content_chunk:str = result[2]["content_chunk"]
            context_contents.append(
                {
                    "related_specie": scientific_name,
                    "common_names": common_names,
                    "content": content_chunk,
                }
            )

        print("# Semantic Search Result Citations:")
        print("\n".join(set(context_sources_description)))

        # Grouping logic
        grouped = defaultdict(list)

        for item in context_contents:
            key = (item["related_specie"], item.get("common_names") or None)
            grouped[key].append(item["content"])

        # Building the final structure
        context_contents_result = []
        for (related_specie, common_names), contents in grouped.items():
            entry = OrderedDict()
            entry["related_specie"] = related_specie
            if common_names:
                entry["common_names"] = common_names
            entry["contents"] = contents
            context_contents_result.append(entry)

        print(f'# Knowledge Consolidated On {len(context_contents_result)} Items')
        knowledge = json.dumps(context_contents_result, ensure_ascii=False, indent=2)
        stream_llama3_response(query, knowledge)


def stream_llama3_response(user_prompt, knowledge):
    system_prompt_template = """You are a specialized scientific research assistant. Your task is to answer user queries using only the information provided between the [KNOWLEDGE] and [/KNOWLEDGE] tags. Do not incorporate any external knowledge or assumptions.

[KNOWLEDGE]
{knowledge}
[/KNOWLEDGE]

If the provided knowledge is insufficient to accurately answer the query, respond with: "I'm not sure" or "The provided information is insufficient to answer that question."

Keep your responses concise, precise, and strictly based on the given information."""

    system_prompt = system_prompt_template.format(knowledge=knowledge)
    print(f"# System Prompt:\n{system_prompt}")
    print(f"# User Message: {user_prompt}")

    url = "http://localhost:11434/api/chat"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": os.getenv("OLLAMA_MODEL_NAME"),
        "stream": True,
        "options": {
            "temperature": float(os.getenv("OLLAMA_MODEL_TEMPERATURE")),
        },
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    response = requests.post(url, json=payload, headers=headers, stream=True)

    print("# Assistant Response:")
    for line in response.iter_lines():
        if line:
            try:
                chunk = line.decode("utf-8")
                if chunk.startswith("data: "):
                    chunk = chunk[6:]
                data = json.loads(chunk)
                print(data.get("message", {}).get("content", ""), end="", flush=True)
            except Exception as e:
                print(f"\n[Error processing stream chunk]: {e}", flush=True)
    print()


if __name__ == "__main__":
    main()
