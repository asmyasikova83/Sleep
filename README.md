## YASA
___________________________________________________
Based on YASA algorithm for identifying sleep stages (https://yasa-sleep.org/index.html)


## Sonya Sleep Application

Sleep_App.py:

> Attention!::q
            requires EDFbrowser: https://www.teuniz.net/edfbrowser/

Provides GUI 

            1. to create a PDF report with sleep statistics, a hypnogram, a spectrogram for the choisen patient

            2. to show EDF/BDF of a patient with a huypnogram

config.py - import to add channel names and settings for processing data
functions_pipeline.py - import to add the necessary funcs

___________________________________________________________
## Requirements

            fpdf2==2.5
            matplotlib==3.8.4
            mne==1.6.1
            numpy==1.25.2
            pandas==2.3.3
            yasa==0.6.5
