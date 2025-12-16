import os
import numpy as np
import pandas as pd
import mne
import yasa
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix

def read_annotations(file_path, file_type):
    if file_type == 'txt':
        with open(file_path, 'r') as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    elif file_type == 'csv':
        df = pd.read_csv(file_path)
        return df['Annotation'].astype(str).tolist()

def preprocessing(fname_edf):
    #Polysomnography data
    raw = mne.io.read_raw_edf(fname_edf, preload=True)

    #Selecting channels
    raw.drop_channels(["EMG chin", "EOG E1-M2", "EOG E2-M2", "ECG"])
    chan = raw.ch_names

    raw.resample(100)
    sf = raw.info["sfreq"]
    raw.filter(0.3, 45)

    return raw, chan, sf

def prepare_data_for_hypnogram(fname_txt, subject):
    hypno = pd.read_csv(fname_txt).squeeze()

    # 0 = Wake, 1 = N1 sleep, 2 = N2 sleep, 3 = N3 sleep and 4 = REM sleep
    sleep_stage_mapping = {
        'W': '0',
        'N1': '1',
        'N2': '2',
        'N3': '3',
        'R': '4'
    }

    # Modify the file with staging info
    # Get the second-to-last column name with Annotations
    second_last_col = hypno.columns[-2]
    # Remove 'Sleep stage ' prefix if it exists in the values
    hypno_clean = hypno[second_last_col].astype(str).str.replace('Sleep stage ', '', regex=False)
    # Remove whitespace
    hypno_clean = hypno_clean.str.strip()
    # Map the values using the dictionary
    hypno_modified = hypno_clean.map(lambda x: sleep_stage_mapping.get(x, x))
    #Filter out not stages
    mask = ~hypno_modified.isin(['Lights off', 'Lights on'])
    hypno_filtered = hypno_modified[mask]
    #hypno_filtered.name = 'Annotation'
    # Save the modified DataFrame to a new CSV file
    hypno_filtered.name = 'Annotation'
    hypno_filtered.to_csv("yasa_annotations_metrics/{}_annotations_doctor.csv".format(subject), index=False)

    return hypno_filtered

def plot_hypnogram(fname_pics, hypno_filtered):
    ax = yasa.plot_hypnogram(hypno_filtered)
    fig = ax.get_figure()
    fig.set_size_inches(35, 6)
    fig.savefig(fname_pics , dpi=300, bbox_inches='tight')
    plt.close(fig)

def plot_spectrogram(fname_pics, chan, sf, hypno_filtered, raw):
    # Upsample our hypnogram from 0.333 Hz to 100 Hz
    hypno_up = yasa.hypno_upsample_to_data(hypno_filtered, sf_hypno=1 / 30, data=raw)
    data = raw.get_data(units="uV")
    ax = yasa.plot_spectrogram(data[chan.index("EEG C4-M1")], sf, hypno_up)
    fig = ax.get_figure()
    fig.set_size_inches(35, 6)
    fig.savefig(fname_pics, dpi=300, bbox_inches='tight')
    plt.close(fig)

def yasa_staging(fname_pics, raw):
    sls = yasa.SleepStaging(raw, eeg_name="EEG C4-M1")
    hypno_pred = sls.predict()  # Predict the sleep stages
    hypno_pred = yasa.hypno_str_to_int(hypno_pred)  # Convert "W" to 0, "N1" to 1, etc
    ax = yasa.plot_hypnogram(hypno_pred)  # Plot
    fig = ax.get_figure()
    fig.set_size_inches(35, 6)
    fig.savefig(fname_pics, dpi=300, bbox_inches='tight')
    plt.close(fig)

    return hypno_pred

def average_recall(results_dict):
    #Recall = Sensitivity: Recall = True Positives / (True Positives + False Negatives)
    recalls = []
    for key, metrics in results_dict.items():
        # Ignore keys not attributed to classes 'accuracy', 'macro avg' и т.д.
        if key.isdigit():
            recalls.append(metrics['recall'])
    if recalls:
        average_recall = sum(recalls) / len(recalls)
        print('кол-во классов', len(recalls))
        return np.round(average_recall, 2)
    else:
        print("Нет данных по классам.")
        return 0

