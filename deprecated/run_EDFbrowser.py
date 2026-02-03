
import os
import subprocess
import sys

# 1. Ввод имени пациента
patient_name = input("Введите имя или ID пациента: ").strip()

if not patient_name:
    print("Ошибка: имя пациента не указано!")
    sys.exit(1)

# 2. Формируем путь к .edf-файлу
base_dir = r"\\MCSSERVER\DB Temp\physionet.org\files\haaglanden-medisch-centrum-sleep-staging-database-1.1\recordings"
edf_file = os.path.join(base_dir, f"{patient_name}.edf")
edf_file = os.path.normpath(edf_file)  # Нормализуем разделители

print(f"Проверяю файл: {edf_file}")


if not os.path.isfile(edf_file):
    print(f"Ошибка: файл не найден: {edf_file}")
    print("Проверьте:")
    print("  - Существует ли папка MCSSERVER\DB Temp\physionet.org\files\haaglanden-medisch-centrum-sleep-staging-database-1.1\recordings")
    print("  - Есть ли в ней файл {patient_name}.edf")
    sys.exit(1)

# 3. Путь к EDFbrowser
edfbrowser_path = r"C:\Program Files (x86)\EDFbrowser\edfbrowser.exe"
edfbrowser_path = os.path.normpath(edfbrowser_path)


if not os.path.isfile(edfbrowser_path):
    print(f"Ошибка: edfbrowser не найден: {edfbrowser_path}")
    print("Убедитесь, что программа установлена по указанному пути.")
    sys.exit(1)

# 4. Запускаем EDFbrowser
try:
    print(f"\n✅ Запускаю EDFbrowser")
    print(f"Файл: {edf_file}")
    subprocess.run([edfbrowser_path, edf_file], check=True)
except subprocess.CalledProcessError as e:
    print(f"Ошибка при запуске EDFbrowser (код {e.returncode}): {e}")
except PermissionError:
    print("Ошибка: Нет прав на запуск EDFbrowser. Попробуйте запустить скрипт от имени администратора.")
except Exception as e:
    print(f"Неизвестная ошибка: {type(e).__name__}: {e}")
