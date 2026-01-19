import os
import sys
import time
import mne
import yasa
import matplotlib.pyplot as plt
from fpdf import FPDF, XPos, YPos
import logging

def set_logger():
    # Set the logger
    # Clean the pipeline.log

    with open('logs.log', 'w', encoding='utf-8') as f:
        f.write('')

    print("Файл logs.log очищен.")
    logging.getLogger().handlers = []

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.propagate = False  # отключаем наследование
    logger.handlers.clear()

    # FileHandler
    file_handler = logging.FileHandler('logs.log', encoding='utf-8')
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
    )
    logger.addHandler(file_handler)

    # StreamHandler (console)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
    )
    logger.addHandler(console_handler)
    return logger

def check_ready(deadline):
    # Waiting for imports to be completed

    return (
        os.path.exists("data/output.txt") or
        time.time() >= deadline
    )

def preprocessing(fname_edf):
    """
    Preprocessing of PSG files (EDF) .

    Arguments:
        fname_edf (str): path to EDF‑file.

    Returns:
        raw (mne.Raw): raw EEG recording.
        chan (list): chan names.
        sf (float): sampling rate.
    """

    # 1. EDF loading
    raw = mne.io.read_raw_edf(fname_edf, preload=True)
    chan = raw.ch_names

    # 2. Resampling and filtering
    raw.resample(100)  # ресемплинг до 100 Гц
    sf = raw.info["sfreq"]  # новая частота дискретизации
    raw.filter(0.3, 40)  # полосовой фильтр (0.3–40 Гц)

    return raw, chan, sf

def plot_hypnogram(fname_pics, hypno_filtered):
    # Based on YASA's annotations plots a hypnogram

    ax = yasa.plot_hypnogram(hypno_filtered)
    fig = ax.get_figure()
    fig.set_size_inches(35, 6)
    fig.savefig(fname_pics , dpi=300, bbox_inches='tight')
    plt.close(fig)

def plot_spectrogram(fname_pics, chan, sf, hypno_filtered, raw):
    # Based on YASA's annotations and raw recordings plots a combined hypnogram/spectrogram

    # Upsample our hypnogram from 0.333 Hz to 100 Hz
    hypno_up = yasa.hypno_upsample_to_data(hypno_filtered, sf_hypno=1 / 30, data=raw)
    data = raw.get_data(units="uV")
    ax = yasa.plot_spectrogram(data[chan.index("EEG C4-M1")], sf, hypno_up)
    fig = ax.get_figure()
    fig.set_size_inches(35, 6)
    fig.savefig(fname_pics, dpi=300, bbox_inches='tight')
    plt.close(fig)

def yasa_staging(fname_pics, raw):
    # Core function: based on raw recording from
    # selected chans performs automated sleep scoring

    #Better results with EOG and submental EMG
    sls = yasa.SleepStaging(raw, eeg_name="EEG C4-M1", eog_name="EOG E2-M2", emg_name="EMG chin")
    hypno_pred = sls.predict()
    # Convert "W" to 0, "N1" to 1, etc
    hypno_pred = yasa.hypno_str_to_int(hypno_pred)

    return hypno_pred

def create_sleep_statistics_pdf(subject, stat, output_folder, image_path):
    # Builds a PDF file with sleep statistics and hypnogram/spectrogram

    descriptions = {
        "TIB": "Время в кровати",
        "SPT": "Время с первого до последнего цикла сна",
        "WASO": "Общая продолжительность бодрствования после засыпания",
        "TST": "Общая продолжительность сна (N1 + N2 + N3 + REM)",
        "N1": "Фаза сна N1",
        "N2": "Фаза сна N2",
        "N3": "Фаза сна N3",
        "REM": "Фаза сна REM: быстрое движение глаз",
        "NREM": "Фазы сна без REM: NREM = N1 + N2 + N3",
        "SOL": "Время от начала процесса засыпания до первой стадии сна",
        "Lat_N1": "Время/Латентность от начала записи до начала стадии сна N1",
        "Lat_N2": "Время/Латентность от начала записи до начала стадии сна N2",
        "Lat_N3": "Время/Латентность от начала записи до начала стадии сна N3",
        "Lat_REM": "Время/Латентность от начала записи до начала стадии сна REM",
        "%N1": "Общая продолжительность сна N1 (в %) от общей продолжительности сна",
        "%N2": "Общая продолжительность сна N2 (в %) от общей продолжительности сна",
        "%N3": "Общая продолжительность сна N3 (в %) от общей продолжительности сна",
        "%REM": "Общая продолжительность сна REM (в %) от общей продолжительности сна",
        "%NREM": "Общая продолжительность сна NREM = N1 + N2 + N3 (в %) от общей продолжительности сна",
        "SE": "Эффективность сна = Общая продолжительность сна / Время в кровати * 100 (%)",
        "SME": "Эффективность поддержания сна = Общая продолжительность сна / Время с первого до последнего цикла сна * 100 (%)"
    }

    def format_duration(value):
        #Format time: hours and minutes
        try:
            minutes = float(value)
            hours = int(minutes // 60)
            remaining_minutes = round(minutes % 60)
            return f"{hours} часов {remaining_minutes} минут"
        except (ValueError, TypeError):
            return str(value)

    # Replace English abbreviations with Russian descriptions
    stat_rus = {}
    for key, value in stat.items():
            desc = descriptions.get(key, key)
            stat_rus[desc] = value

    # Create PDF object
    pdf = FPDF(orientation='L')
    pdf.add_page()

    # Add DejaVu Sans for cyrillic
    font_path = r'C:\Users\msasha\PycharmProjects\Sleep\dejavu-sans-ttf-2.37\ttf\DejaVuSans.ttf'

    # Register only the regular style of the DejaVu font
    pdf.add_font('DejaVu', '', font_path)
    pdf.set_font("DejaVu", size=12)

    # Title
    pdf.cell(200, 10, text=f"Статистика сна для {subject}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")

    # Subject info
    pdf.cell(200, 10, text=f"Испытуемый: {subject}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Table
    pdf.set_fill_color(200, 220, 255)
    pdf.set_font("DejaVu", '', 12)  # Используем DejaVu для заголовков (обычный стиль)

    pdf.cell(200, 10, "Параметр", border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, align='C', fill=True)
    pdf.cell(70, 10, "Значение", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C', fill=True)

    pdf.set_font("DejaVu", '', 11)  # Используем DejaVu для данных (обычный стиль)

    # Data
    if stat_rus:
        for key, value in stat_rus.items():
            pdf.multi_cell(200, 10, key, border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, align='L')

            if '%' in key:
                display_value = f"{int(float(value))}%"  # выводим значение без форматирования
            else:
                display_value = format_duration(value)  # применяем форматирование

            pdf.multi_cell(70, 10, display_value, border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')

    #Image
    pdf.ln(20)
    pdf.image(image_path, x=10, y=None, w=250) # image_path, x=left, y=top, w=width. None means that aspect ratio is kept.

    # Save PDF
    filename = os.path.join(output_folder, f"{subject}_sleep_statistics.pdf")
    pdf.output(filename)
