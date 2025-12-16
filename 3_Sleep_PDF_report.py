#Loads sleep statistics for each subjects and puts it in PDF
#with a hypnogram, spectrogram
#Stores the PDF in {subject}_sleep_statistics.pdf


from fpdf import FPDF, XPos, YPos
import os
import json
import warnings
warnings.filterwarnings("ignore")

def create_sleep_statistics_pdf(subject, stat, output_folder):
    """
    Создает PDF файл со статистикой сна для субъекта
    """

    # Создаем PDF объект
    pdf = FPDF(orientation='L')
    pdf.add_page()

    def format_duration(value):
        """
        Форматирует длительность в минутах с округлением минут
        """
        try:
            minutes = float(value)
            hours = int(minutes // 60)
            remaining_minutes = round(minutes % 60)  # Округляем минуты
            return f"{hours} часов {remaining_minutes} минут"
        except (ValueError, TypeError):
            return str(value)


    # Добавляем шрифт DejaVu Sans с поддержкой кириллицы
    font_path = r'C:\Users\msasha\PycharmProjects\Sleep\dejavu-sans-ttf-2.37\ttf\DejaVuSans.ttf'

    # Register only the regular style of the DejaVu font
    pdf.add_font('DejaVu', '', font_path)  # Убрали uni=True
    # Обязательно установка шрифта перед добавлением текста
    pdf.set_font("DejaVu", size=12)
    # Заголовок
    pdf.cell(200, 10, text=f"Статистика сна для {subject}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")

    # Subject info
    pdf.cell(200, 10, text=f"Субъект: {subject}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Table
    pdf.set_fill_color(200, 220, 255)
    pdf.set_font("DejaVu", '', 12)  # Используем DejaVu для заголовков (обычный стиль)

    pdf.cell(200, 10, "Параметр", border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, align='C', fill=True)
    pdf.cell(70, 10, "Значение", border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C', fill=True)

    pdf.set_font("DejaVu", '', 11)  # Используем DejaVu для данных (обычный стиль)

    # Data

    if stat:
        for key, value in stat.items():
            pdf.multi_cell(200, 10, key, border=1, new_x=XPos.RIGHT, new_y=YPos.TOP, align='L')

            if '%' in key:
                display_value = f"{int(float(value))}%"  # выводим значение без форматирования
            else:
                display_value = format_duration(value)  # применяем форматирование

            pdf.multi_cell(70, 10, display_value, border=1, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')

    #Image
    pdf.ln(20)  # Blankspace
    pdf.image(image_path, x=10, y=None, w=250) # image_path, x=left, y=top, w=width. None means that aspect ratio is kept.

    # Save PDF
    filename = os.path.join(output_folder, f"{subject}_sleep_statistics.pdf")
    pdf.output(filename)
    print(f"{filename} создан")




folder_statistics_path = r"C:\Users\msasha\PycharmProjects\Sleep\sleep_statistics"
output_folder = r"C:\Users\msasha\PycharmProjects\Sleep\PDF"

subject = input("Введите имя испытуемого (от SN001 до SN154) + enter или 'exit', чтобы выйти: ").strip()

if subject.lower() == 'exit':
    print("Вы вышли из процесса.")


image_path = r"C:\Users\msasha\PycharmProjects\Sleep\pics\spectrogram_{}_doctor.png".format(subject)
fname_stat = folder_statistics_path + "\{}_sleep_statistics.json".format(subject)


# JSON
try:
    with open(fname_stat, 'r', encoding='utf-8') as f:
        stat = json.load(f)
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

        # Replace the key
        stat_rus = {}
        for key, value in stat.items():
            desc = descriptions.get(key, key)
            stat_rus[desc] = value

        create_sleep_statistics_pdf(subject, stat_rus, output_folder)
except FileNotFoundError:
    print(f"Файл {fname_stat} не найден")
    stat = {}  # или другое значение по умолчанию


