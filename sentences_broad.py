import csv
import re
import json
from collections import defaultdict
import itertools
import pprint
import glob
from tqdm import tqdm

from config import params

# This code will produce the notes that are entered into Zotero. Each note contains an exact text match with a
# mission/instrument and variable pair or with a match with one of the exceptions. The exceptions include all datasets
# labeled with the Microwave limb sounder and each of the data models.


# Extracts the variables from the mission, instrument, and variable csvs. This will extract both the short names and
# the long names. It will output a list of all missions, variables and instruments and all the potential pairs
# The aliases dictionaries contain mapping from short name to long name and the main dictionaries contain a mapping from
# long name to short name
"""
create list of mission, instrument, and variables and create dictionaries mapping from short->long and long->short
"""


# convert everything to short names. ie: water vapor -> h2o
def standardize(mission, instrument, variable):
    for index, m in enumerate(mission):
        if m in aliases["mission_aliases"]:
            mis = aliases["mission_aliases"][m].lower()
            mission[index] = mis

    for index, ins in enumerate(instrument):
        if ins in aliases["instrument_aliases"]:
            ins = aliases["instrument_aliases"][ins]
            instrument[index] = ins

    for index, v in enumerate(variable):
        if v in aliases["var_aliases"]:
            var = aliases["var_aliases"][v]
            variable[index] = var

    return mission, instrument, variable


# This will output the potential tags. It simply takes the possible permutations of the missions, instruments and variables
# and outputs all the possible permutations of each that occur. Note again that MLS implies the aura satellite
def get_tags(mission, instrument, variable, aliases):
    tags = []
    completed = []
    for perm in itertools.product(*[mission, instrument, variable]):
        if perm in completed:
            continue
        else:
            completed.append(perm)

        if perm[0] in aliases["mission_aliases"]:
            mis = aliases["mission_aliases"][perm[0]].lower()
        elif perm[0] in aliases["mission_main"]:
            mis = perm[0]
        else:
            mis = perm[0]

        if perm[1] in aliases["instrument_aliases"]:
            ins = aliases["instrument_aliases"][perm[1]]
        elif perm[1] in aliases["instrument_main"]:
            ins = perm[1]
        else:
            ins = perm[1]

        if perm[2] in aliases["var_aliases"]:
            var = aliases["var_aliases"][perm[2]]
        elif perm[2] in aliases["var_main"]:
            var = perm[2]
        else:
            var = perm[2]

        # if mis == "mls" or mis == "microwave limb sounder":
        #     mis = "aura"
        if (mis + "/" + ins, var) not in tags:
            tags.append((mis + "/" + ins, var))
    return tags


def load_in_GES_parameters():
    # As created in produce_notes.py
    with open("data/json/aliases.json") as jsonfile:
        aliases = json.load(jsonfile)

    with open('data/json/GES_missions.json') as jsonfile:
        missions = json.load(jsonfile)

    with open('data/json/GES_instruments.json') as jsonfile:
        instruments = json.load(jsonfile)

    with open('data/json/variables.json') as jsonfile:
        variables = json.load(jsonfile)

    with open('data/json/exceptions.json') as jsonfile:
        exceptions = json.load(jsonfile)

    return aliases, missions, instruments, variables, exceptions


def is_ordered_subset(subset, sentence):
    sub = subset.split(" ")
    lst = sentence.split(" ")
    ln = len(sub)
    for i in range(len(lst) - ln + 1):
        if all(sub[j] == lst[i + j] for j in range(ln)):
            return True
    return False


def label_important_pieces(mission, instrument, variable, exception, sentence, data, tag=None):
    if tag is None:
        tag = "(" + mission + '/' + instrument + ',' + variable + ")"
    data[tag].append({
        "mission": mission,
        "instrument": instrument,
        "variable": variable,
        "exception": exception,
        "sentence": sentence
    })


