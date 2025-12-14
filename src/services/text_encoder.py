from typing import List, Tuple

import torch
from transformers import AutoTokenizer, AutoModelForMaskedLM
from sentence_transformers import SentenceTransformer
from transformers import logging as hf_logging
hf_logging.set_verbosity_error()

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print('# Available device:', device)

class TextEncoder:
    def __init__(
        self,
        sparse_model_name: str,
        dense_model_name: str,
    ):
        self.sparse_tokenizer = None
        self.sparse_model = None
        self.dense_model = None
        self.sparse_model_name = sparse_model_name
        self.dense_model_name = dense_model_name

    def encode_sparse(self, text: str) -> Tuple[List[int], List[float]]:
        if self.sparse_model is None:
            self.sparse_tokenizer = AutoTokenizer.from_pretrained(self.sparse_model_name)
            self.sparse_model = AutoModelForMaskedLM.from_pretrained(self.sparse_model_name)
            self.sparse_model.to(device)
            print(f"# Sparse model loaded on device: {device}")

        encoded_inputs = self.sparse_tokenizer(
            text, padding=True, truncation=True, return_tensors="pt"
        ).to(device)
        with torch.no_grad():
            logits = self.sparse_model(**encoded_inputs).logits
            max_activations = torch.max(torch.nn.functional.relu(logits), dim=1)[0]
        indices = max_activations.nonzero(as_tuple=True)[1].tolist()
        values = max_activations[0, indices].tolist()
        return indices, values

    def encode_dense(self, text: str, task:str) -> List[float]:
        if self.dense_model is None:
            self.dense_model = SentenceTransformer(self.dense_model_name, trust_remote_code=True)
            print(f"# Dense model loaded on device: {self.dense_model.device}")
        return self.dense_model.encode(text, task=task, prompt_name=task).tolist()

    def get_dense_embedding_size(self) -> int:
        return len(self.encode_dense("Hello World", 'retrieval.passage'))
