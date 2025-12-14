class Plague:
    scientific_name: str
    common_names: str
    content: str
    source_url: str
    keywords: str
    is_quarantine: str

    def __init__(self, scientific_name, common_names, source_url, content, is_quarantine):
        self.scientific_name = scientific_name
        self.common_names = common_names
        self.source_url = source_url
        self.content = content
        self.is_quarantine = is_quarantine
        self.keywords = ", ".join(
            filter(
                None,
                [self.scientific_name, self.common_names],
            )
        )
        
    def __repr__(self):
        return f"Plague(scientific_name={self.scientific_name}, common_names={self.common_names}, source_url={self.source_url}, content={self.content[0:50]}...)"