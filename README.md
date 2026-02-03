# Sleep
___________________________________________________
Based on YASA algorithm for identifying sleep stages (https://yasa-sleep.org/index.html)

the and data from Haaglanden Medisch Centrum sleep staging database (https://doi.org/10.13026/t4w7-3k21) 

the code performs automatic sleep staging identification


## Sleep Application

Sleep_App.py:

! requires EDFbrowser: https://www.teuniz.net/edfbrowser/

Provides GUI 
           
            1. to show raw EDF of a chosen patient
             
              
             2. to create a PDF report with automated sleep classification based on YASA (see Sleep_staging_YASA_pipeline.py)


             3. to show the PDF report from 2. with sleep statistics, a hypnogram, a spectrogram for the choisen patient


             4. to show a huypnogram separately


______________________________________________________
Sleep_staging_YASA_pipeline.py:

            1.Loads, prepocesses (filters, resamples) the data for each patient

            2. Launches YASA and stores {subject}_annotations_yasa.csv with mapped to int classification of sleep stages

            3. Plots hypnograms and spectrograms 

            4. Derives and stores sleep statistics (Time in bed, Latency N1-3/REM, Share of N1-3/REM, Sleep efficiency

               for the participant from YASA package in {subject}_sleep_statistics.json"

            5. Puts sleep statistics in PDF along with a hypnogram, spectrogram. Stores the PDF in {subject}_sleep_statistics.pdf

functions_pipeline.py - import to add the necessary funcs

___________________________________________________________
## Launching the project


            1. create and activate virtual environment: python - m venv .venv1

               .venv1\Scripts\Activate.ps1

            2. install the dependencies: python -m pip install -r requirements.txt
