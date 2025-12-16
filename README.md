# Sleep
Based on YASA algorithm for identifying sleep stages (https://yasa-sleep.org/index.html) the and data from Haaglanden Medisch Centrum sleep staging database (https://doi.org/10.13026/t4w7-3k21) the code performs automatic sleep staging identification

0_YASA_generate_hypnogram_annotations.py:

Loads, prepocesses (filters, resamples) the data;
Generates files {subject}_annotations_doctor.csv with mapped (to int) sleep stages classification;
Plots hypnograms and spectrograms for each subject;
Launches YASA and stores {subject}_annotations_yasa.csv with mapped to int classification of sleep stages
Stores {subject}_metrics_report_yasa.txt with recall, precision, f1 score ... for each subject
Stores cmp_annotations.txt with matches of doctor's manual classification and yasa vs total aka cmp accuracy

1_YASA_generate_metrics_table.py:

Computes metrics averaged over classes in each subject:
avg_recall (this is derived from  classification_report())
avg_PPV aka Positive Predictive Value (PPV)
avg_fpr, TP, FP, FN, TN aka false_positive_rate, true positives,
false positives, false negatives, true negatives
those metrics are stored in a table with a row representing one subject

2_Sleep_statistics.py:

Derives and stores sleep statistics (Time in bed, Latency N1-3/REM, Share of N1-3/REM, Sleep efficicency
for each subject from YASA package in {subject}_sleep_statistics.json"

3_Sleep_PDF_report.py:

Loads sleep statistics for each subjects and puts it in PDF 
with a hypnogram, spectrogram
Stores the PDF in {subject}_sleep_statistics.pdf

functions.py - import to add the necessary funcs

