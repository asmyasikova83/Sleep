import os
import numpy as np
import pandas as pd
import mne
import yasa
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix
import random

def detect_glued_anns(annotations_filt, col_name):
    diffs = annotations_filt[col_name].diff()
    mask = (diffs != pd.Timedelta(seconds=30))
    problematic_rows = annotations_filt[mask]

    if not problematic_rows.empty:
        # Добавляем колонку с предыдущим временем для контекста
        problematic_rows['prev_time'] = annotations_filt[col_name].shift(1)[mask]
        problematic_rows['Duration[s]'] = diffs[mask]
        problematic_rows = problematic_rows.dropna(subset=['Duration[s]']).copy()
        problematic_rows['Duration[s]'] = problematic_rows['Duration[s]'].dt.total_seconds().astype(int)

        merged = annotations_filt.merge(
            problematic_rows[['Time [hh:mm:ss]', 'Duration[s]']],
            on='Time [hh:mm:ss]',
            how='left',
            suffixes=('', '_prob')  # Optional: distinguishes columns if names clash
        )

        # 2. Apply your logic:
        # If 'Duration[s]_prob' exists (match found), use it. Otherwise, use original 'Duration[s]'.
        # Note: If your original column is named 'Duration[s]', and the merged one is 'Duration[s]_prob'
        merged['Final_Duration'] = merged['Duration[s]_prob'].fillna(merged['Duration[s]'])

        # Optional: Drop the temporary helper columns
        merged = merged.drop(columns=['Duration[s]_prob'])

        # 2. Filter rows where duration is greater than 30
        #filtered = merged[merged['Final_Duration'] > pd.Timedelta(seconds=30)].copy()
        merged['Final_Duration'] = merged['Final_Duration'].astype(int)
        filtered = merged[merged['Final_Duration'] > np.abs(30)].copy()
    else:
        print("Все интервалы равны ровно 30 секундам!")
        merged = annotations_filt
    #print('merged', merged)
    return problematic_rows, merged

def read_annotations(file_path, file_type):
    if file_type == 'txt':
        with open(file_path, 'r') as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    elif file_type == 'csv':
        df = pd.read_csv(file_path)
        return df['Annotation'].astype(str).tolist()


def preprocessing(fname_edf, annotations):
    # Polysomnography data
    raw = mne.io.read_raw_edf(fname_edf, preload=True)

    # Suppose you have a DataFrame of annotations:
    # columns: 'onset', 'duration', 'description'

    '''
    # Get the last annotation
    last_row = annotations[-1]
    # Compute the time to crop from (onset + duration)
    crop_start = last_row['Time [hh:mm:ss]'] + last_row['Duration[s]']

    if last_row['description'] == 'Sleep stage ?':
        cropped_ann = annotations[:-1]
        print('len cropped', len(cropped_ann))
    else:
        cropped_ann = annotations

    if raw.times[-1] > crop_start:
        cropped_raw = raw.crop(tmin=crop_start, tmax=None)  # tmax=None keeps until the end
    else:
        cropped_raw = raw
    # print(f"Cropped raw EEG starting from {crop_start} seconds")
    '''
    # Selecting channels TODO
    # raw.drop_channels(["EMG chin", "EOG E1-M2", "EOG E2-M2", "ECG"])
    # raw.drop_channels(["EMG chin", "EOG E2-M2"]
    # chan = cropped_raw.ch_names
    cropped_raw = raw
    chan = cropped_raw.ch_names

    cropped_raw.resample(100)
    sf = cropped_raw.info["sfreq"]
    cropped_raw.filter(0.3, 45)

    #return cropped_raw, chan, sf, cropped_ann
    return cropped_raw, chan, sf, annotations

def remove_col(annotations, cols, target_col, target_val):
    cleaned_annotations = []

    # Rebuild the list excluding that index for every row
    for row in annotations:
        new_row = [val for i, val in enumerate(row) if val not in target_val and val != target_col]
        cleaned_annotations.append(new_row)

    cols_clean = [val for i, val in enumerate(cols) if val != target_col]

    return cleaned_annotations, cols_clean

def process_annotations(annotations):
    #processed_annotations = split_long_annotations(annotations)
    #processed_annotations_clean = [row for row in processed_annotations if row.get('description') != 'Movement time']
    #annotations_list = [ann['description'] for ann in processed_annotations_clean]

    annotations_list = [ann['Sleep Stage'] for ann in annotations]
    hypno_doctor = pd.DataFrame({'Annotation': annotations_list})
    doctor_hypno_scoring = (
        hypno_doctor['Annotation']
        .fillna('')  # Handle NaN values
        .astype(str)
        .str.replace('Sleep stage ', '', regex=False)
        .str.replace('W', '0', regex=False)
        .str.replace('4', '3', regex=False)  # 3 + 4 | **N3 (Slow-Wave Sleep)**
        .str.replace('R', '4', regex=False)  # 3 + 4 | **N3 (Slow-Wave Sleep)**

        .str.strip()  # Clean whitespace
    )

    return doctor_hypno_scoring


