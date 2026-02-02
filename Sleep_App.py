import threading
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
from pathlib import Path
import os
import subprocess
import time
from pathlib import Path
import json
import pandas as pd
from functions_pipeline import check_ready, set_logger, preprocessing, plot_hypnogram, plot_spectrogram, yasa_staging, create_sleep_statistics_pdf
from yasa import sleep_statistics
import warnings
warnings.filterwarnings("ignore")


class SleepApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Соня: cистема просмотра и анализа записей сна")
        self.root.geometry("600x400")
        self.root.resizable(False, False)

        # Хранилище последнего выбранного пути (можно сохранить в конфиг)
        self.last_data_dir = None

        # --- Меню ---
        self.menu = tk.Menu(root)
        root.config(menu=self.menu)

        # Подменю "О программе"
        self.about_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="О программе", menu=self.about_menu)
        self.about_menu.add_command(label="Информация", command=self.show_about)

        # Основные пункты меню
        self.menu.add_command(label="Показать запись", command=self.show_EDF)
        self.menu.add_command(label="Создать отчёт", command=self.create_report)
        self.menu.add_command(label="Показать отчёт", command=self.show_report)
        self.menu.add_command(label="Показать сомнограмму", command=self.show_hypnogram)
        self.menu.add_command(label="Выход", command=self.exit_app)

        # --- Основной интерфейс ---
        tk.Label(
            root,
            text="Соня: cистема просмотра и анализа записей сна",
            font=("Arial", 14, "bold"),
            pady=20
        ).pack()

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=30)

        # Настройка фрейма для центрирования (пример)
        btn_frame.columnconfigure(0, weight=1)  # Растягивает колонку на всю ширину
        btn_frame.rowconfigure(list(range(4)), weight=1)  # Равномерное распределение строк

        # Кнопка 1: Показать запись
        tk.Button(
            btn_frame,
            text="Показать запись",
            bg="#D8BFD8",
            fg="white",
            font=("Arial", 11),  # Увеличен размер шрифта
            width=25,  # Увеличена ширина кнопки
            command=self.show_EDF
        ).grid(
            row=0, column=0,
            padx=20,  # Увеличены горизонтальные отступы
            pady=(15, 10),  # Вертикальные отступы: сверху 15px, снизу 10px
            sticky="ew"  # Растягивает кнопку на всю ширину колонки
        )

        # Кнопка 2: Показать отчёт
        tk.Button(
            btn_frame,
            text="Создать отчёт",
            bg="#DDA0DD",
            fg="white",
            font=("Arial", 11),
            width=25,
            command=self.create_report
        ).grid(
            row=1, column=0,
            padx=20,
            pady=10,
            sticky="ew"
        )

        # Кнопка 3: Создать отчёт
        tk.Button(
            btn_frame,
            text="Показать отчёт",
            bg="#BA55D3",
            fg="white",
            font=("Arial", 11),
            width=25,
            command=self.show_report
        ).grid(
            row=2, column=0,
            padx=20,
            pady=10,
            sticky="ew"
        )

        # Кнопка 4: Показать сомнограмму
        tk.Button(
            btn_frame,
            text="Показать сомнограмму",
            bg="#9370DB",
            fg="white",
            font=("Arial", 11),
            width=25,
            command=self.show_hypnogram
        ).grid(
            row=3, column=0,  # Исправлено: было column=1 → теперь column=0
            padx=20,
            pady=(10, 15),  # Вертикальные отступы: сверху 10px, снизу 15px
            sticky="ew"
        )

    def show_about(self):
        messagebox.showinfo(
            "О программе",
            "Соня: cистема просмотра и анализа записей сна \n"
            "Версия: 1.0\n"
            "Разработчик: Александра\n\n"
            "Использует YASA для автоматической классификации стадий и рассчета статистики сна\n\n"
            "Использует EDFbrowser для визуализации .edf-файлов\n\n"
        )

    def get_base_directory(self):
        """
        Интерактивно запрашивает у пользователя базовую директорию с EDF‑файлами.
        Сохраняет последний выбранный путь для следующего вызова.
        """
        initial_dir = str(self.last_data_dir) if self.last_data_dir else "/"

        selected_dir = filedialog.askdirectory(
            initialdir=initial_dir,
            title="Выберите папку с EDF‑файлами"
        )

        if not selected_dir:
            return None  # Пользователь отменил выбор

        dir_path = Path(selected_dir)
        if not dir_path.is_dir():
            messagebox.showerror("Ошибка", "Выбранная папка не существует!")
            return None

        # Сохраняем для следующего раза
        self.last_data_dir = dir_path
        return dir_path

    def get_name_edf_file(self):
        """
        Запрашивает имя пациента и путь к EDF‑файлу.
        Возвращает: (patient_name: str, edf_file: Path) или (None, None) при ошибке.
        """
        try:
            # 1. Ввод имени пациента
            patient_name_input = simpledialog.askstring(
                "Имя пациента",
                "Введите имя или ID пациента:"
            )
            if not patient_name_input or not patient_name_input.strip():
                messagebox.showerror("Ошибка", "Имя пациента не указано!")
                return None, None
            patient_name = patient_name_input.strip()

            # 2. Интерактивный выбор base_dir
            base_dir = self.get_base_directory()
            if not base_dir:
                messagebox.showerror("Ошибка", "Папка с данными не выбрана.")
                return None, None

            # 3. Формируем путь к .edf-файлу
            edf_file = base_dir / f"{patient_name}.edf"

            if not edf_file.is_file():
                messagebox.showerror(
                    "Ошибка",
                    f"Файл не найден:\n{edf_file}\n\nПроверьте:\n  - Правильность имени пациента ({patient_name})\n  - Наличие файла в выбранной папке."
                )
                return None, None

        except Exception as e:
            messagebox.showerror(
                "Ошибка",
                f"Произошла непредвиденная ошибка:\n{type(e).__name__}: {e}"
            )
            return None, None

        return patient_name, edf_file


    def show_EDF(self):
        """
        Запускает просмотрщик EDF-browser c указанным EDF‑файлом.
        """
        patient_name, edf_file = self.get_name_edf_file()

        if not patient_name or not edf_file:
            return

        try:
            # Путь к EDFbrowser
            edfbrowser_path = Path(r"C:\Program Files (x86)\EDFbrowser\edfbrowser.exe")
            if not edfbrowser_path.is_file():
                messagebox.showerror(
                    "Ошибка",
                    f"EDFbrowser не найден:\n{edfbrowser_path}\n\n"
                    "Убедитесь, что программа установлена по указанному пути."
                )
                return

            # Запускаем EDFbrowser
            messagebox.showinfo("Запуск", f"Открываю запись для пациента: {patient_name}")
            subprocess.Popen([str(edfbrowser_path), str(edf_file)], shell=False)

        except PermissionError:
            messagebox.showerror(
                "Ошибка",
                "Нет прав на запуск EDFbrowser.\n"
                "Попробуйте запустить приложение от имени администратора."
            )
        except Exception as e:  # только здесь e определена
            messagebox.showerror(
                "Ошибка",
                f"Не удалось запустить EDFbrowser:\n{type(e).__name__}: {e}"
            )

    def create_report(self):
        """Запускает процесс создания отчёта через YASA в отдельном потоке с логированием."""
        patient_name, edf_file = self.get_name_edf_file()

        if not patient_name:
            return

        subject = patient_name
        # 1. Настройка логгера
        logger = set_logger()
        logger.info(f"[INFO] Начало обработки для испытуемого: {subject}")

        # 2. Пути к директориям
        #folder_data = Path(r"\\MCSSERVER\DB Temp\physionet.org\files\haaglanden-medisch-centrum-sleep-staging-database-1.1\recordings")
        folder_pics_path = Path(r"\\MCSSERVER\DB Temp\physionet.org\processing\Sleep\pics\pipeline")
        folder_metrics_path = Path(r"\\MCSSERVER\DB Temp\physionet.org\processing\Sleep\yasa_annotations_metrics")
        folder_statistics_path = Path(r"\\MCSSERVER\DB Temp\physionet.org\processing\Sleep\sleep_statistics")
        folder_PDF = Path(r"\\MCSSERVER\DB Temp\physionet.org\processing\Sleep\PDF\pipeline")


        # Создание директорий
        for folder in [folder_pics_path, folder_metrics_path, folder_statistics_path, folder_PDF]:
            folder.mkdir(parents=True, exist_ok=True)
            logger.info(f"[OK] Директория создана/проверена: {folder}")

        root = self.root

        root.config(cursor="watch")  # Сразу меняем курсор
        root.update()  # Принудительно обновляем интерфейс

        # 3. Препроцессинг
        messagebox.showinfo("Обработка", "Начинаю препроцессинг EDF-файла...")
        logger.info(f"[INFO] Начинаю препроцессинг: {edf_file}")
        raw, chan, sf = preprocessing(fname_edf=str(edf_file))
        logger.info("[OK] Препроцессинг завершён")

        root.config(cursor="")  # Всегда возвращаем курсор
        root.update()

        # 4. YASA: стадирование сна
        messagebox.showinfo("YASA", "Запускаю стадирование сна (YASA)...")
        logger.info("[INFO] Запускаю YASA для стадирования")
        hypno_pics = folder_pics_path / f"hypnogram_{subject}_yasa.png"
        hypno_predicted = yasa_staging(hypno_pics, raw)
        logger.info("[OK] Стадирование YASA завершено")

        # Сохранение аннотаций YASA
        yasa_annotations_path = folder_metrics_path / f"{subject}_annotations_yasa.csv"
        pd.DataFrame({'Annotation': hypno_predicted}).to_csv(yasa_annotations_path, index=False)
        logger.info(f"[OK] Аннотации YASA сохранены: {yasa_annotations_path}")


        # 5. Построение графиков
        messagebox.showinfo("Графики", "Строю гипнограмму...")
        logger.info("[INFO] Строю гипнограмму")
        plot_hypnogram(hypno_pics, hypno_predicted)
        logger.info(f"[OK] Гипнограмма сохранена: {hypno_pics}")


        messagebox.showinfo("Графики", "Строю спектрограмму...")
        logger.info("[INFO] Строю спектрограмму")
        spectro_pics = folder_pics_path / f"spectrogram_{subject}_yasa.png"
        plot_spectrogram(spectro_pics, chan, sf, hypno_predicted, raw)
        logger.info(f"[OK] Спектрограмма сохранена: {spectro_pics}")


        # 6. Статистика сна
        messagebox.showinfo("Статистика", "Рассчитываю статистику сна...")
        logger.info("[INFO] Рассчитываю статистику сна")
        stat = sleep_statistics(hypno_predicted, sf_hyp=1/30)  # 30-секундные эпохи
        logger.info("[OK] Статистика сна рассчитана")


        # Сохранение статистики в JSON
        fname_stat = folder_statistics_path / f"{subject}_sleep_statistics.json"
        with open(fname_stat, 'w', encoding='utf-8') as f:
            json.dump(stat, f, ensure_ascii=False, indent=4)
        logger.info(f"[OK] Статистика сохранена: {fname_stat}")

        # 7. Создание PDF-отчёта
        messagebox.showinfo("PDF", "Создаю PDF-отчёт...")
        logger.info("[INFO] Создаю PDF-отчёт")
        font_path = r"\\MCSSERVER\DB Temp\physionet.org\processing\Sleep\dejavu-sans-ttf-2.37\ttf\DejaVuSans.ttf"
        create_sleep_statistics_pdf(subject, stat, folder_PDF, spectro_pics, font_path)
        pdf_path = folder_PDF / f"{subject}_report.pdf"
        logger.info(f"[OK] PDF-отчёт создан: {pdf_path}")
        messagebox.showinfo("Готово!", f"PDF-отчёт создан:\n{pdf_path}")

        return

    def show_report(self):
        """Показывает PDF, сформированный в функции create_report()"""
        patient_name, edf_file = self.get_name_edf_file()

        folder_PDF = Path(r"\\MCSSERVER\DB Temp\physionet.org\processing\Sleep\PDF\pipeline")
        pdf_path = folder_PDF / f"{patient_name}_sleep_statistics.pdf"

        if pdf_path and os.path.exists(pdf_path):
            try:
                subprocess.Popen([pdf_path], shell=True)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть файл:\n{e}")
                return
        else:
            messagebox.showerror("Ошибка", f"Файл PDF {pdf_path} не найден.")

        return

    def show_hypnogram(self):
        """Показывает hypnogram, сформированный в функции create_report()"""
        patient_name, edf_file = self.get_name_edf_file()

        folder_PDF = Path(r"\\MCSSERVER\DB Temp\physionet.org\processing\Sleep\pics\pipeline")
        png_path = folder_PDF / f"hypnogram_{patient_name}_yasa.png"

        if png_path and os.path.exists(png_path):
            try:
                subprocess.Popen([png_path], shell=True)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть файл:\n{e}")
                return
        else:
            messagebox.showerror("Ошибка", f"Файл png {png_path} не найден.")

        return

    def exit_app(self):
        self.root.quit()



if __name__ == "__main__":
    root = tk.Tk()
    app = SleepApp(root)
    root.mainloop()

