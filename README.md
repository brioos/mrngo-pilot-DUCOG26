# Project Structure

```text
project/
├── data/
│   ├── MIC/
│   └── CFC/
├── derivatives/
│   ├── MIC/
│   └── CFC/
└── scripts/
```

## Folders

- `data/MIC/` — original raw data from the `MIC` PsychoPy experiment.
- `data/CFC/` — original raw data from the `FCF` PsychoPy experiment.
- `derivatives/` — outputs generated from analyses, such as results, preprcoessed elements.
- `derivatives/MIC/` — participant-wise preprocessed data based on `scripts/MIC_preprocess.py`.
- `derivatives/CFC/` — participant-wise preprocessed data based on `scripts/MIC_preprocess.py`.
- `derivatives/figures/` — tables, or figures generated during analysis.
- `code/` — preprocessing and analysis scripts for the project.

## Scripts

The `code/` folder contains the analysis code used in the project.

In this project, analyses are written in **Python** and **R**.

## Basic workflow

1. Keep original files in `data/`
2. Save preprocessed files in `derivatives/`
3. Save analysis outputs in `derivatives/` or `derivatives/figures/`.

4. Keep code in `code/`

## Reproducibility
- Never overwrite anythin in `data/raw/`.
- Always use commits for version control.
- Comment your codes and document your decisions.