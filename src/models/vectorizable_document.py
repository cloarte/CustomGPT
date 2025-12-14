from typing import Dict


class VectorizableDocument:
    def __init__(self, id: int, text: str, metadata: Dict[str, str]):
        self.id = id
        self.text = text
        self.metadata = metadata

    def __repr__(self):
        return f"VectorizableDocument(id={self.id}, text={self.text}, metadata={self.metadata})"