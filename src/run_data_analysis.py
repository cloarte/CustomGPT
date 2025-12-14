from repositories import CabiSpeciesRepository 

def main():
    cabi_species_repository = CabiSpeciesRepository()
    cabi_species = cabi_species_repository.get_all_species()
    print("# CabiSpecies total count", len(cabi_species))
    print()

    print("# CabiSpecies by Source URL")
    not_found_source_urls = []
    for cabi_specie in cabi_species:
        cabi_specie.content = cabi_species_repository.get_cabi_specie_content_by_source_url(cabi_specie.source_url)
        if not cabi_specie.content:
            not_found_source_urls.append(cabi_specie.source_url)

    cabi_specie_with_content = [cabi_specie for cabi_specie in cabi_species if cabi_specie.content]
    print("## CabiSpecie with content", len(cabi_specie_with_content))
    print("## MaxLenght content:", max([len(cabi_specie.content) for cabi_specie in cabi_specie_with_content]))
    print("## MinLenght content:", min([len(cabi_specie.content) for cabi_specie in cabi_specie_with_content]))
    print("## CabiSpecie object with largest content:", max(cabi_specie_with_content, key=lambda x: len(x.content)).scientific_name)
    
    print()

    print("# CabiSpecies by Scientific Name")
    not_found_scientific_names = []
    for cabi_specie in cabi_species:
        cabi_specie.content = cabi_species_repository.get_cabi_specie_content_by_scientific_name(cabi_specie.scientific_name)
        if not cabi_specie.content:
            not_found_scientific_names.append(cabi_specie.scientific_name)

    cabi_specie_with_content = [cabi_specie for cabi_specie in cabi_species if cabi_specie.content]
    print("## CabiSpecie with content", len(cabi_specie_with_content))
    print("## MaxLenght content:", max([len(cabi_specie.content) for cabi_specie in cabi_specie_with_content]))
    print("## MinLenght content:", min([len(cabi_specie.content) for cabi_specie in cabi_specie_with_content]))
    print("## CabiSpecie object with largest content:", max(cabi_specie_with_content, key=lambda x: len(x.content)).scientific_name)    

    print()
    print('# Writing not found source urls to disk...')
    with open('data/not_found_urls.txt', 'w') as f:
        for url in not_found_source_urls:
            f.write(url + '\n')

    print('# Writing not found source urls to disk... done')
    print('# Writing not found scientific names to disk...')
    with open('data/not_found_scientific_names.txt', 'w') as f:
        for name in not_found_scientific_names:
            f.write(name + '\n')
    print('# Writing not found scientific names to disk... done')
    
if __name__ == "__main__":
    main()
