from db import PostgresSession, MongoSession
from typing import Dict, List

from entities import Specie


class SpeciesRepository:
    def __init__(self):
        self.url_scraper_collection = MongoSession["urls_scraper"]

    def get_cabi_specie_content_by_source_url(self, source_url) -> str:
        documents: list[Dict] = list(
            self.url_scraper_collection.find(
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

    def get_all_species(self) -> List[Specie]:
        return PostgresSession.query(Specie).all()
