# Computes metrics averaged over classes in each subject:
# avg_recall (this is derived from  classification_report())
# avg_PPV aka Positive Predictive Value (PPV)
# avg_fpr, TP, FP, FN, TN aka false_positive_rate, true positives,
# false positives, false negatives, true negatives
# those metrics are stored in a table with a row representing one subject

import os
from os import listdir
import glob
import mne
import numpy as np
import pandas as pd
import re
from sklearn.metrics import classification_report
import warnings

warnings.filterwarnings("ignore")
from functions import (process_annotations, generate_random_annotations, split_long_annotations_df, preprocessing,
                       prepare_data_for_hypnogram,
                       yasa_staging, average_sensitivity, average_PPV,
                       average_false_positive_rate, compare_annotations)

#folder_data = r"C:\Users\TelefonMelfon\Desktop\Miasnikova\CAP\data"
#folder_metrics_path = r"C:\Users\TelefonMelfon\Desktop\Miasnikova\CAP\metrics\random"
#folder_pics_path = r"C:\Users\TelefonMelfon\Desktop\CAP\Miasnikova\CAP\pics"
folder_data = r"\\MCSSERVER\DB Temp\physionet.org\files\capslpdb\1.0.0"
folder_metrics_path = r"\\MCSSERVER\DB Temp\msasha\Sleep\CAP\metrics\random"
folder_pics_path = r"\\MCSSERVER\DB Temp\msasha\Sleep\CAP\pics"
folder_data_hypno = folder_data


os.makedirs(folder_pics_path, exist_ok=True)
os.makedirs(folder_metrics_path, exist_ok=True)

columns = ["ID записи", "TP", "FP", "FN", "TN", "Чувствительность Se (R)", "Специфичность P(PPV)",
           "Доля ложных распознаваний FPR", "Точность: Matches Yasa & Doctor/Total"]
df = pd.DataFrame(columns=columns)

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
    # Get and process the data (channels, resampling, filter), remove data from raw eeg which is inconsistent with annotations: > last onset + duration
    [raw, chan, sf, annotations] = preprocessing(fname_edf, annotations)

    data_label = 'CAP'
    #doctor_hypno_scoring = generate_random_annotations('', folder_metrics_path, prefix, data_label, annotations)
    doctor_hypno_scoring = generate_random_annotations('', folder_metrics_path, prefix, data_label, annotations)
    #
    # Automatic sleep staging with YASA
    fname_pics = folder_pics_path + "/hypnogram_{}_yasa.png".format(prefix)
    hypno_predicted = yasa_staging(fname_pics, raw)

    doctor_hypno_scoring = np.array(doctor_hypno_scoring)
    hypno_predicted = np.array(hypno_predicted)

    print(len(doctor_hypno_scoring))
    print(len(hypno_predicted))

    if len(doctor_hypno_scoring) != len(hypno_predicted):
        m = min(len(doctor_hypno_scoring), len(hypno_predicted))
        doctor_hypno_scoring_ = doctor_hypno_scoring[:m]
        hypno_predicted_ = hypno_predicted[:m]
    else:
        doctor_hypno_scoring_ = doctor_hypno_scoring.copy()
        hypno_predicted_ = hypno_predicted.copy()

    doctor_hypno_scoring = doctor_hypno_scoring_.astype(int)
    hypno_predicted = hypno_predicted_.astype(int)

    avg_sensitivity = average_sensitivity(doctor_hypno_scoring, hypno_predicted)
    # "Specificity" in ГОСТ P MЭК 60601 2-47-2017 (tp/(tp + fp)) = Precision, ie Positive Predictive Value (PPV)
    # https://pmc.ncbi.nlm.nih.gov/articles/PMC8993826/
    avg_PPV = average_PPV(doctor_hypno_scoring, hypno_predicted)
    # FPR
    [avg_fpr, TP, FP, FN, TN] = average_false_positive_rate(doctor_hypno_scoring, hypno_predicted)
    # Cmp accuracy: hits of yasa and doctor / total
    manual_acc = compare_annotations(folder_metrics_path, prefix)

    # Table
    #ID = re.sub(r'[A-Za-z]', '', prefix)
    ID = prefix
    averaged_row = [ID, TP, FP, FN, TN, avg_sensitivity, avg_PPV, avg_fpr, manual_acc]

    df.loc[len(df)] = averaged_row
    print(df)

# Means for the table
# TP, FP, FN, TN
cols_to_round_0 = df.columns[1:5]
# "Чувствительность Se (R)", "Специфичность P(PPV)",
# "Доля ложных распознаваний FPR", "Точность: Matches Yasa & Doctor/Total"
cols_to_round_2 = df.columns[5:]

df[cols_to_round_0] = df[cols_to_round_0].astype(float).round(0)
df[cols_to_round_2] = df[cols_to_round_2].astype(float).round(2)

means = df[cols_to_round_0].mean().round(0).astype(int)
means2 = df[cols_to_round_2].mean().round(2)

# Mean
mean_result = ['Среднее']
mean_result += list(means)
mean_result += list(means2)

print(mean_result)
# Добавляем строку в DataFrame
df.loc[len(df)] = mean_result

# Save in Excel
yasa_metrics_path = os.path.join(folder_metrics_path, "Total_metrics_CAP_random.xlsx")
df.to_excel(yasa_metrics_path, index=False)
