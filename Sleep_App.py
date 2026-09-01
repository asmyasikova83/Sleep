
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
from pathlib import Path
import os
import subprocess
import shutil
from pathlib import Path
import time
import json
import pandas as pd
import mne
import numpy as np
from functions_pipeline import check_ready, set_logger, preprocessing, plot_hypnogram, plot_spectrogram, yasa_staging, create_sleep_statistics_pdf
from yasa import sleep_statistics
import warnings
warnings.filterwarnings("ignore")


class SleepApp:
    def __init__(self, root):

        self.root = root
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        self.root.title("Sonya")

        # --- Основной интерфейс: заголовок ---
        tk.Label(
            root,
            text="Sonya: system of automated sleep staging and visualization",
            font=("Arial", 14, "bold"),
            pady=20
        ).pack()  # Размещаем сразу после создания

        # --- Фрейм для кнопок ---
        self.btn_frame = tk.Frame(root)
        self.btn_frame.pack(pady=30)  # pady создаёт отступ от заголовка

        # Настройка сетки внутри фрейма (для выравнивания кнопок)
        self.btn_frame.columnconfigure(0, weight=1)  # Растягиваем колонку на всю ширину
        for i in range(3):  # Настраиваем все строки (0–2)
            self.btn_frame.rowconfigure(i, weight=1)

        # --- Создаём кнопки ---
        self.create_buttons()

        # Создаём фрейм для сообщения с отступами
        self.message_frame = tk.Frame(self.root, bg='#333333', padx=15,
                                      pady=10)  # тёмно‑серый фон, отступы 15 px по горизонтали, 10 px по вертикали
        self.message_frame.pack(fill='x', side='top', padx=10,
                                pady=5)  # отступ от краёв окна: 10 px слева/справа, 5 px сверху/снизу

        # Создаём метку для текста сообщения
        self.status_label = tk.Label(
            self.message_frame,
            text="",
            fg='white',  # белый шрифт
            bg='black',  # тёмно‑серый фон (совпадает с фреймом)
            font=('Arial', 11),  # обычный шрифт, чуть меньше для многострочности
            wraplength=650,  # перенос строк при достижении 650 px
            justify='left',  # выравнивание по левому краю
            anchor='nw'  # привязка к северо‑западному углу (верхний левый)
        )
        self.status_label.pack(fill='both', expand=True)
        self.update_window_title("")

        # Пути
        # Определяем корневую папку — текущую рабочую директорию
        self.root_dir = Path(".")  # или Path.cwd()
        self.root_abs = self.root_dir.resolve()
        # Setting up logger
        self.logger = set_logger()

        # Создаём пути к подпапкам (относительно текущей директории)
        self.folder_yasa = self.root_abs / "yasa_annotations_metrics"
        self.folder_pics_path = self.root_abs / "pics"
        self.folder_statistics_path = self.root_abs / "sleep_statistics"
        self.folder_PDF = self.root_abs / "PDF"
        self.folder_data_anns = self.root_abs / "data_anns"
        self.font_path = self.root_abs / "dejavu-sans-ttf-2.37"/"ttf"/"DejaVuSans.ttf"
        self.edfbrowser_path = Path(r"C:\Program Files\EDFbrowser\edfbrowser.exe")
        self.converter_path = Path(r"C:\Program Files\MCS\NeoRec\ConverterStandalone.exe")

        # Создаём все папки при инициализации (если их нет)
        self.create_output_directories()

        # Хранилище последнего выбранного пути (можно сохранить в конфиг)
        self.last_data_dir = None
        self.last_patient_name = None

        # Флаг состояния: какая операция выполнена
        self.step_completed = {
            "load_raw_eeg": False,
            "create_show_report": False,
            "save_show_edf": False
        }

        # Порядок команд в меню (для удобства)
        self.menu_commands = [
            "load_raw_eeg",
            "create_show_report",
            "save_show_edf"
        ]

        self.setup_menu()  # Выносим меню в отдельный метод

    def create_output_directories(self):
        """Создаёт все необходимые выходные папки."""
        folders = [
            self.folder_yasa,
            self.folder_pics_path,
            self.folder_statistics_path,
            self.folder_PDF,
            self.folder_data_anns
        ]

        for folder in folders:
            try:
                folder.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"[OK] Папка создана/проверена: {folder}")
            except Exception as e:
                self.logger.error(f"[ERROR] Не удалось создать папку {folder}: {e}")

    def create_buttons(self):
        # Кнопка 0: Загрузить EEG
        self.btn_load_raw_eeg = tk.Button(
                self.btn_frame,
                text="Load EEG",
                bg="white",
                fg="purple",
                font=("Arial", 11),
                width=55,
                command=self.load_raw_edf
        )
        self.btn_load_raw_eeg.grid(row=0, column=0, padx=20, pady=(15, 10), sticky="ew")

        # Кнопка 1: Создать отчёт и показать PDF-отчет
        self.btn_create_show_report = tk.Button(
                self.btn_frame,
                text="Create and show PDF-report",
                bg="white",
                fg="purple",
                font=("Arial", 11),
                width=25,
                command=self.create_show_report,
                state="disabled"  # Изначально отключена
        )
        self.btn_create_show_report.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        # Кнопка 2: Сохранить и показать ЭЭГ со стадированием
        self.btn_save_show_edf = tk.Button(
                self.btn_frame,
                text="Save and show EEG",
                bg="white",
                fg="purple",
                font=("Arial", 11),
                width=25,
                command=self.save_show_edf,
                state="disabled"
        )
        self.btn_save_show_edf.grid(row=2, column=0, padx=20, pady=(10, 15), sticky="ew")

    def update_menu_state(self):
        """Включает/отключает пункты меню в зависимости от выполненных шагов."""
        # Load EEG — всегда доступна (начальная точка)
        self.data_menu.entryconfig("Load EEG", state="normal")

        # Create and show PDF-report — доступна только после Load EEG
        if self.step_completed["load_raw_eeg"]:
            self.data_menu.entryconfig("Create and show PDF-report ", state="normal")
        else:
            self.data_menu.entryconfig("Create and show PDF-report ", state="disabled")

        # Save and show EEG — доступна только после Create and show PDF-report
        if self.step_completed["create_show_report"]:
            self.data_menu.entryconfig("Save and show EEG", state="normal")
        else:
            self.data_menu.entryconfig("Save and show EEG", state="disabled")

        # About и Exit — всегда доступны
        self.data_menu.entryconfig("About", state="normal")
        self.data_menu.entryconfig("Exit", state="normal")

    def setup_menu(self):
        self.menu = tk.Menu(self.root)
        self.root.config(menu=self.menu)

        self.data_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Menu", menu=self.data_menu)

        self.data_menu.add_command(label="About", command=self.show_about)
        self.data_menu.add_command(label="Load EEG", command=self.load_raw_edf)
        self.data_menu.add_command(label="Create and show PDF-report ", command=self.create_show_report)
        self.data_menu.add_command(label="Save and show EEG", command=self.save_show_edf)
        self.data_menu.add_command(label="Exit", command=self.exit_app)

        # Первоначальная настройка состояния меню
        self.update_menu_state()

    def show_about(self):
        messagebox.showinfo(
            "О программе",
            "Соня: cистема просмотра и анализа записей сна \n"
            "Версия: 1.0\n"
            "Разработчик: Александра\n\n"
            "Использует YASA для автоматической классификации стадий и рассчета статистики сна\n\n"
            "Использует EDFbrowser для визуализации .edf-файлов\n\n"
        )

    def update_window_title(self, message=""):
        """Обновляет текст в статус‑метке под кнопками (синее окно).
        Если сообщение слишком длинное — обрезает его."""
        max_length = 120  # Увеличили лимит для большого окна

        if message:
            # Обрезаем сообщение, если оно длиннее max_length
            if len(message) > max_length:
                message = message[:max_length - 3] + "..."
            # Обновляем текст метки
            self.status_label.config(text=message)
        else:
            # Очищаем окно, если сообщение пустое
            self.status_label.config(text="")

    def get_name_edf_file(self):
        """
        Запрашивает имя пациента и путь к EDF‑файлу.
        Возвращает: (patient_name: str, edf_file: Path) или (None, None) при ошибке.
        """
        # 1. Интерактивный выбор файла с записью пациента
        edf_file = self.load_raw_edf()

        patient_name = Path(edf_file).stem

        self.update_window_title(f"Имя пациента: {patient_name} / Patient's name:  {patient_name}")

        return patient_name, edf_file

    def load_raw_edf(self):
        """
        Предлагает пользователю:
        1. Выбрать .edf‑файл для загрузки.
        2. Выбрать папку, куда скопировать этот файл.
        Если исходная и целевая папки совпадают — файл не копируется,
        возвращается исходный путь. Иначе — копирует и возвращает путь к копии.
        """

        # Шаг 0: выбираем исходную папку (где лежит EDF)
        initial_dir = str(self.last_data_dir) if self.last_data_dir else "/"
        src_dir = filedialog.askdirectory(
            initialdir=initial_dir,
            title="Выберите папку с EDF‑файлами / Select EDF source folder"
        )
        if not src_dir:
            self.update_window_title("Выбор папки отменён / Folder selection cancelled")
            return None

        src_path = Path(src_dir)

        # Шаг 1: выбираем сам EDF‑файл
        file = filedialog.askopenfilename(
            initialdir=src_dir,
            title="Выберите файл для загрузки / Choose file to load",
            filetypes=[("All files", "*.*")] #("EDF files", "*.edf"),
        )

        if not file:
            self.update_window_title("Выбор файла отменён / EDF file selection cancelled")
            return None

        file_path = Path(file)
        patient_name = Path(file).stem

        # 2. Проверяем, изменился ли пациент
        if self.last_patient_name != patient_name:
            # Пациент сменился — сбрасываем состояние шагов
            self.step_completed = {
                "load_raw_eeg": True,  # считаем, что загрузка выполнена (мы только что выбрали файл)
                "create_show_report": False,
                "save_show_edf": False
            }
            self.update_menu_state()
            self.btn_create_show_report.config(state="disabled")
            self.btn_save_show_edf.config(state="disabled")
            self.logger.info(f"[INFO] Сменился пациент. Сброс состояния шагов. Новый пациент: {patient_name}")

        # 2. Сохраняем имя текущего пациента как последнее
        self.last_patient_name = patient_name

        # Проверка расширения
        if file_path.suffix.lower() != '.edf':
            edf_file = self.convert_edf(file, patient_name)
            file_path = Path(edf_file)
            self.update_window_title("Файл с расширением .edf создан / An .edf file created")

        # Шаг 4: выбираем целевую папку
        dest_dir = filedialog.askdirectory(
            title="Выберите целевую папку для EDF‑файла / Select destination folder for EDF-file"
        )
        if not dest_dir:
            self.update_window_title("Выбор целевой папки отменён / Destination folder selection cancelled")
            return None

        dest_path = Path(dest_dir) / file_path.name  # Полный путь к копии

        # Шаг 5: проверяем, совпадают ли исходная и целевая папки
        if src_path.resolve() == dest_path.parent.resolve():
            # Папки совпадают: не копируем, возвращаем исходный путь
            self.update_window_title(
                f"Файл уже в целевой папке: {file_path.name} / File already in destination: {file_path.name}"
            )
            self.btn_create_show_report.config(state="normal")
            self.step_completed["load_raw_eeg"] = True
            self.update_menu_state()
            self.root.after(3000, lambda: self.update_window_title(""))

            return file_path  # Возвращаем исходный путь

        # Шаг 6: копируем файл (папки различаются)
        try:
            shutil.copy2(file_path, dest_path)  # copy2 сохраняет метаданные
            self.update_window_title(
                f"Файл скопирован: {dest_path.name} / File copied: {dest_path.name}"
            )
            self.root.after(3000, lambda: self.update_window_title(""))
            self.btn_create_show_report.config(state="normal")
            self.step_completed["load_raw_eeg"] = True
            self.update_menu_state()
            return dest_path  # Возвращаем путь к скопированному файлу

        except Exception as e:
            self.update_window_title(f"Ошибка копирования: {e} / Copy error: {e}")
            return None

    def create_show_report(self):
        """Запускает процесс создания отчёта через YASA в отдельном потоке с логированием."""

        patient_name, edf_file = self.get_name_edf_file()

        if not patient_name:
            return

        self.logger.info(f"[INFO] Начало обработки: {patient_name}")
        self.update_window_title(f"Начало обработки: {patient_name} / Processing: {patient_name}")

        # 2. Пути к директориям
        folder_pics_path = self.folder_pics_path
        folder_yasa = self.folder_yasa
        folder_statistics_path = self.folder_statistics_path
        folder_PDF = self.folder_PDF
        font_path = self.font_path

        # 3. Препроцессинг
        self.logger.info(f"[INFO] Начинаю препроцессинг: {edf_file}")
        self.update_window_title(f"Начинаю препроцессинг: {patient_name} / Preprocessing initiated : {patient_name}" )
        raw, chan, sf = preprocessing(fname_edf=str(edf_file))
        self.logger.info("[OK] Препроцессинг завершён")
        self.update_window_title(f"Препроцессинг завершён: {patient_name} / Preprocessing completed:{patient_name}")

        # 4. YASA: стадирование сна
        self.logger.info("[INFO] Запускаю YASA для стадирования сна")
        self.update_window_title(f"Cтадирование сна: {patient_name} / Sleep staging: {patient_name}")
        hypno_pics = folder_pics_path / f"hypnogram_{patient_name}_yasa.png"
        hypno_predicted = yasa_staging(hypno_pics, raw)
        self.logger.info("[OK] Стадирование YASA завершено")
        self.update_window_title(f"Стадирование сна завершено: {patient_name} / Sleep staging completed: {patient_name}")

        # Сохранение аннотаций YASA
        yasa_annotations_path = folder_yasa/ f"{patient_name}_annotations_yasa.csv"
        pd.DataFrame({'Annotation': hypno_predicted}).to_csv(yasa_annotations_path, index=False)
        self.logger.info(f"[OK] Аннотации сна сохранены: {yasa_annotations_path}")


        # 5. Построение графиков
        self.logger.info("[INFO] Строю гипнограмму")
        self.update_window_title(f"Строю гипнограмму: {patient_name} / Creating spectrogram: {patient_name}")
        plot_hypnogram(hypno_pics, hypno_predicted)
        self.logger.info(f"[OK] Гипнограмма сохранена: {hypno_pics}")
        self.update_window_title(f"Гипнограмма сохранена: {patient_name} / Hypnogram saved: {patient_name}")

        self.logger.info("[INFO] Строю спектрограмму")
        self.update_window_title(f"Строю спектрограмму для пациента: {patient_name}")
        spectro_pics = folder_pics_path / f"spectrogram_{patient_name}_yasa.png"
        plot_spectrogram(spectro_pics, chan, sf, hypno_predicted, raw)
        self.logger.info(f"[OK] Спектрограмма сохранена: {spectro_pics}")
        self.update_window_title(f"Спектрограмма сохранена: {patient_name} / Spectrogram saved: {patient_name}")

        # 6. Статистика сна
        self.logger.info("[INFO] Рассчитываю статистику сна")
        self.update_window_title(f"Рассчитываю статистику сна: {patient_name} / Computing sleep stat: {patient_name}")
        stat = sleep_statistics(hypno_predicted, sf_hyp=1/30)  # 30-секундные эпохи
        self.logger.info("[OK] Статистика сна рассчитана")
        self.update_window_title(f"Статистика сна рассчитана: {patient_name} / Sleep stat computed: {patient_name}")

        # Сохранение статистики в JSON
        fname_stat = folder_statistics_path / f"{patient_name}_sleep_statistics.json"
        with open(fname_stat, 'w', encoding='utf-8') as f:
            json.dump(stat, f, ensure_ascii=False, indent=4)
        self.logger.info(f"[OK] Статистика cна сохранена: {fname_stat}")
        self.update_window_title(f"Статистика cна сохранена: {patient_name} / Sleep stat saved: {patient_name}")

        # 7. Создание PDF-отчёта
        self.logger.info("[INFO] Создаю PDF-отчёт")
        self.update_window_title(f"Создаю PDF-отчёт: {patient_name} / Creating PDF-report: {patient_name}")

        create_sleep_statistics_pdf(patient_name, stat, folder_PDF, spectro_pics, font_path)
        pdf_path = folder_PDF / f"{patient_name}_sleep_statistics.pdf"
        self.logger.info(f"[OK] PDF-отчёт создан: {pdf_path}")
        self.update_window_title(f"PDF-отчёт создан: {patient_name} / PDF-report created: {patient_name}")
        if pdf_path and os.path.exists(pdf_path):
            try:
                subprocess.Popen([pdf_path], shell=True)
                self.step_completed["create_show_report"] = True
                self.update_menu_state()
            except Exception as e:
                self.update_window_title(
                    f"Не удалось открыть PDF-отчет: {patient_name} / Failed to open PDF-report: {patient_name}")
                return
        else:
            self.update_window_title(f"PDF-отчет не найден: {patient_name} / Failed to find PDF-report: {patient_name}")

        self.root.after(5000, lambda: self.update_window_title(""))

        # --- РАЗБЛОКИРОВКА ТРЕТЬЕЙ КНОПКИ (только при успехе!) ---
        self.btn_save_show_edf.config(state="normal")

        return

    def save_show_edf(self):
        """
        Загружает EDF‑файл и YASA‑аннотации, добавляет аннотации к сырым данным,
        сохраняет результат в указанную директорию и открывает в EDFbrowser.
        """
        folder_yasa = self.folder_yasa
        folder_data_anns = self.folder_data_anns

        self.logger.info(f"[OK] Директория для записи ЭЭГ и меток сна создана/проверена: {folder_data_anns}")

        # Шаг 1: получаем имя пациента и путь к EDF
        patient_name, eeg_file = self.get_name_edf_file()
        if not patient_name:
            self.update_window_title("Ошибка: не выбран пациент / No patient selected")
            return False

        # Формируем пути к файлам
        anns_yasa_name = folder_yasa / f"{patient_name}_annotations_yasa.csv"
        raw_eeg_name = Path(eeg_file)  # Гарантируем Path‑объект

        edf_file = str(raw_eeg_name)  # Для subprocess

        # Шаг 2: проверка существования файлов
        if not anns_yasa_name.exists():
            self.logger.error(f"Аннотации сна не найдены: {patient_name}")
            self.update_window_title(f"Аннотации сна не найдены: {patient_name} / Sleep anns not found: {patient_name}")
            return False

        self.logger.info(f"Файлы найдены для: {patient_name}. Начинаем обработку...")
        self.update_window_title(f"Аннотации сна найдены: {patient_name} / Sleep anns found: {patient_name}")

        try:
            # Шаг 3: читаем данные
            anns_yasa = pd.read_csv(anns_yasa_name)
            raw = mne.io.read_raw_edf(raw_eeg_name, preload=True)

            # Шаг 4: формируем аннотации
            length = len(anns_yasa)
            onset = [i * 30 for i in range(length)]
            duration = np.repeat(30, length)

            sleep_stage_mapping = {
                '0': 'W',  # Бодрствование (Wake)
                '1': 'N1',  # Фаза N1 (лёгкий сон)
                '2': 'N2',  # Фаза N2
                '3': 'N3',  # Фаза N3 (глубокий сон)
                '4': 'R'  # Фаза R (REM‑сон)
            }

            anns_yasa['Annotation'] = anns_yasa['Annotation'].astype(str).map(sleep_stage_mapping)
            description = anns_yasa['Annotation']
            annotations = mne.Annotations(onset, duration, description)
            raw.set_annotations(annotations)

            # Шаг 5: сохраняем результат
            output_filename = f"{patient_name}_with_anns.edf"
            full_eeg_path = folder_data_anns / output_filename

            mne.export.export_raw(
                full_eeg_path,
                raw,
                fmt='edf',
                overwrite=True
            )

            self.logger.info(f"[OK] ЭЭГ с аннотациями сна сохранена: {full_eeg_path}")
            self.update_window_title(f"Аннотации сна сохранены: {patient_name} / Sleep anns saved: {patient_name}")

            # Шаг 6: открываем в EDFbrowser
            try:
                edfbrowser_path = self.edfbrowser_path
                if not edfbrowser_path.is_file():
                    self.update_window_title(f"EDFbrowser не найден / EDFbrowser not found")
                    return False

                self.update_window_title(f"Открываю запись: {patient_name} / Opening EEG: {patient_name}")
                subprocess.Popen([str(edfbrowser_path), str(full_eeg_path)], shell=False)
                self.step_completed["save_show_edf"] = True
                self.update_menu_state()  # хотя дальше шагов нет, для полноты
                self.root.after(5000, lambda: self.update_window_title(""))


            except PermissionError:
                self.update_window_title(f"Нет прав на запуск EDFbrowser / No rights to run EDFbrowser")
                return False
            except Exception as e:
                self.update_window_title(f"Не удалось запустить EDFbrowser: {e} / Failed to run EDFbrowser")
                self.logger.error(f"[ERROR] Ошибка при запуске EDFbrowser: {e}")
                return False

            return True

        except Exception as e:
            error_msg = f"Ошибка при обработке данных: {e}"
            self.logger.error(error_msg)
            self.update_window_title(f"Ошибка при обработке данных / Error in data processing")
            self.root.after(5000, lambda: self.update_window_title(""))
            return False

    def convert_edf(self, file, patient_name):
        """
        Запускает ConverterStandalone.exe для конвертации .sm файла в .edf
        """
        try:
            # Путь к ConverterStandalone.exe
            converter_path = self.converter_path
            if not converter_path.is_file():
                self.update_window_title(f"\ConverterStandalone не найден / ConverterStandalone not found")
                return

            # Запускаем ConverterStandalone
            self.update_window_title(f"Открываю запись: {patient_name} / Opening EEG: {patient_name}")
            subprocess.Popen([str(converter_path), '-s', '-f', 'edf', str(file)], shell=False)
            fname = file.split('.')[0]
            edf_file = fname + '.edf'
            return edf_file

        except Exception as e:  # только здесь e определена
            self.update_window_title(f"Не удалось запустить ConverterStandalone / Failed to run ConverterStandalone")
            self.root.after(5000, lambda: self.update_window_title(""))
        except Exception as e:  # только здесь e определена
            self.update_window_title(f"Не удалось запустить ConverterStandalone / Failed to run ConverterStandalone")
            self.root.after(5000, lambda: self.update_window_title(""))


        except Exception as e:  # только здесь e определена
            self.update_window_title(f"Не удалось запустить ConverterStandalone / Failed to run ConverterStandalone")
            self.root.after(5000, lambda: self.update_window_title(""))

    def exit_app(self):
        self.update_window_title("Выходим из программы / Exiting")
        self.root.after(5000, lambda: self.update_window_title(""))
        self.root.quit()



if __name__ == "__main__":
    root = tk.Tk()
    app = SleepApp(root)
    root.mainloop()

