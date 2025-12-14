from db import EntityBase
from sqlalchemy import Column, String, Boolean


class CabiSpecie(EntityBase):
    __tablename__ = "cabi_species"

    scientific_name = Column(String, nullable=False, primary_key=True)
    common_names = Column(String, nullable=False)
    distribution = Column(String, nullable=False)
    hosts = Column(String, nullable=False)
    source_url = Column(String, nullable=False)
    is_quarantine = Column(Boolean, nullable=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.content: str = ""  # Initialize content as an empty string

    @property
    def keywords(self) -> str:
        return ", ".join(
            filter(
                None,
                [
                    self.scientific_name,
                    self.common_names
                ],
            )
        )