def generate_random_annotations(fname_txt, folder_metrics_path, subject, data_label, annotations):
    # 0 = Wake, 1 = N1 sleep, 2 = N2 sleep, 3 = N3 sleep and 4 = REM sleep
    sleep_stage_mapping = {
        'W': '0',
        'N1': '1',
        'N2': '2',
        'N3': '3',
        'R': '4'
    }

    # Extract the sleep stages (keys)
    stages = list(sleep_stage_mapping.keys())

    # Shuffle the stages to randomize the order
    random.shuffle(stages)

    # Create a new mapping with the shuffled stages
    randomized_mapping = {stage: str(i) for i, stage in enumerate(stages)}

    # Print the randomized mapping
    print(randomized_mapping)

    if data_label == 'Haaglanden':
        hypno = pd.read_csv(fname_txt).squeeze()
        # Modify the file with staging info
        # Get the second-to-last column name with Annotations
        second_last_col = hypno.columns[-2]
        # Remove 'Sleep stage ' prefix if it exists in the values
        hypno_clean = hypno[second_last_col].astype(str).str.replace('Sleep stage ', '', regex=False)
        # Remove whitespace
        hypno_clean = hypno_clean.str.strip()
        # Map the values using the dictionary
        hypno_modified = hypno_clean.map(lambda x: randomized_mapping.get(x, x))
    if data_label == 'Sleep_EDF_Extended':
        split_ann = split_long_annotations_df(data_label, annotations)
        processed_annotations = [row for row in split_ann if row.get('description') != 'Movement time']

        annotations_list = [ann['description'] for ann in processed_annotations]
        hypno_doctor = pd.DataFrame({'Annotation': annotations_list})

        labels = list(randomized_mapping.values())

        hypno_modified = (
            hypno_doctor['Annotation']
            .fillna('')
            .astype(str)
            .str.replace('Sleep stage ', '', regex=False)
            .str.replace('4', '3', regex=False)
            .str.strip()
            .apply(lambda _: random.choice(labels))
        )
    if data_label == 'CAP':
        cols = ['Sleep Stage', 'Position', 'Time [hh:mm:ss]', 'Event', 'Duration[s]', 'Location']
        col_name = 'Time [hh:mm:ss]'
        annotations_filt = process_anns(annotations, cols, col_name)

        problematic_rows, annotations_filt_corr = detect_glued_anns(annotations_filt, col_name)
        #annotations_filt_corr  = annotations_filt.reset_index(drop=True)

        annotations_filt_long = split_long_annotations_df(data_label, annotations_filt_corr)
        annotations_filt_long = pd.DataFrame(annotations_filt_long)

        hypno_doctor = pd.DataFrame({'Annotation': annotations_filt_long['Event']})

        labels = list(randomized_mapping.values())

        hypno_modified = (
            hypno_doctor['Annotation']
            .fillna('')
            .astype(str)
            .str.replace('Sleep stage ', '', regex=False)
            .str.replace('REM ', 'R', regex=False)
            .str.replace('S4', 'S3', regex=False)
            .str.strip()
            .apply(lambda _: random.choice(labels))
        )
    print(hypno_modified.unique())
    # Filter out not stages
    if data_label == 'Haaglanden':
        mask = ~hypno_modified.isin(['Lights off', 'Lights on'])
        hypno_filtered = hypno_modified[mask]
    else:
        hypno_filtered = hypno_modified
    print(hypno_filtered.unique())
    # hypno_filtered.name = 'Annotation'
    # Save the modified DataFrame to a new CSV file
    hypno_filtered.name = 'Annotation'
    fname = folder_metrics_path + "/{}_annotations_doctor.csv".format(subject)
    hypno_filtered.to_csv(fname, index=False)

    return hypno_filtered


