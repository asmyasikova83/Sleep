#Derives and stores sleep statistics (Time in bed, Latency N1-3/REM, Share of N1-3/REM, Sleep efficicency
# for each subject from YASA package in {subject}_sleep_statistics.json"

import os
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore")
from functions import (preprocessing, prepare_data_for_hypnogram, plot_hypnogram,
                      plot_spectrogram, yasa_staging, compare_annotations)
import yasa
from yasa import sleep_statistics
import json

import warnings
warnings.filterwarnings("ignore")
from functions import (preprocessing, prepare_data_for_hypnogram, plot_hypnogram,
                      plot_spectrogram, yasa_staging, compare_annotations)

folder_data =  r'C:\Users\msasha\PycharmProjects\Sleep\data\haaglanden-medisch-centrum-sleep-staging-database-1.1\recordings'
folder_statistics_path = r"C:\Users\msasha\PycharmProjects\Sleep\sleep_statistics"

for idx in range(1, 155):
    if idx < 10:
        subject = "SN00{}".format(idx)
    elif idx > 9 and idx < 100:
        subject = "SN0{}".format(idx)
    else:
        assert(idx > 99)
        subject = "SN{}".format(idx)

    fname_edf = os.path.join(folder_data, f"{subject}.edf")
    # Get and process the data (channels, resampling, filter)
    try:
        [raw, chan, sf] = preprocessing(fname_edf)
    except Exception as FileNotFoundError:
        print(f"Error processing file {fname_edf}: {FileNotFoundError}")
        continue

    # Mapping
    # 0 = Wake, 1 = N1 sleep, 2 = N2 sleep, 3 = N3 sleep and 4 = REM sleep
    fname_txt = folder_data + "\{}_sleepscoring.txt".format(subject)
    hypno_filtered = prepare_data_for_hypnogram(fname_txt, subject)

    # Only integers for sleep stages needed
    hypno_filtered = hypno_filtered.iloc[1:]
    hypno_numeric = hypno_filtered.astype(int)

    # Assuming that we have one-value per 30-second.
    stat = sleep_statistics(hypno_numeric, sf_hyp=1/30)

    fname_stat = folder_statistics_path + "\{}_sleep_statistics.json".format(subject)
    # JSON
    with open(fname_stat, 'w', encoding='utf-8') as f:
        json.dump(stat, f, ensure_ascii=False, indent=4)

    print(f"Статистика сохранена в {fname_stat}")

