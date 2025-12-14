from keybert import KeyBERT
from sentence_transformers import SentenceTransformer


class QueryProcessor:
    def __init__(self, keyword_model_name):
        self.model = SentenceTransformer(keyword_model_name, trust_remote_code=True)
        self.kw_model = KeyBERT(model=self.model)

    def extract_keywords(self, query: str, seed_keywords: str, ngram_range: tuple = (2, 4)) -> str:
        keywords = self.kw_model.extract_keywords(
            query, keyphrase_ngram_range=ngram_range, stop_words=None, use_mmr=True, seed_keywords=seed_keywords
        )
        return ", ".join([kw[0] for kw in keywords])
