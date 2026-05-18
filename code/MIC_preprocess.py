import pandas as pd
import openpyxl
import glob
import numpy as np

# ----- author: Schvéger Domonkos -----
# ----- modifications: McFegan Rebecca -----
# ----- revision: Alex Ilyés -----

#%% READ-IN
BEHAV_notes = "../data/Behavioral-pilot-notes.xlsx"  # first row is skipped below
BEHAV_df = pd.read_excel(BEHAV_notes)
## MIC INFO!
BEHAV_dict = {
    behav["ParticipantID"]: {
        trialno: behav[trial_col]
        for trialno, trial_col in enumerate([
            f"Run{run}T{trial}"
            for run in [1, 2]
            for trial in range(1, 31)
            if f"Run{run}T{trial}" in BEHAV_df.columns
        ])
    }
    for behavno, behav in BEHAV_df.iterrows()
}

### DEMOGRAPHY export
DEM_rows = []
for mrngo_i, mrngo_pt in BEHAV_df.iterrows():
    # location
    if "ELTE" in mrngo_pt["Location"]:
        mrngo_loc = "ELTE"
    else:
        mrngo_loc = "TTK"
        
    # age
    birthdate = pd.to_datetime(mrngo_pt["Date of birth"])
    testdate = pd.to_datetime(mrngo_pt["Date"])
    if testdate < pd.to_datetime("2026-05-01"):
        version = 1
    else:
        version = 2
        
    mrngo_age_months = ((testdate.year - birthdate.year) * 12 + (testdate.month - birthdate.month) - int(testdate.day < birthdate.day))
    mrngo_age_years = (testdate.year - birthdate.year - int((testdate.month, testdate.day) < (birthdate.month, birthdate.day)))
    
    # rest
    mrngo_ID = mrngo_pt["ParticipantID"]
    mrngo_sex = mrngo_pt["Sex"]
    
    DEM_rows.append({
        "ID": mrngo_ID,
        "version": version,
        "sex": mrngo_sex,
        "age_year": mrngo_age_years,
        "age_months": mrngo_age_months,
        "location": mrngo_loc
    })
DEM_df = pd.DataFrame(DEM_rows)
DEM_df.to_excel("../derivatives/mrngo_demography.xlsx", index=False)
    

## MIC
MIC_folder = "../data/MIC/"
MIC_output = "../derivatives/MIC_preprocessed.xlsx"
MIC_output_participant = "../derivatives/MIC/"
MIC_file_pattern = "*_MIC_task_*.csv"
MIC_files_pattern = glob.glob(MIC_folder + MIC_file_pattern)
MIC_files_list = [MIC_file for MIC_file in MIC_files_pattern]
MIC_files = {m_comp[12:17]: [m_id for m_id in MIC_files_list if m_id[13:17] == m_comp[13:17]] for m_comp in MIC_files_list}

## Concepts map
MIC_concepts = MIC_folder + "concept-id-mapping.xlsx"
MIC_concepts_df = pd.read_excel(MIC_concepts)
MIC_concepts_dict = {colname: {trial["trial"]: trial[colname] for trialno, trial in MIC_concepts_df.iterrows()} for colname in MIC_concepts_df.columns[1:]}

EN_concepts_df = pd.read_excel("../data/MRNGO_concepts_final.xlsx")
EN_concepts_dict = {item["item_HU"]:item["item_EN"] for itemrow, item in EN_concepts_df.iterrows()}

#%% MAIN
MIC_rows = []

## Read data files in loop
for mrngo_id, mic_data_list in MIC_files.items():
    
    if len(mic_data_list) == 1:
        # Prep
        mic_df = pd.read_csv(mic_data_list[0])
    else:
        mic_df = pd.concat(
            [pd.read_csv(mic_data) for mic_data in mic_data_list],
            ignore_index=True
        )
        
        mic_df.loc[mic_df["run_loop.thisRepN"].notna(), "run_loop.thisRepN"] = pd.to_numeric(mic_df.loc[mic_df["run_loop.thisRepN"].notna(), "RunNo"]) - 1
    
    MIC_participant_rows = []
    MIC_trial_ranges = mic_df[mic_df["item_HU"].notna()].drop_duplicates(["run_loop.thisRepN", "item_HU"], keep="first").index.tolist()
    
    # Loop trials
    for MIC_trial_range in MIC_trial_ranges:
        MIC_trial_range_start = MIC_trial_range
        if MIC_trial_ranges.index(MIC_trial_range) == len(MIC_trial_ranges)-1:
            MIC_trial_range_end = len(mic_df)
        else:
            MIC_trial_range_end = MIC_trial_ranges[MIC_trial_ranges.index(MIC_trial_range)+1]
                
        # get run and trial data
        trial_run = mic_df.at[MIC_trial_range,"run_loop.thisRepN"]  
        trial_no = mic_df.at[MIC_trial_range,"trial_loop.thisTrialN"]
        trial_concept_HU = mic_df.at[MIC_trial_range,"item_HU"]
        trial_concept = EN_concepts_dict[trial_concept_HU]
        trial_conceptno = mic_df.at[MIC_trial_range,"itemno"]  
        
        # Get response if exist
        trial_df = mic_df.iloc[MIC_trial_range_start:MIC_trial_range_end+1].copy()
        trial_space_rows = trial_df[trial_df["key_resp.keys"].astype(str).str.strip() == "space"]
        trial_start_t = pd.to_numeric(mic_df.at[MIC_trial_range_start, "thisRow.t"])

        if len(trial_space_rows) > 0:
            trial_responded = 1
            # first space row only
            trial_response_row = trial_space_rows.index[0]
            trial_space_t = pd.to_numeric(mic_df.at[trial_response_row, "thisRow.t"])
            trial_segment_rt = mic_df.at[trial_response_row, "key_resp.rt"]
            if pd.isna(trial_segment_rt):
                trial_segment_rt = 0

            # real RT = elapsed time until the space-row + key RT within that row
            trial_rt = (trial_space_t - trial_start_t) + trial_segment_rt
  
        else:
            trial_responded = 0
            trial_rt = pd.NA
            
        # Get whether response was correct orn ot
        trial_correctness = BEHAV_dict[mrngo_id][MIC_trial_ranges.index(MIC_trial_range)]
        
        trial_dict = {
            "ID": mrngo_id,
            "run": trial_run+1,
            "trialno": trial_no+1,
            "conceptno": trial_conceptno,
            "concept": trial_concept,
            "concept_HU": trial_concept_HU,
            "responded": trial_responded,
            "rt": trial_rt,
            "correct": trial_correctness
        }  
        
        MIC_rows.append(trial_dict)    
        MIC_participant_rows.append(trial_dict)
    
    #ID preproc
    MIC_participant_preproc_df = pd.DataFrame(MIC_participant_rows)
    MIC_participant_preproc_df.to_excel(MIC_output_participant + mrngo_id + "_preprocessed.xlsx", index=False)

#Sum preproc
MIC_preproc_df = pd.DataFrame(MIC_rows)
MIC_preproc_df.to_excel(MIC_output, index=False)