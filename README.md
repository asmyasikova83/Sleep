## YASA
___________________________________________________
Based on YASA algorithm for identifying sleep stages (https://yasa-sleep.org/index.html)


## Sonya Sleep Application

`Sleep_App.py`:

> Attention!
            requires EDFbrowser: https://www.teuniz.net/edfbrowser/

GUI for EDF/BDF/SM files:

            1. PDF report generation: produces a report containing sleep statistics, a hypnogram, and a spectrogram.

            2. Data visualization: displays the EDF/BDF file content with an overlaid hypnogram.


`config.py` - import to add channel names and settings for processing data


`functions_pipeline.py` - import to add the funcs for data processing

___________________________________________________________
## Requirements

            fpdf2==2.5
            matplotlib==3.8.4
            mne==1.6.1
            numpy==1.25.2
            pandas==2.3.3
            yasa==0.6.5
