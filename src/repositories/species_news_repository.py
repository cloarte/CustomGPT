from db import PostgresSession, MongoSession
from typing import Dict, List

from entities import SpecieNew


class SpeciesNewsRepository:
    def __init__(self):
        self.news_article_collection = MongoSession["news_article"]

    def get_news_article_content_by_source_url(self, source_url) -> str:
        documents: list[Dict] = list(
            self.news_article_collection.find(
                {"source_url": source_url},
                {
                    "contenido": True,
                },
            ).limit(1)
        )

        if not documents:
            return ""
        else:
            return documents[0].get("contenido")

    def get_all_species_news(self) -> List[SpecieNew]:
        return PostgresSession.query(SpecieNew).all()
