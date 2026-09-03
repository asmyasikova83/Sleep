# Loads, prepocesses (filters, resamples) the data;
# Generates files {subject}_annotations_doctor.csv with mapped (to int) sleep stages classification;
# Plots hypnograms and spectrograms for each subject;
# Launches YASA and stores {subject}_annotations_yasa.csv with mapped to int classification of sleep stages
# Stores {subject}_metrics_report_yasa.txt with recall, precision, f1 score ... for each subject
# Stores cmp_annotations.txt with matches of doctor's manual classification and yasa vs total aka cmp accuracy

import os
from os import listdir
import numpy as np
import glob
import pandas as pd
import re
import mne
from sklearn.metrics import accuracy_score, classification_report
import warnings
warnings.filterwarnings("ignore")
from functions import (process_annotations, split_long_annotations_df, preprocessing, generate_random_annotations,
                       prepare_data_for_hypnogram, plot_hypnogram,
                       plot_spectrogram, yasa_staging, compare_annotations)

#folder_data = r"C:\Users\TelefonMelfon\Desktop\Miasnikova\CAP\data"
#folder_metrics_path = r"C:\Users\TelefonMelfon\Desktop\Miasnikova\CAP\metrics"
#folder_pics_path = r"C:\Users\TelefonMelfon\Desktop\CAP\Miasnikova\CAP\pics"

folder_data = r"\\MCSSERVER\DB Temp\physionet.org\files\capslpdb\1.0.0"
#folder_data = r"\\MCSSERVER\DB Temp\physionet.org\files\capslpdb\1.0.0"
folder_metrics_path = r"\\MCSSERVER\DB Temp\msasha\Sleep\CAP\metrics"
folder_pics_path = r"\\MCSSERVER\DB Temp\msasha\Sleep\CAP\pics"

random = True
if random:
    #folder_metrics_path = r"C:\Users\TelefonMelfon\Desktop\Miasnikova\CAP\metrics\random"
    #folder_pics_path = r"C:\Users\TelefonMelfon\Desktop\Miasnikova\CAP\pics\random"
    folder_metrics_path = r"\\MCSSERVER\DB Temp\msasha\Sleep\CAP\metrics\random"
    folder_pics_path = r"\\MCSSERVER\DB Temp\msasha\Sleep\CAP\pics\random"

os.makedirs(folder_pics_path, exist_ok=True)
os.makedirs(folder_metrics_path, exist_ok=True)

files = listdir(folder_data)
compare_annot_list = []
counter = 0
for f in files:
    # EEG in PSG
    # 1. Ищем шаблон для PSG.edf
    psg_match = re.search(r"\.edf", f, re.IGNORECASE)  # лучше экранировать точку
    if not psg_match:
        print(f"No PSG pattern in '{f}'. Skipping.")
        continue

    # prefix будет содержать всё, что ДО .edf
    prefix = f[:psg_match.start()]
    print(f"Prefix: {prefix}")

    # Формируем путь к PSG.edf
    fname_edf = os.path.join(folder_data, f"{prefix}.edf")
    print(f"PSG file: {fname_edf}")

    # Проверяем существование (опционально)
    if os.path.exists(fname_edf):
        print("PSG file exists.")
    else:
        print("PSG file not found.")

    # 2. Формируем шаблон для Hypnogram.txt на основе найденных prefix
    hypno_txt = os.path.join(folder_data, f"{prefix}.txt")

    # Проверяем существование Hypnogram (опционально)
    if os.path.exists(hypno_txt):
        print(f" Hypnogram file exists: {hypno_txt}")
    else:
        print("Hypnogram file not found.")

    annotations = np.loadtxt(hypno_txt, delimiter='\t', dtype=str, skiprows=21)

    annotations = np.array(annotations, dtype=str)
    # Get and process the data (channels, resampling, filter), remove data from raw eeg which is inconsistent with annotations: > last onset + duration
    [raw, chan, sf, annotations] = preprocessing(fname_edf, annotations)

    if random:
        data_label = 'CAP'
        random_label = 'random'
        hypno_doctor_clean = generate_random_annotations('', folder_metrics_path, prefix, data_label, annotations)
    else:
        hypno_doctor_clean = process_annotations(annotations)
        # print('hypno_doctor_clean ', hypno_doctor_clean.value_counts())
        fname = folder_metrics_path + "/{}_annotations_doctor.csv".format(prefix)
        hypno_doctor_clean.to_csv(fname, index=False)
    hypnogram = True
    if hypnogram:
        # Hypnogram
        fname_pics = folder_pics_path + "/hypnogram_{}_doctor.png".format(prefix)
        plot_hypnogram(fname_pics, hypno_doctor_clean)

    hypno_doctor_filtered = hypno_doctor_clean
    # Spectrogram
    fname_pics = folder_pics_path + "/spectrogram_{0}_{1}.png".format(prefix, random_label)
    plot_spectrogram(fname_pics, chan, sf, hypno_doctor_filtered, raw)

    # Automatic sleep staging with YASA
    fname_pics = folder_pics_path + "/hypnogram_{}_yasa.png".format(prefix)
    hypno_predicted = yasa_staging(fname_pics, raw)
    print('------------------------------------------------------')
    print(len(hypno_doctor_filtered))
    print(len(hypno_predicted))

    print('------------------------------------------------------')
    # Metrics
    # hypno_doctor_filtered = hypno_doctor_filtered.astype(int)
    # report = classification_report(hypno_doctor_filtered, hypno_predicted, output_dict=False)
    # print(report)
    # check that raw EEG is long enough fpor yasa 5 min * 60 sec * 100 (sampling rate)
    """
    if len(hypno_doctor_filtered) != len(hypno_predicted):
        continue
    else:
        counter = counter + 1
    
    if len(hypno_doctor_filtered) != len(hypno_predicted):
        m = min(len(hypno_doctor_filtered), len(hypno_predicted))
    """
    # Generate YASA annotations
    yasa_metrics_path = os.path.join(folder_metrics_path, "{}_metrics_report_yasa.txt".format(prefix))
    yasa_annotations_path = os.path.join(folder_metrics_path, "{}_annotations_yasa.csv".format(prefix))
    with open(yasa_annotations_path, 'w', newline='', encoding='utf-8') as f:
        f.write("Annotation\n")  # Заголовок
        for prediction in hypno_predicted:
            f.write(f"{prediction}\n")

    # Manual comparison of doctor's and yasa's annotations
    compare_annot_list.append(compare_annotations(folder_metrics_path, prefix))
    compare_annotations_path = folder_metrics_path + '/cmp_annotations.txt'
    with open(compare_annotations_path, 'w', newline='', encoding='utf-8') as f:
        f.write("doctor's, yasa annotations: matches / total\n")  # Заголовок
        for accuracy in compare_annot_list:
            f.write(f"{accuracy}\n")
