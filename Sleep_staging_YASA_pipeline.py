#Loads, prepocesses (filters, resamples) the data;
#Launches YASA and stores {subject}_annotations_yasa.csv with mapped to int classification of sleep stages
#Plots hypnograms and spectrograms for each subject;
#Builds PDF with sleep statistics and plots

import sys
import time
from pathlib import Path
import json
import pandas as pd
from functions_pipeline import check_ready
import warnings
warnings.filterwarnings("ignore")

print(f"[{time.time():.1f}] Импорты стандартных библиотек завершены")
print("Сейчас будем долго грузить функции  этого модуля, сходите за кофе...", end=" ", flush=True)

deadline = time.time() + 60  # ждать максимум 60 секунд
while not check_ready(deadline):
    print(".", end="", flush=True)
    time.sleep(0.5)
print("Готово!")

from functions_pipeline import (
    set_logger,
    preprocessing,
    plot_hypnogram,
    plot_spectrogram,
    yasa_staging,
    create_sleep_statistics_pdf
)
print(f"[{time.time():.1f}] Импорт функций завершён")
from yasa import sleep_statistics
print(f"[{time.time():.1f}] Импорт yasa sleep_statistics завершён")

#Logging
logger = set_logger()

# 1. Provide patient's name
subject = input("Введите имя испытуемого (например, SN001): ").strip()
if not subject:
    logger.warning("[ERROR] Имя испытуемого не может быть пустым.")
    sys.exit(1)
logger.info(f"[INFO] Обработка испытуемого: {subject}")

# 2. Paths
folder_data = Path(
    r"C:\Users\msasha\PycharmProjects\Sleep_16Jan2026\data\haaglanden-medisch-centrum-sleep-staging-database-1.1\recordings")
folder_pics_path = Path(r"C:\Users\msasha\PycharmProjects\Sleep\pics\pipeline")
folder_metrics_path = Path(r"C:\Users\msasha\PycharmProjects\Sleep\yasa_annotations_metrics")
folder_statistics_path = Path(r"C:\Users\msasha\PycharmProjects\Sleep\sleep_statistics")
folder_PDF = Path(r"C:\Users\msasha\PycharmProjects\Sleep\PDF\pipeline")

# Create dirs
for folder in [folder_pics_path, folder_metrics_path, folder_statistics_path, folder_PDF]:
    folder.mkdir(parents=True, exist_ok=True)

# 3. Preprocessing of an EDF-file
fname_edf = folder_data / f"{subject}.edf"
try:
    raw, chan, sf = preprocessing(
        fname_edf=str(fname_edf)
    )
    logger.info(f"[OK] EDF‑файл обрабатывается: {fname_edf}")
except FileNotFoundError:
    logger.warning(f"[ERROR] EDF‑файл не найден: {fname_edf}")
    sys.exit(1)

# 4. Automated sleep scoring (YASA)
hypno_pics = folder_pics_path / f"hypnogram_{subject}_yasa.png"
hypno_predicted = yasa_staging(hypno_pics, raw)
logger.info(f"[OK] Стадирование YASA завершено")

# Save YASA's annotations
yasa_annotations_path = folder_metrics_path / f"{subject}_annotations_yasa.csv"
pd.DataFrame({'Annotation': hypno_predicted}).to_csv(yasa_annotations_path, index=False)
logger.info(f"[OK] Аннотации YASA сохранены: {yasa_annotations_path}")

# 5. Plots
# Hypnogram
plot_hypnogram(hypno_pics, hypno_predicted)
logger.info(f"[OK] Гипнограмма сохранена: {hypno_pics}")

# Spectrogram
spectro_pics = folder_pics_path / f"spectrogram_{subject}_yasa.png"
plot_spectrogram(spectro_pics, chan, sf, hypno_predicted, raw)
logger.info(f"[OK] Спектрограмма сохранена: {spectro_pics}")

# 6. Sleep statistics
stat = sleep_statistics(hypno_predicted, sf_hyp=1 / 30)  # 30‑секундные эпохи
logger.info("[OK] Статистика сна рассчитана")

# Save sleep statistics in JSON
fname_stat = folder_statistics_path / f"{subject}_sleep_statistics.json"
with open(fname_stat, 'w', encoding='utf-8') as f:
    json.dump(stat, f, ensure_ascii=False, indent=4)
logger.info(f"[OK] Статистика сохранена: {fname_stat}")

# 8. Build a report in PDF‑
# Add DejaVu Sans for cyrillic
font_path = r'C:\Users\msasha\PycharmProjects\Sleep\dejavu-sans-ttf-2.37\ttf\DejaVuSans.ttf'
create_sleep_statistics_pdf(subject, stat, folder_PDF, spectro_pics, font_path)
logger.info(f"[OK] PDF‑отчёт создан: {folder_PDF / subject}_report.pdf")