def average_PPV(doctor_hypno_scoring, hypno_pred):
    #Precision/Positive Predictive Value (PPV) = TP/(TP + FP)
    cm = confusion_matrix(doctor_hypno_scoring, hypno_pred)
    # Multi-class
    total = np.sum(cm)
    PPVs = []
    for i in range(cm.shape[0]):
        TP = cm[i, i]
        FP = np.sum(cm[i, :]) - TP
        FN = np.sum(cm[:, i]) - TP
        TN = total - (TP + FP + FN)
        PPV = TP / (TP + FP) if (TP + FP) > 0 else 0
        PPVs.append(PPV)

    return np.round(np.mean(PPVs), 2)

def specificity(doctor_hypno_scoring, hypno_pred):
    cm = confusion_matrix(doctor_hypno_scoring, hypno_pred)
    # Multi-class
    total = np.sum(cm)
    specificities = []
    for i in range(cm.shape[0]):
        TP = cm[i, i]
        FP = np.sum(cm[i, :]) - TP
        FN = np.sum(cm[:, i]) - TP
        TN = total - (TP + FP + FN)
        specificity = TN / (TN + FP) if (TN + FP) > 0 else 0
        specificities.append(specificity)

    return np.round(np.mean(specificities), 2)

def average_false_positive_rate(doctor_hypno_scoring, hypno_pred):
    #FPR = FP/(FP + TN)
    cm = confusion_matrix(doctor_hypno_scoring, hypno_pred)
    # Multi-class
    total = np.sum(cm)
    false_positive_rates = []
    for i in range(cm.shape[0]):
        TP = cm[i, i]
        FP = np.sum(cm[i, :]) - TP
        FN = np.sum(cm[:, i]) - TP
        TN = total - (TP + FP + FN)
        fpr = FP / (FP + TN) if (FP + TN) > 0 else 0
        false_positive_rates.append(fpr)

    return np.round(np.mean(false_positive_rates), 2), TP, FP, FN, TN

def compare_annotations(folder_metrics_path, subject):
    yasa_annotations_path = os.path.join(folder_metrics_path, "{}_annotations_yasa.csv".format(subject))
    doctor_annotations_path = os.path.join(folder_metrics_path, "{}_annotations_doctor.csv".format(subject))

    yasa_annotations_data = read_annotations(yasa_annotations_path, 'csv')
    doctor_annotations_data = read_annotations(doctor_annotations_path, 'csv')

    # Проверяем, что файлы имеют одинаковую длину
    if len(yasa_annotations_data) != len(doctor_annotations_data):
        print(f"Внимание: файлы имеют разную длину!")
        print(f"yasa_annotations_data: {len(yasa_annotations_data)} строк, doctor_annotations_data: {len(doctor_annotations_data)} строк")
        print("Сравнение будет выполнено только для общего количества строк")
        min_length = min(len(yasa_annotations_data), len(doctor_annotations_data))
    else:
        min_length = len(yasa_annotations_data)

    # Сравниваем построчно и выводим результат
    for i in range(min_length):
        is_match = yasa_annotations_data[i] == doctor_annotations_data[i]
        #print(f"{i + 1:6} | {yasa_annotations_data[i]:11} | {doctor_annotations_data[i]:11} | {is_match}")

        # Или просто вывод True/False для каждой строки:
        # print(is_match)

    # Дополнительная статистика
    matches = sum(1 for i in range(min_length) if yasa_annotations_data[i] == doctor_annotations_data[i])
    total = min_length
    accuracy = matches / total if total > 0 else 0

    #print(f"\nСтатистика сравнения:")
    #print(f"Всего строк: {total}")
    #print(f"Совпадений: {matches}")
    #print(f"Несовпадений: {total - matches}")
    print(f"Точность совпадения: {accuracy:.2%}")

    return round(accuracy, 2)
