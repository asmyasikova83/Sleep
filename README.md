# Sleep

Based on YASA algorithm for identifying sleep stages (https://yasa-sleep.org/index.html) the and data from Haaglanden Medisch Centrum sleep staging database (https://doi.org/10.13026/t4w7-3k21) the code performs automatic sleep staging identification

Sleep_staging_YASA_pipeline.py:

Loads, prepocesses (filters, resamples) the data for each subject

Launches YASA and stores {subject}_annotations_yasa.csv with mapped to int classification of sleep stages

Plots hypnograms and spectrograms 

Derives and stores sleep statistics (Time in bed, Latency N1-3/REM, Share of N1-3/REM, Sleep efficiency

for the subject from YASA package in {subject}_sleep_statistics.json"

Puts sleep statistics in PDF 

with a hypnogram, spectrogram

Stores the PDF in {subject}_sleep_statistics.pdf

functions_pipeline.py - import to add the necessary funcs

___________________________________________________________
Launching the project

create and activate virtual environment:

python - m venv .venv1

.venv1\Scripts\Activate.ps1

install the dependencies

python -m pip install -r requirements.txt
