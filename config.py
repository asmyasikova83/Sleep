
# Add names of your channels if not listed
target_eeg = ['C3', 'C4', 'EEG C4-M1', 'EEG C4', 'C4-Ref', 'C4 - A1 - A2', 'C4-P4']
target_eog = ['EOG E2-M2', 'EOG E1-M1', 'ROC-LOC']
target_emg = ['EMG chin', 'CHIN', 'EMG1-EMG2']

# Settings from https://yasa-sleep.org/tutorials/quickstart.html
#Resample
resample_rate = 100

# Filter settings
low_cutoff_freq = 0.3
high_cutoff_freq =45