def split_long_annotations_df(label, annotations):
    """
    Processes a list of annotation dictionaries.
    If an annotation's duration > 30 seconds, splits it into 30-second chunks,
    adjusting onset times and preserving the description.
    Results are returned in chronological order by 'onset'.

    Args:
        annotations (list): List of dicts with keys 'onset', 'duration', 'description'

    Returns:
        list: New list of annotations (split where necessary), sorted by 'onset'
    """

    insert = []

    for index, ann in annotations.iterrows():
        if label == 'CAP':
            duration = ann['Final_Duration']
        if label == 'Sleep_EDF':
            duration = ann['onset']

        if duration == 30:
            # Keep as-is if duration ≤ 30s
            if label == 'CAP':
                ann_dict = ann.to_dict()
                insert.append(ann_dict)
            if label == 'Sleep_EDF':
                insert.append(ann)
        else:
            # Split into 30-second segments
            num_segments = int(duration // 30)  # Fixed: was //3 (bug)
            remainder = duration % 30
            print('num_segments', num_segments)
            # Create full 30-second segments
            if num_segments < 0:
                print(f'num_segments < 0', num_segments )
                pass
            else:
                for i in range(num_segments):
                    if label == 'CAP':
                        new_ann = {
                        'Time [hh:mm:ss]': ann['Time [hh:mm:ss]'] + pd.Timedelta(seconds=30 * i),
                        'Final_Duration': 30,
                        'Event': ann['Event']
                        }
                    if label == 'Sleep_EDF':
                        new_ann = {
                        'onset': ann['onset'] + i * 30,
                        'duration': 30,
                        'description': ann['description']
                        }
                    print('new_ann', new_ann)
                    insert.append(new_ann)

                # Handle remainder if any
                if remainder > 0:
                    if label == 'CAP':
                        new_ann = {
                        'Time [hh:mm:ss]': ann['Time [hh:mm:ss]'] + pd.Timedelta(seconds=30 * i),
                        'Final_Duration': 30,
                        'Event': ann['Event']
                        }

                    if label == 'Sleep_EDF':
                        new_ann = {
                        'onset': ann['onset'] + i * 30,
                        'duration': 30,
                        'description': ann['description']
                        }
                    print('new_ann', new_ann)
                    insert.append(new_ann)

    # Sort by onset to ensure chronological order
    if label == 'CAP':
        insert.sort(key=lambda x: x['Time [hh:mm:ss]'])
    if label == 'Sleep_EDF':
        insert.sort(key=lambda x: x['onset'])

    return insert


def prepare_data_for_hypnogram(fname_txt, folder_metrics_path, subject):
    # for Haaglanden Medisch Centrum sleep staging database
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
    # Filter out not stages
    mask = ~hypno_modified.isin(['Lights off', 'Lights on'])
    hypno_filtered = hypno_modified[mask]
    # hypno_filtered.name = 'Annotation'
    # Save the modified DataFrame to a new CSV file
    hypno_filtered.name = 'Annotation'
    fname = folder_metrics_path + "/{}_annotations_doctor.csv".format(subject)
    hypno_filtered.to_csv(fname, index=False)

    return hypno_filtered


def plot_hypnogram(fname_pics, hypno_filtered):
    ax = yasa.plot_hypnogram(hypno_filtered)
    fig = ax.get_figure()
    fig.set_size_inches(35, 6)
    fig.savefig(fname_pics, dpi=300, bbox_inches='tight')
    plt.close(fig)


def plot_spectrogram(fname_pics, chan, sf, hypno_filtered, raw):
    # Upsample our hypnogram from 0.333 Hz to 100 Hz
    print('raw.ch_names', raw.ch_names)
    hypno_up = yasa.hypno_upsample_to_data(hypno_filtered, sf_hypno=1 / 30, data=raw)
    data = raw.get_data(units="uV")
    # ax = yasa.plot_spectrogram(data[chan.index("EEG C4-M1")], sf, hypno_up)
    # ax = yasa.plot_spectrogram(data[chan.index("EEG Pz-Oz")], sf, hypno_up)
    channel_options = ["C4-A1", "C3-A2", "C4A1", "C4"]
    for ch in channel_options:
        if ch in raw.ch_names:
            channel_name = ch

    idx = raw.ch_names.index(channel_name)
    ax = yasa.plot_spectrogram(data[idx], sf, hypno_up)
    fig = ax.get_figure()
    fig.set_size_inches(35, 6)
    fig.savefig(fname_pics, dpi=300, bbox_inches='tight')
    plt.close(fig)

def process_anns(annotations, cols, col_name):

    annotations_clean, cols_clean  = remove_col(annotations, cols, 'Position', ['Unknown Position', 'N/A', 'Prone', 'Supine', 'Right', 'Left'])

    annotations_pd = pd.DataFrame(annotations_clean, columns=cols_clean)
    annotations_pd = annotations_pd.iloc[1:].reset_index(drop=True)

    clean_times = annotations_pd[col_name].astype(str).str.strip().str.replace('.', ':', regex=False)
    annotations_pd[col_name] = pd.to_timedelta(clean_times)
    annotations_pd[col_name].to_csv('time_parsed.csv', index=False, header=['Time_parsed'])

    mask = annotations_pd['Event'].isin(['SLEEP-S0', 'SLEEP-S1', 'SLEEP-S2', 'SLEEP-S3', 'SLEEP-S4', 'SLEEP-REM'])
    annotations_filt = annotations_pd[mask]

    return  annotations_filt

def yasa_staging(fname_pics, raw):
    # Sleep Extended
    # sls = yasa.SleepStaging(raw, eeg_name="EEG Pz-Oz", eog_name='EOG horizontal', emg_name='EMG submental')
    # Haagladen
    # sls = yasa.SleepStaging(raw, eeg_name="EEG C4-M1", eog_name = "EOG E1-M2", emg_name = "EMG chin")
    print('raw.ch_names', raw.ch_names)
    eeg_options = ["C4-A1", "C4A1", "C4", 'C3-A2']
    emgs_options = ["EMG1-EMG2", "EMG-EMG","CHIN-1", "CHIN1", "EMG1"]
    eogs_options = ["LOC", "LOC-A1", "ROC-LOC", "LOC-A2", "EOG-L", "EOG sin"]
    eeg_name = []
    eog_name = []
    emg_name = []
    for ch in eeg_options:
        if ch in raw.ch_names:
            eeg_name = ch
    for ch in emgs_options:
        if ch in raw.ch_names:
            emg_name = ch
    for ch in eogs_options:
        if ch in raw.ch_names:
            eog_name = ch
    if emg_name:
        sls = yasa.SleepStaging(raw, eeg_name=eeg_name, eog_name=eog_name, emg_name=emg_name)
    else:
        sls = yasa.SleepStaging(raw, eeg_name=eeg_name, eog_name=eog_name)
    hypno_pred = sls.predict()  # Predict the sleep stages
    hypno_pred = yasa.hypno_str_to_int(hypno_pred)  # Convert "W" to 0, "N1" to 1, etc
    ax = yasa.plot_hypnogram(hypno_pred)  # Plot
    fig = ax.get_figure()
    fig.set_size_inches(35, 6)
    fig.savefig(fname_pics, dpi=300, bbox_inches='tight')
    plt.close(fig)

    return hypno_pred


def average_recall(results_dict):
    # Recall = Sensitivity: Recall = True Positives / (True Positives + False Negatives)
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


def average_sensitivity(doctor_hypno_scoring, hypno_pred):
    # Recall = Sensitivity: Recall = True Positives / (True Positives + False Negatives)

    cm = confusion_matrix(doctor_hypno_scoring, hypno_pred)

    # Multi-class
    total = np.sum(cm)
    sensitivities = []
    for i in range(cm.shape[0]):
        TP = cm[i, i]
        FP = np.sum(cm[i, :]) - TP
        FN = np.sum(cm[:, i]) - TP
        TN = total - (TP + FP + FN)
        sens = TP / (TP + FN) if (TP + FN) > 0 else 0
        sensitivities.append(sens)

    return np.round(np.mean(sensitivities), 2)


def average_PPV(doctor_hypno_scoring, hypno_pred):
    # Precision/Positive Predictive Value (PPV) = TP/(TP + FP)
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
    # FPR = FP/(FP + TN)
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
        print(
            f"yasa_annotations_data: {len(yasa_annotations_data)} строк, doctor_annotations_data: {len(doctor_annotations_data)} строк")
        print("Сравнение будет выполнено только для общего количества строк")
        min_length = min(len(yasa_annotations_data), len(doctor_annotations_data))
    else:
        min_length = len(yasa_annotations_data)

    # Сравниваем построчно и выводим результат
    for i in range(min_length):
        is_match = yasa_annotations_data[i] == doctor_annotations_data[i]
        # print(f"{i + 1:6} | {yasa_annotations_data[i]:11} | {doctor_annotations_data[i]:11} | {is_match}")

        # Или просто вывод True/False для каждой строки:
        # print(is_match)

    # Дополнительная статистика
    matches = sum(1 for i in range(min_length) if yasa_annotations_data[i] == doctor_annotations_data[i])
    total = min_length
    accuracy = matches / total if total > 0 else 0

    # print(f"\nСтатистика сравнения:")
    # print(f"Всего строк: {total}")
    # print(f"Совпадений: {matches}")
    # print(f"Несовпадений: {total - matches}")
    print(f"Точность совпадения: {accuracy:.2%}")

    return round(accuracy, 2)
