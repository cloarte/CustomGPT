from db import PostgresSession, MongoSession

from entities import CabiSpecie


class CabiSpeciesRepository:
    def __init__(self):
        self.cabi_scraper_collection = MongoSession["cabi_scraper"]

    def get_cabi_specie_content_by_scientific_name(self, scientific_name) -> str:
        documents: list[dict] = list(
            self.cabi_scraper_collection.find(
                {"nombre_cientifico": scientific_name},
                {
                    "contenido": True,
                },
            ).limit(1)
        )

        if not documents:
            return ""
        else:
            return documents[0].get("contenido")

    def get_all_cabi_species(self) -> list[CabiSpecie]:
        return PostgresSession.query(CabiSpecie).all()
