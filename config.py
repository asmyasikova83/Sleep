
# Rename channels from raw data file
ch_renamed = {
    'Fp1': 'TrSens+',
    'Fp2': 'TrSens-',
    'P3': 'EMGL',
    'P4': 'EOGL',
    'T3': 'EMGR',
    'T4': 'EOGR',
    'F8': 'ECG',
    'A1': 'M1',
    'A2': 'M2',
    'Fz': 'O2',
}

# Settings for reference
anodes = ['TrSens+', 'EMGL', 'EOGR', 'ECG', 'F4', 'C4', 'O2', 'F3', 'C3', 'O1']
cathodes = ['TrSens-', 'EMGR', 'EOGL', 'M1', 'M1', 'M1', 'M1', 'M2', 'M2', 'M2']

ch_names = ['TrSens', 'CHIN', 'EOGR-EOGL', 'ECG-M1', 'F4_M1', 'C4-M1', 'O2-M1', 'F3-M2', 'C3-M2', 'O1-M2']
eeg_chs = ['F4_M1', 'C4-M1', 'O2-M1', 'F3-M2', 'C3-M2', 'O1-M2']
eog_ch = ['EOGR-EOGL']
ecg_ch = ['ECG-M1']
emg_ch = ['CHIN']
trsens_ch = ['TrSens']

# Add names of your channels if not listed
target_eeg = ['C3', 'C4', 'EEG C4-M1', 'EEG C4', 'C4-Ref', 'C4 - A1 - A2', 'C4-P4', 'C4-M1']
target_eog = ['EOG E2-M2', 'EOG E1-M1', 'ROC-LOC', 'EOGR-EOGL']
target_emg = ['EMG chin', 'CHIN', 'EMG1-EMG2']

# Settings from https://yasa-sleep.org/tutorials/quickstart.html
#Resample
resample_rate = 100

# Filter settings
low_cutoff_freq = 0.3
high_cutoff_freq =45