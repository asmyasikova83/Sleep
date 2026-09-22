## YASA
___________________________________________________
Based on YASA algorithm for identifying sleep stages (https://yasa-sleep.org/index.html)


## Sonya Sleep Application

Sleep_App.py:

! requires EDFbrowser: https://www.teuniz.net/edfbrowser/

Provides GUI 

            1. to create a PDF report with sleep statistics, a hypnogram, a spectrogram for the choisen patient

            2. to show EDF/BDF of a patient with a huypnogram

config.py - import to add channel names and settings for processing data
functions_pipeline.py - import to add the necessary funcs

___________________________________________________________
## Launching the project


            1. create and activate virtual environment: python - m venv .venv1

               .venv1\Scripts\Activate.ps1

            2. install the dependencies: python -m pip install -r requirements.txt