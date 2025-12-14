import os
from repositories import SpeciesRepository, CabiSpeciesRepository, SpeciesNewsRepository
from models import Plague

class PlagueService():
    def __init__(self):
        self.species_repository = SpeciesRepository()
        self.cabi_species_repository = CabiSpeciesRepository()
        self.species_news_repository = SpeciesNewsRepository()

        if not os.path.exists("data/invalid_content"):
            os.makedirs("data/invalid_content", exist_ok=True)

    def __log_invalid_species_content(self, species_list, file_path):
        invalid_names = [
            specie.scientific_name
            for specie in species_list
            if not isinstance(specie.content, str) or not specie.content.strip()
        ]
        with open(file_path, "w", encoding="utf-8") as f:
            for name in invalid_names:
                f.write(name + "\n")

    def get_plagues(self):
        # Get all Cabi Species
        cabi_species = self.cabi_species_repository.get_all_cabi_species()
        print("# Cabi Species Count:", len(cabi_species))
        for cabi_specie in cabi_species:
            cabi_specie.content = (
                self.cabi_species_repository.get_cabi_specie_content_by_scientific_name(
                    cabi_specie.scientific_name
                )
            )
        cabi_species_with_content = [
            cabi_specie for cabi_specie in cabi_species
            if isinstance(cabi_specie.content, str) and cabi_specie.content.strip()
        ]
        self.__log_invalid_species_content(cabi_species, "data/invalid_content/invalid_cabi_species.txt")
        print(
            f"# Total elements from Cabi Species with content: {len(cabi_species_with_content)}"
        )

        # Get all Species
        species = self.species_repository.get_all_species()
        print("# Species Count:", len(species))
        for specie in species:
            specie.content = (
                self.species_repository.get_cabi_specie_content_by_source_url(
                    specie.source_url
                )
            )
        species_with_content = [
            specie for specie in species
            if isinstance(specie.content, str) and specie.content.strip()
        ]
        self.__log_invalid_species_content(species, "data/invalid_content/invalid_species.txt")
        print(
            f"# Total elements from Species with content: {len(species_with_content)}"
        )

        # Get all Species News
        species_news = self.species_news_repository.get_all_species_news()
        print("# Species News Count:", len(species_news))
        for specie in species_news:
            specie.content = (
                self.species_news_repository.get_news_article_content_by_source_url(
                    specie.source_url
                )
            )
        species_news_with_content = [
            specie_new for specie_new in species_news
            if isinstance(specie_new.content, str) and specie_new.content.strip()
        ]
        self.__log_invalid_species_content(species_news, "data/invalid_content/invalid_species_news.txt")
        print(
            f"# Total elements from Species News with content: {len(species_news_with_content)}"
        )

        cabi_species_list = [Plague(cabi_specie.scientific_name, cabi_specie.common_names, cabi_specie.source_url, cabi_specie.content, "Es cuarentenanaria" if cabi_specie.is_quarantine else "No es cuarentenanaria") for cabi_specie in cabi_species_with_content]
        species_list = [Plague(specie.scientific_name, specie.common_names, specie.source_url, specie.content, "-") for specie in species_with_content]
        species_news_list = [Plague(specie_new.scientific_name, None, specie_new.source_url, specie_new.content, "Es cuarentenanaria" if specie_new.is_quarantine else "No es cuarentenanaria") for specie_new in species_news_with_content]

        cabi_species_list.extend(species_list)
        cabi_species_list.extend(species_news_list)
        return cabi_species_list