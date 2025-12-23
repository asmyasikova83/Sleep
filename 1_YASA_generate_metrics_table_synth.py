#Computes metrics averaged over classes in each subject:
#avg_recall (this is derived from  classification_report())
#avg_PPV aka Positive Predictive Value (PPV)
#avg_fpr, TP, FP, FN, TN aka false_positive_rate, true positives,
#false positives, false negatives, true negatives
#those metrics are stored in a table with a row representing one subject

import os
import numpy as np
import pandas as pd
import re
from sklearn.metrics import classification_report
import warnings
warnings.filterwarnings("ignore")
from functions import (preprocessing, generate_random_annotations,
                       yasa_staging, average_recall,average_sensitivity, average_PPV,
                      average_false_positive_rate, compare_annotations)
import openpyxl

folder_data = "/home/daniil/sleep/Sleep/data"
folder_pics_path = "/home/daniil/sleep/Sleep/pics"
folder_metrics_path = "/home/daniil/sleep/Sleep/random_yasa_annotations_metrics"

os.makedirs(folder_pics_path, exist_ok=True)
os.makedirs(folder_metrics_path, exist_ok=True)

columns = ["ID записи", "TP", "FP", "FN", "TN" , "Чувствительность Se (R)", "Специфичность P(PPV)",
           "Доля ложных распознаваний FPR", "Точность: Matches Yasa & Doctor/Total"]
df = pd.DataFrame(columns=columns)

for idx in range(1, 4):
    if idx < 10:
        subject = "SN00{}".format(idx)
    elif idx > 9 and idx < 100:
        subject = "SN0{}".format(idx)
    else:
        assert(idx > 99)
        subject = "SN{}".format(idx)

    fname_edf = os.path.join(folder_data, f"{subject}.edf")
    #Get and process the data (channels, resampling, filter)
    try:
        [raw, chan, sf] = preprocessing(fname_edf)
    except Exception as FileNotFoundError:
        print(f"Error processing file {fname_edf}: {FileNotFoundError}")
        continue

    #Mapping
    # 0 = Wake, 1 = N1 sleep, 2 = N2 sleep, 3 = N3 sleep and 4 = REM sleep
    fname_txt = folder_data + "/{}_sleepscoring.txt".format(subject)
    hypno_random_scoring = generate_random_annotations(fname_txt, folder_metrics_path, subject)
    #Automatic sleep staging with YASA
    fname_pics = folder_pics_path + "/hypnogram_{}_yasa.png".format(subject)
    hypno_predicted = yasa_staging(fname_pics, raw)

    #Костыль
    if len(hypno_predicted) > len(hypno_random_scoring):
        hypno_pred = hypno_predicted[:-1]
    else:
        hypno_pred = hypno_predicted

    # Metrics
    hypno_random_scoring = hypno_random_scoring.astype(int)
    report = classification_report(hypno_random_scoring, hypno_pred, output_dict=True)
    # "Sensitivity"  in ГОСТ P MЭК 60601 2-47-2017 (tp/(tp + fn)) = Recall
    #https://pmc.ncbi.nlm.nih.gov/articles/PMC10529246/https://pmc.ncbi.nlm.nih.gov/articles/PMC10529246/
    avg_recall = average_recall(report)
    avg_sens = average_sensitivity(hypno_random_scoring, hypno_pred)
    #"Specificity" in ГОСТ P MЭК 60601 2-47-2017 (tp/(tp + fp)) = Precision, ie Positive Predictive Value (PPV)
    # https://pmc.ncbi.nlm.nih.gov/articles/PMC8993826/
    avg_PPV = average_PPV(hypno_random_scoring, hypno_pred)
    # FPR
    [avg_fpr, TP, FP, FN, TN] = average_false_positive_rate(hypno_random_scoring, hypno_pred)
    # Cmp accuracy: hits of yasa and doctor / total
    manual_acc = compare_annotations(folder_metrics_path, subject)

    # Table
    ID = re.sub(r'[A-Za-z]', '', subject)
    averaged_row = [ID,  TP, FP, FN, TN, avg_sens, avg_PPV, avg_fpr, manual_acc]
    df.loc[len(df)] = averaged_row
    print(df)

# Means for the table
#TP, FP, FN, TN
cols_to_round_0 = df.columns[1:5]
# "Чувствительность Se (R)", "Специфичность P(PPV)",
# "Доля ложных распознаваний FPR", "Точность: Matches Yasa & Doctor/Total"
cols_to_round_2 = df.columns[5:]

df[cols_to_round_0] = df[cols_to_round_0].astype(float).round(0)
df[cols_to_round_2] = df[cols_to_round_2].astype(float).round(2)

means = df[cols_to_round_0].mean().round(0).astype(int)
means2 = df[cols_to_round_2].mean().round(2)

#Mean
mean_result = ['Среднее']
mean_result += list(means)
mean_result += list(means2)

print(mean_result)
# Добавляем строку в DataFrame
df.loc[len(df)] = mean_result

# Save in Excel
yasa_metrics_path = os.path.join(folder_metrics_path, "Total_metrics_report_yasa_random.xlsx")
df.to_excel(yasa_metrics_path, index=False)
