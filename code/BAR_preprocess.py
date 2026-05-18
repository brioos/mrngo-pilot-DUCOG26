import pandas as pd
import openpyxl
import glob
from huggingface_hub import hf_hub_download
import fasttext
import floret
import numpy as np
import csv, sys
from deep_translator import GoogleTranslator

#%% READ-IN

BAR_folder = "../data/BAR/"
BAR_output = "../derivatives/BAR_preporcessed.xlsx"
BAR_output_participant = "../derivatives/BAR/"

BAR_concepts = pd.read_csv(BAR_folder + "concept_id_mapping.csv", delimiter=";")
BAR_concepts_dict = {concept["id"]: concept["concept"] for conceptid, concept in BAR_concepts.iterrows()}

model_path = hf_hub_download(
    repo_id="huspacy/hu_vectors_web_lg",
    filename="floret/floret_vectors.bin"
)
HUN_model = floret.load_model(model_path)
HUN_translator = GoogleTranslator(source="hu", target="en")

EN_concepts_df = pd.read_excel("../data/MRNGO_concepts_final.xlsx")
EN_concepts_dict = {item["item_HU"]:item["item_EN"] for itemrow, item in EN_concepts_df.iterrows()}

#%% HELPERS

def get_text_vector(text):
    text = str(text).strip()

    if text == "" or text.lower() == "-":
        return None

    # floret should usually support this, and it is better for multi-word responses
    if hasattr(HUN_model, "get_sentence_vector"):
        return HUN_model.get_sentence_vector(text)

    # fallback: average word vectors
    words = text.split()
    if len(words) == 0:
        return None

    word_vectors = np.array([HUN_model.get_word_vector(word) for word in words])
    return word_vectors.mean(axis=0)


def get_cosine_similarity(vector1, vector2):
    if vector1 is None or vector2 is None:
        return pd.NA

    norm1 = np.linalg.norm(vector1)
    norm2 = np.linalg.norm(vector2)

    if norm1 == 0 or norm2 == 0:
        return pd.NA

    similarity = np.dot(vector1, vector2) / (norm1 * norm2)

    return float(similarity)


#%% MAIN
BAR_rows = []
## Read data files in loop
for bar_data in glob.glob(BAR_folder + "*.csv"):
    if "concept_id_mapping.csv" in bar_data:
        continue
    
    # Read single file
    bar_df = pd.read_csv(bar_data)
    mrngo_id = bar_data.split("/")[-1].split("\\")[-1].split("_")[0]
    BAR_participant_rows = []
    
    #Loop trials
    trial_concept = "start"
    listno = 0
    training_found = False
    for bar_trialno, bar_trial in bar_df.iterrows():
        if not training_found:
            if pd.notna(bar_trial["main_yesno_response.started"]):
                training_found = True
            else:
                continue      
        
        trial_no = bar_trial["trialno"]
        trial_feature = bar_trial["feature_name"]
        trial_conceptno = bar_trial["concPathMain"].split("/")[1]
        
        if trial_concept != BAR_concepts_dict[trial_conceptno]:
            print(trial_concept, BAR_concepts_dict[trial_conceptno], listno)
            listno += 1
        
        trial_concept = BAR_concepts_dict[trial_conceptno]
        trial_concept_EN = EN_concepts_dict[trial_concept]
        trial_duration = bar_trial["fixDuration"]
        
        if pd.isna(trial_no):
            continue
        
        # get response
        if not pd.isna(bar_trial["typed_text"]):   
            trial_responded = 1
            trial_response = bar_trial["typed_text"]
            trial_response_EN = translated = HUN_translator.translate(trial_response)
        elif not pd.isna(bar_trial["textbox_response_main.text"]):
            trial_response = bar_trial["textbox_response_main.text"]
            trial_response_EN = HUN_translator.translate(trial_response)
            trial_responded = 1
        else:
            trial_response = pd.NA
            trial_response_EN = pd.NA
            trial_responded = 0
        
        # get cosine
        if trial_responded == 1:
            trial_concept_vector = get_text_vector(trial_concept)
            trial_response_vector = get_text_vector(trial_response)
            trial_similarity = get_cosine_similarity(trial_concept_vector, trial_response_vector)
        else:
            trial_similarity = pd.NA
            
        trial_dict = {
            "ID": mrngo_id,
            "listno": listno,
            "trialno": trial_no,
            "feature": trial_feature,
            "conceptno": trial_conceptno,
            "concept": trial_concept_EN,
            "concept_HU": trial_concept,
            "duration": trial_duration,
            "responded": trial_responded,
            "response": trial_response_EN,
            "response_HU": trial_response,
            "similarity": trial_similarity
        }  
        
        BAR_rows.append(trial_dict)    
        BAR_participant_rows.append(trial_dict)
    
    #ID preproc
    BAR_participant_preproc_df = pd.DataFrame(BAR_participant_rows)
    BAR_participant_preproc_df.to_excel(BAR_output_participant + mrngo_id + "_preprocessed.xlsx", index=False)

#Sum preproc
BAR_preproc_df = pd.DataFrame(BAR_rows)
BAR_preproc_df.to_excel(BAR_output, index=False)