# This function takes the text of a preprocessed txt document and outputs the notes. Each note contains all
# the notes for each (mission/instrument, variable) tuple. It also passes through the aliases used in this file
# The output format is a dictionary with key = (mission/instrument, variable) and value = list of sentences with matches
def jacob_produce_notes(text, aliases, missions, instruments, variables, exceptions):
    text = re.sub("[\(\[].*?[\)\]]", "",
                  text)  # I think this is to remove the citations. Does this also not remove like Global Position System (GPS)
    text = re.sub("\n", " ", text)
    text = re.sub("- ", "", text)
    text = re.sub("/", " ", text)

    data = defaultdict(list)

    for s in text.split("."):
        mission = []
        instrument = []
        var = []
        exception = []

        for e in exceptions:
            if is_ordered_subset(e, s.lower()):
                exception.append(e)

        for m in missions:
            if is_ordered_subset(m, s.lower()):
                mission.append(m)
        if not mission and not exception:  # keep going: if mission or exception
            continue
        for i in instruments:
            if is_ordered_subset(i, s.lower()):
                instrument.append(i)
        if not instrument and not exception:  # keep going: if instrument or exception
            continue
        for v in variables:
            if is_ordered_subset(v, s.lower()):
                var.append(v)
        if not var and not exception:  # keep going: if var or exception
            continue

        for tag in get_tags(mission, instrument, var, aliases):
            data[tag].append({
                "sentence": s,
                "mission": tag[0].split("/")[0],
                "instrument": tag[0].split("/")[1],
                "variable": tag[1],
                "exception": False
            })

        for e in exception:
            if e in aliases["exception_aliases"]:
                e = aliases["exception_aliases"][e]
            data[(e, "none")].append({
                "sentence": s,
                "mission": False,
                "instrument": False,
                "variable": False,
                "exception": e
            })

    return data


def produce_notes(text, aliases, missions, instruments, variables, exceptions, debug=False):
    text = re.sub("[\(\[].*?[\)\]]", "", text)  # I think this is to remove the citations. Does this also not remove like Global Position System (GPS)
    text = re.sub("\n", " ", text)
    text = re.sub("- ", "", text)
    text = re.sub("/", " ", text)

    data = defaultdict(list)

    for s in text.split("."):
        s = s.strip()
        mission = []
        instrument = []
        var = []
        exception = []

        for e in exceptions:
            if is_ordered_subset(e, s.lower()):
                exception.append(e)

        for m in missions:
            if is_ordered_subset(m, s.lower()):
                mission.append(m)

        for i in instruments:
            if is_ordered_subset(i, s.lower()):
                instrument.append(i)

        for v in variables:
            if is_ordered_subset(v, s.lower()):
                var.append(v)
        if mission is None and instrument is None and var is None and exception is None:  # None of them found
            continue


        mission, instrument, variable = standardize(mission, instrument, var)

        if debug:
            print(s)
            print(mission)
            print(instrument)
            print(var)

        if mission and instrument and var:
            for perm in itertools.product(*[mission, instrument, variable]):
                label_important_pieces(perm[0], perm[1], perm[2], False, s, data)
        # elif mission and instrument:
        #     for perm in itertools.product(*[mission, instrument]):
        #         label_important_pieces(perm[0], perm[1], 'None', False, s, data)
        # elif mission and var:
        #     for perm in itertools.product(*[mission, variable]):
        #         label_important_pieces(perm[0], 'None', perm[1], False, s, data)
        # elif instrument and var:
        #     for perm in itertools.product(*[instrument, variable]):
        #         label_important_pieces('None', perm[0], perm[1], False, s, data)

        for e in exception:
            if e in aliases["exception_aliases"]:
                e = aliases["exception_aliases"][e]
            data[(e, "none")].append({
                "mission": False,
                "instrument": False,
                "variable": False,
                "exception": e,
                "sentence": s,
            })

    return data


def add_to_csv(d, paper_name):
    csv_columns = ['paper', 'mission', 'instrument', 'variable', 'exception', 'sentence']
    csv_text = ""
    csv_text += "\n\n" + ",".join(csv_columns) + "\n"
    csv_text += paper_name
    for key in d.keys():
        # csv_text += str(key) + ',\n'
        for value in d[key]:
            csv_text += ","  # b/c we are leaving the paper column blank
            csv_text += str(value['mission']) + ","
            csv_text += str(value['instrument']) + ","
            csv_text += str(value['variable']) + ","
            csv_text += str(value['exception']) + ","
            sentence = value['sentence'] + "\n"
            sentence = re.sub(r',', '', sentence)
            csv_text += sentence + "\n"

    return csv_text


'''
todo: Missions has MLS + Microwave Limb Sounder. Why?
'''

