from CMR_Queries.manually_reviewed_utilities import *
from CMR_Queries.sentence_label_utilities import *
from datetime import datetime

'''
key: {
    key
    article_name
    file_name
    manually_reviewed_datasets
    summary stats
    CMR Queries
    Sentences
    *******************************    
    The sentences that contain at least one of the GES DISC instruments, platforms or models
    Summary statistics:
        Instrument/platform pair counts
        Single instrument, platform, model counts
        Derived dataset (from CMR) counts
    
    For each sentence:
        Extract instruments, platforms or models (either GES DISC or not) record them as matching instrument/platform pair if possible, otherwise as single features.
        Extract science keywords, and record them.
    For each instrument/platform pair:
        For each science keyword:
            Query CMR and record first returned dataset
    For reminder of instruments
        For each science keyword:
            Query CMR and record first returned dataset
            
}

'''

if __name__ == '__main__':

    # User Parameters
    preprocessed_directory = '../convert_using_cermzones/forward_gesdisc/preprocessed/'
    pubs_with_attchs_location = '../more_papers_data/forward_gesdisc_linkage/pubs_with_attchs_forward_ges.json'
    zot_notes_location = '../more_papers_data/forward_gesdisc_linkage/zot_notes_forward_ges.json'
    dataset_couples_location = '../data/json/datasets_to_couples.json'
    keyword_file_location = '../data/json/keywords.json'
    # keyword_file_location = 'keyword_optimization/keywords_regex_revised.json' #  try with the regex keywords
    mission_instrument_couples = '../data/json/mission_instrument_couples_LOWER.json'
    output_title = 'forward_gesdisc_'
    sort_by_usage = False  # sort CMR Queries by usage

    # determine manually reviewed datasets for the papers that were reviewed based on zotero notes file
    key_title_ground_truth = get_manually_reviewed_ground_truths(dataset_couples_location, pubs_with_attchs_location, zot_notes_location)

    # Generate Features and CMR results
    # if you don't want to actually run cmr queries (ie: you just want feature), you can set update_cmr=False
    sentences_stats_queries = run_keyword_sentences(keyword_file_location, mission_instrument_couples, preprocessed_directory, sort_by_usage=sort_by_usage)

    # add the date to the file name, so we don't accidentally overwrite stuff
    now = datetime.now()
    current_time = now.strftime("%H-%M-%S") + output_title

    with open(current_time + 'key_title_ground_truth.json', 'w', encoding='utf-8') as f:
        json.dump(key_title_ground_truth, f, indent=4)

    with open(current_time + 'features.json', 'w', encoding='utf-8') as f:
        json.dump(sentences_stats_queries, f, indent=4)

    # Merge the features and zotero information. Keep only the papers which were manually reviewed in the merged file
    for parent_key, value in key_title_ground_truth.items():
        pdf_key = value['pdf']
        if pdf_key in sentences_stats_queries:
            for inner_key, inner_value in sentences_stats_queries[pdf_key].items():
                value[inner_key] = inner_value

        key_title_ground_truth[parent_key] = value

    with open(current_time + 'features_merged.json', 'w', encoding='utf-8') as f:
        json.dump(key_title_ground_truth, f, indent=4)