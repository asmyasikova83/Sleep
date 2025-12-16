#Loads, prepocesses (filters, resamples) the data;
#Generates files {subject}_annotations_doctor.csv with mapped (to int) sleep stages classification;
#Plots hypnograms and spectrograms for each subject;
#Launches YASA and stores {subject}_annotations_yasa.csv with mapped to int classification of sleep stages
#Stores {subject}_metrics_report_yasa.txt with recall, precision, f1 score ... for each subject
#Stores cmp_annotations.txt with matches of doctor's manual classification and yasa vs total aka cmp accuracy

import os
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report
import warnings
warnings.filterwarnings("ignore")
from functions import (preprocessing, prepare_data_for_hypnogram, plot_hypnogram,
                      plot_spectrogram, yasa_staging, compare_annotations)

folder_data =  r'C:\Users\msasha\PycharmProjects\Sleep\data\haaglanden-medisch-centrum-sleep-staging-database-1.1\recordings'
folder_pics_path = r"C:\Users\msasha\PycharmProjects\Sleep\pics"
folder_metrics_path = r"C:\Users\msasha\PycharmProjects\Sleep\yasa_annotations_metrics"

os.makedirs(folder_pics_path, exist_ok=True)
os.makedirs(folder_metrics_path, exist_ok=True)

compare_annot_list = []
for idx in range(1, 155):
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
    fname_txt = folder_data + "\{}_sleepscoring.txt".format(subject)
    doctor_hypno_scoring = prepare_data_for_hypnogram(fname_txt, subject)

    #Hypnogram
    fname_pics = folder_pics_path + "\hypnogram_{}_doctor.png".format(subject)
    plot_hypnogram(fname_pics, doctor_hypno_scoring )

    #Spectrogram
    fname_pics = folder_pics_path + "\spectrogram_{}_doctor.png".format(subject)
    plot_spectrogram(fname_pics, chan, sf, doctor_hypno_scoring, raw)

    #Automatic sleep staging with YASA
    fname_pics = folder_pics_path + "\hypnogram_{}_yasa.png".format(subject)
    hypno_predicted = yasa_staging(fname_pics, raw)

    #Костыль
    if len(hypno_predicted) > len(doctor_hypno_scoring):
        hypno_pred = hypno_predicted[:-1]
    else:
        hypno_pred = hypno_predicted

    # Metrics
    doctor_hypno_scoring = doctor_hypno_scoring.astype(int)
    report = classification_report(doctor_hypno_scoring, hypno_pred, output_dict=False)
    print(report)

    # Generate YASA annotations
    yasa_metrics_path = os.path.join(folder_metrics_path, "{}_metrics_report_yasa.txt".format(subject))
    yasa_annotations_path = os.path.join(folder_metrics_path, "{}_annotations_yasa.csv".format(subject))
    with open(yasa_annotations_path, 'w', newline='', encoding='utf-8') as f:
        f.write("Annotation\n")  # Заголовок
        for prediction in hypno_pred:
            f.write(f"{prediction}\n")
    with open(yasa_metrics_path, 'w') as f:
        f.write(report)

    # Manual comparison of doctor's and yasa's annotations
    compare_annot_list.append(compare_annotations(folder_metrics_path, subject))
    compare_annotations_path = folder_metrics_path + '/cmp_annotations.txt'
    with open(compare_annotations_path, 'w', newline='', encoding='utf-8') as f:
        f.write("doctor's, yasa annotations: matches / total\n")  # Заголовок
        for accuracy in compare_annot_list:
            f.write(f"{accuracy}\n")
