import pyttsx3
from pathlib import Path
import os
from moviepy import AudioFileClip
import shutil

def get_audio_duration(file_path):
    """Получает длительность аудиофайла с помощью moviepy."""
    try:
        audio = AudioFileClip(file_path)
        return audio.duration
    except Exception as e:
        print(f"Ошибка при извлечении длительности для файла {file_path}: {e}")
        return 0

def clear_output_folder(output_dir):
    """Удаляет все файлы в указанной папке."""
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

def generate_voiceover(lines, output_dir="output/voiceover", speed=220):
    """Генерирует озвучку для каждого сообщения и сохраняет их в output_dir, используя pyttsx3."""
    os.makedirs(output_dir, exist_ok=True)
    clear_output_folder(output_dir)
    
    engine = pyttsx3.init()  # Инициализация TTS движка
    engine.setProperty('rate', speed)  # Установка скорости речи

    durations = []

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        # Убираем префикс типа "0: " или "1: "
        if line[1] == ':' and line[0] in ('0', '1'):
            text = line[3:].strip()
        else:
            text = line

        mp3_output_path = Path(output_dir) / f"line{i}.wav"  # Сохраняем в формате WAV
        print(f"[+] Генерация озвучки для: '{text}'")

        # Генерация аудио с использованием pyttsx3 и сохранение в файл
        engine.save_to_file(text, str(mp3_output_path))

        # Получаем длительность аудиофайла
        engine.runAndWait()  # Обязательно вызываем runAndWait после сохранения файла

        # Получаем длительность с помощью moviepy
        duration = get_audio_duration(str(mp3_output_path))
        durations.append(duration)

    print(f"[✓] Озвучка завершена, файлы в: {output_dir}")
    return durations
