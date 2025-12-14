from db import EntityBase
from sqlalchemy import Column, String, Boolean


class SpecieNew(EntityBase):
    __tablename__ = "species_news"

    scientific_name = Column(String, nullable=False, primary_key=True)
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
                    self.scientific_name
                ],
            )
        )