if __name__ == '__main__':
    use_jacob_method = False
    use_all = True
    one_sentence_test = False

    preprocessed_directory = 'data/cermine_results/cermzones_preprocess/'
    output_directory = 'data/cermine_results/cermzones_sentences/'
    csv_results = ""

    aliases, missions, instruments, variables, exceptions = load_in_GES_parameters()

    if one_sentence_test:

        sentence = 'The Earth Observing System Microwave Limb Sounder (MLS) aboard the NASA Aura satellite provides a homogeneous, near-global (82°N to 82°S) observational data set of many important trace species, including water vapor in the UTLS'
        data = produce_notes(sentence, aliases, missions, instruments, variables, exceptions, debug=True)
        csv_results += add_to_csv(data, sentence)

        print(csv_results)

        import sys
        sys.exit()

    elif not use_all:
        file = 'Dolinar et al. - 2016 - A clear-sky radiation closure study using a one-di.txt'
        with open(preprocessed_directory + file, encoding='utf-8') as f:
            txt = f.read()

        if use_jacob_method:
            data = jacob_produce_notes(txt, aliases, missions, instruments, variables, exceptions)
            csv_results += add_to_csv(data, file)
            with open('output_directory' + 'JACOB' + file, 'w') as f:
                f.write(csv_results)
            import sys
            sys.exit()

        data = produce_notes(txt, aliases, missions, instruments, variables, exceptions)
        csv_results += add_to_csv(data, file)
    else:
        for file in tqdm(glob.glob(preprocessed_directory + "*.txt")):
            file_name = file.split("\\")[-1]
            print(file_name)
            with open(file, encoding='utf-8') as f:
                txt = f.read()

            data = produce_notes(txt, aliases, missions, instruments, variables, exceptions)
            csv_results += add_to_csv(data, file_name)

            with open(output_directory + file_name + ".csv", 'w') as f:
                f.write(csv_results)
                csv_results = ""
    '''
    sample results
    Data: 
    ('aura/mls', 'h2o') [{'sentence': ' in this study, we evaluate the modern-era retrospective analysis for research and applications version 2  reanalyzed clear-sky temperature and water vapor profiles with newly generated atmospheric profiles from department of energy atmospheric radiation measurement -merged soundings and aura microwave limb sounder retrievals at three arm sites', 'mission': 'aura', 'instrument': 'mls', 'variable': 'h2o', 'exception': False}, {'sentence': ' mls water vapor is retrieved at a frequency of 190 ghz with acceptable range of 316–0', 'mission': 'aura', 'instrument': 'mls', 'variable': 'h2o', 'exception': False}, {'sentence': ' the estimated uncertainty of mls water vapor in the stratosphere is ~10%', 'mission': 'aura', 'instrument': 'mls', 'variable': 'h2o', 'exception': False}, {'sentence': ' the black line represents the hybrid profiles from the arm-merged soundings  and the microwave limb sounder  for atmospheric temperature and water vapor', 'mission': 'aura', 'instrument': 'mls', 'variable': 'h2o', 'exception': False}]
    ('aura/mls', 't') [{'sentence': ' in this study, we evaluate the modern-era retrospective analysis for research and applications version 2  reanalyzed clear-sky temperature and water vapor profiles with newly generated atmospheric profiles from department of energy atmospheric radiation measurement -merged soundings and aura microwave limb sounder retrievals at three arm sites', 'mission': 'aura', 'instrument': 'mls', 'variable': 't', 'exception': False}, {'sentence': ' the black line represents the hybrid profiles from the arm-merged soundings  and the microwave limb sounder  for atmospheric temperature and water vapor', 'mission': 'aura', 'instrument': 'mls', 'variable': 't', 'exception': False}]
    ('merra/mls', 'h2o') [{'sentence': ' in this study, we evaluate the modern-era retrospective analysis for research and applications version 2  reanalyzed clear-sky temperature and water vapor profiles with newly generated atmospheric profiles from department of energy atmospheric radiation measurement -merged soundings and aura microwave limb sounder retrievals at three arm sites', 'mission': 'merra', 'instrument': 'mls', 'variable': 'h2o', 'exception': False}]
    ('merra/mls', 't') [{'sentence': ' in this study, we evaluate the modern-era retrospective analysis for research and applications version 2  reanalyzed clear-sky temperature and water vapor profiles with newly generated atmospheric profiles from department of energy atmospheric radiation measurement -merged soundings and aura microwave limb sounder retrievals at three arm sites', 'mission': 'merra', 'instrument': 'mls', 'variable': 't', 'exception': False}]
    ('merra', 'none') [{'sentence': ' in this study, we evaluate the modern-era retrospective analysis for research and applications version 2  reanalyzed clear-sky temperature and water vapor profiles with newly generated atmospheric profiles from department of energy atmospheric radiation measurement -merged soundings and aura microwave limb sounder retrievals at three arm sites', 'mission': False, 'instrument': False, 'variable': False, 'exception': 'merra'}, {'sentence': ' in this study, temperature and water vapor profiles from modern-era retrospective analysis for research and applications version 2 , along with the climatic aerosol optical depths over the three arm sites, are used as input to the radiative transfer model to calculate the clear-sky surface and toa radiative fluxes', 'mission': False, 'instrument': False, 'variable': False, 'exception': 'merra'}, {'sentence': ' a new version of merra has been released with several major improvements, making it the centerpiece of the evaluation performed in this study', 'mission': False, 'instrument': False, 'variable': False, 'exception': 'merra'}, {'sentence': ' this is in contrast to the one and a half million observations assimilated in merra from 2002 to the present', 'mission': False, 'instrument': False, 'variable': False, 'exception': 'merra'}]
    ('merra-2', 'none') [{'sentence': ' the temperature profiles are well replicated in merra-2 at all three sites, whereas tropospheric water vapor is slightly dry below ~700 hpa', 'mission': False, 'instrument': False, 'variable': False, 'exception': 'merra-2'}, {'sentence': ' the first objective of this study is to evaluate the merra-2 clear-sky temperature and water vapor profiles using a newly generated atmospheric profile data set', 'mission': False, 'instrument': False, 'variable': False, 'exception': 'merra-2'}, {'sentence': ' section 2 documents the groundand satellite-based data sets used in this study, as well as several of the notable updates in the recently released merra-2 reanalysis', 'mission': False, 'instrument': False, 'variable': False, 'exception': 'merra-2'}, {'sentence': ' profiles of atmospheric temperature, water vapor mixing ratio, and ozone mixing ratio have been generated from arm-merged sounding and satellite  retrievals over three arm sites, which are used to evaluate the merra-2 profiles', 'mission': False, 'instrument': False, 'variable': False, 'exception': 'merra-2'}, {'sentence': ' merra-2 is horizontally discretized on a cubed sphere grid, which is superior to the latitude-longitude methods used in earlier versions', 'mission': False, 'instrument': False, 'variable': False, 'exception': 'merra-2'}, {'sentence': ' for merra-2 the number of assimilated observations per 6 h increment has increased from three million in 2010 to five million in 2015; however, capabilities of assimilating future satellite observations are also developed', 'mission': False, 'instrument': False, 'variable': False, 'exception': 'merra-2'}, {'sentence': ' merra-2 is available on a 0', 'mission': False, 'instrument': False, 'variable': False, 'exception': 'merra-2'}, {'sentence': ' differences in the vertical profiles are expected since the merra-2 profiles cannot be perfectly collocated with the satellite ground-based data', 'mission': False, 'instrument': False, 'variable': False, 'exception': 'merra-2'}, {'sentence': ' the blue line is from the closest merra-2 grid point, and the red line is the midlatitude climatological mean', 'mission': False, 'instrument': False, 'variable': False, 'exception': 'merra-2'}, {'sentence': ' the hybrid and merra-2 water vapor mixing ratios match very well above ~850 hpa', 'mission': False, 'instrument': False, 'variable': False, 'exception': 'merra-2'}, {'sentence': ' however, below 850 hpa, the merra-2 water vapor profile diverges from the hybrid profile to the drier side \x002 g g', 'mission': False, 'instrument': False, 'variable': False, 'exception': 'merra-2'}, {'sentence': ' on the global scale, a moist bias in merra-2 can be up to 75–150% in the upper tropoby <0', 'mission': False, 'instrument': False, 'variable': False, 'exception': 'merra-2'}, {'sentence': ' the midlatitude climate mean water vapor mixing ratio is less than both the hybrid and merra-2 profiles in the lower troposphere ', 'mission': False, 'instrument': False, 'variable': False, 'exception': 'merra-2'}, {'sentence': ' temperature  is well reproduced in merra-2 at the twpc3 site through the troposphere; however, a slight discrepancy is seen just above the tropopause and below the stratopause, which could be an artifact of the coarser vertical resolution of merra-2', 'mission': False, 'instrument': False, 'variable': False, 'exception': 'merra-2'}, {'sentence': ' the tropical climate mean temperature agrees well with the hybrid and merra-2 profiles in the troposphere but is slightly warmer in the stratosphere and mesosphere', 'mission': False, 'instrument': False, 'variable': False, 'exception': 'merra-2'}, {'sentence': ' the twpc3 ozone comparison is similar to the results at the arm sgp and nsa sites, where the ozone profiles from merra-2 and the hybrid data set are very close', 'mission': False, 'instrument': False, 'variable': False, 'exception': 'merra-2'}, {'sentence': ' yet still, a noticeable discrepancy between the two data sets can be seen from ~10 to 20 hpa, where merra-2 is slightly smaller', 'mission': False, 'instrument': False, 'variable': False, 'exception': 'merra-2'}, {'sentence': ' the merra-2 atmospheric temperature profiles are nearly identical to the hybrid ones, and the climate mean temperature profiles agree with the hybrid ones within several kelvin', 'mission': False, 'instrument': False, 'variable': False, 'exception': 'merra-2'}, {'sentence': ' since mls ozone data are directly assimilated into merra-2, it is not surprising that the merra-2 and hybrid ozone profiles match extremely well at all three arm sites', 'mission': False, 'instrument': False, 'variable': False, 'exception': 'merra-2'}, {'sentence': ' most of the merra-2 water vapor mixing ratios agree well with the hybrid ones over three sites except for in the boundary layer at the arm twpc3', 'mission': False, 'instrument': False, 'variable': False, 'exception': 'merra-2'}, {'sentence': ' a bias of greater than \x0020 w m2 is found in the surface lw_dn flux using the hybrid and merra-2 profiles, a result that is inconsistent with long and turner  and is likely due to the skin temperature used in the rtm', 'mission': False, 'instrument': False, 'variable': False, 'exception': 'merra-2'}, {'sentence': ' vertical profiles of temperature at the three sites are well replicated in merra-2 when compared to the newly generated satellite surface-based  data set', 'mission': False, 'instrument': False, 'variable': False, 'exception': 'merra-2'}, {'sentence': ' finally, the merra-2 tropospheric water vapor mixing ratios are, on average, on the drier side of the combined satellite surfacebased data set at sgp and nsa for snow-free conditions', 'mission': False, 'instrument': False, 'variable': False, 'exception': 'merra-2'}, {'sentence': ' however, the relatively small and constant tropospheric water vapor profile at nsa for the snow cases is well replicated in merra-2', 'mission': False, 'instrument': False, 'variable': False, 'exception': 'merra-2'}]
    ('aura/mls', 'o3') [{'sentence': ' stratospheric ozone from mls is retrieved at a frequency of 240 ghz, which offers the best precision for a wide vertical range', 'mission': 'aura', 'instrument': 'mls', 'variable': 'o3', 'exception': False}, {'sentence': ' the recommended range of the mls ozone product is from 261 to 0', 'mission': 'aura', 'instrument': 'mls', 'variable': 'o3', 'exception': False}, {'sentence': ' the mls ozone product used for this study is also from version 4', 'mission': 'aura', 'instrument': 'mls', 'variable': 'o3', 'exception': False}, {'sentence': ' the ozone profile  is from the atmospheric infrared sounder  and mls', 'mission': 'aura', 'instrument': 'mls', 'variable': 'o3', 'exception': False}, {'sentence': ' since mls ozone data are directly assimilated into merra-2, it is not surprising that the merra-2 and hybrid ozone profiles match extremely well at all three arm sites', 'mission': 'aura', 'instrument': 'mls', 'variable': 'o3', 'exception': False}, {'sentence': ' since mls ozone is directly assimilated, the merra2 ozone mixing ratios are very close to the hybrid profiles at all three arm sites', 'mission': 'aura', 'instrument': 'mls', 'variable': 'o3', 'exception': False}]
    ('aura/airs', 'o3') [{'sentence': ' the ozone profile  is from the atmospheric infrared sounder  and mls', 'mission': 'aura', 'instrument': 'airs', 'variable': 'o3', 'exception': False}]
    ('merra-2/an', 't') [{'sentence': ' temperature  is well reproduced in merra-2 at the twpc3 site through the troposphere; however, a slight discrepancy is seen just above the tropopause and below the stratopause, which could be an artifact of the coarser vertical resolution of merra-2', 'mission': 'merra-2', 'instrument': 'an', 'variable': 't', 'exception': False}]
    ('merra-2/mls', 'o3') [{'sentence': ' since mls ozone data are directly assimilated into merra-2, it is not surprising that the merra-2 and hybrid ozone profiles match extremely well at all three arm sites', 'mission': 'merra-2', 'instrument': 'mls', 'variable': 'o3', 'exception': False}]

    '''
