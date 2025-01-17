import json
import re

# Load the features. We will use the 'summary_stats' to get the pltaform/ins couples & models
all_features_loc = ['../../CMR_Queries/cmr_results/forward_gesdisc/forward_gesdisc_features_rerun_all.json',
                    '../../CMR_Queries/cmr_results/giovanni/giovanni_papers_features.json',
                    '../../CMR_Queries/cmr_results/aura_mls/_v1_features.json',
                    '../../CMR_Queries/cmr_results/aura-omi/3-22-15-Aura_omi_features.json']

unique_couples, unique_models = set(), set()

for feature_loc in all_features_loc:
    with open(feature_loc, encoding='utf-8') as f:
        features_data = json.load(f)
    print(feature_loc)
    # list of all valid sources from GES DISC website. Extracted from 'Refine By' sidebar on right side
    with open('valid_sources.json') as f:
        valid_sources = json.load(f)

    # FInd unique couples and models
    for pdf_key, feature in features_data.items():
        summary_stats = feature['summary_stats']
        platform_ins_couples = summary_stats['valid_couples']
        for pic in platform_ins_couples:
            pic = re.sub(r'----level[\- ]\d', '', pic)
            unique_couples.add(pic)
        models = summary_stats['models']
        for mod in models:
            unique_models.add(mod)


# Code to generate a reviewable baseline dictionary to use for plat/ins couples. Manually removed a few afterward
edward_couples_to_source_couples = {}
for couple in unique_couples:
    words = ' '.join(couple.split('/', maxsplit=1))
    match_found = False
    for vs in valid_sources:
        temp = [w for w in words.split()]
        word_occurrences = [w in vs.lower() for w in words.split()]
        if all(word_occurrences):
            print(couple, vs)
            match_found = True
            edward_couples_to_source_couples[couple] = vs
    if not match_found:
        print(couple, "no match found")

with open('models_to_source_models.json', 'w', encoding='utf-8') as f:
    json.dump(edward_couples_to_source_couples, f, indent=4)

# Code to generate a reviewable baseline dictionary to use for Models. Manually removed a few afterward
edward_models_to_source_couples = {}
for model in unique_models:
    words = 'models/analyses ' + model
    match_found = False
    for vs in valid_sources:
        temp = [w for w in words.split()]
        word_occurrences = [w in vs.lower() for w in words.split()]
        if all(word_occurrences):
            print(model, vs)
            match_found = True
            edward_models_to_source_couples[model] = vs
    if not match_found:
        print(model, "no match found")

with open('couples_to_source_couples.json', 'w', encoding='utf-8') as f:
    json.dump(edward_models_to_source_couples, f, indent=4)
