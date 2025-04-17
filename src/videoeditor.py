import os
from pathlib import Path
from moviepy import ImageClip, concatenate_videoclips, concatenate_audioclips, AudioFileClip, VideoFileClip, CompositeVideoClip
import random
from playwright.sync_api import sync_playwright

# Путь к HTML-шаблону
current_dir = os.path.dirname(__file__)
css_path = os.path.join(current_dir, "..", "assets", "chat_template.html")
chat_template = None

# Чтение шаблона
with open(css_path, "r", encoding="utf-8") as f:
    chat_template = f.read()

def make_html(msgs):
    """Создаёт HTML для отображения сообщений чата."""
    html_msgs = []
    for msg in msgs:
        if msg.startswith("0:"):
            text = msg[2:].strip()
            html_msgs.append(f'<div class="msg left">{text}<div class="time">10:12</div></div>')
        elif msg.startswith("1:"):
            text = msg[2:].strip()
            html_msgs.append(f'<div class="msg right">{text}<div class="time">10:13</div></div>')

    html_content = "\n".join(html_msgs).strip()
    return chat_template.replace("THERE_WILL_BE_MESSAGES", html_content)

def save_html(content, path):
    """Сохраняет HTML контент в файл."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def edit(lines, durations, output='output/chat.mp4'):
    """Создаёт визуализацию чата и озвучки."""
    bg_folder = os.path.abspath(os.path.join(current_dir, "..", "assets", "backgrounds"))
    bg_videos = list(Path(bg_folder).glob("*.mp4"))
    if not bg_videos:
        raise ValueError("в папке backgrounds нет видео")
    bg_video_path = random.choice(bg_videos)
    html_dir = 'output/html'
    frame_dir = 'output/frames'
    os.makedirs(html_dir, exist_ok=True)
    os.makedirs(frame_dir, exist_ok=True)

    # Создаём HTML файлы для каждого кадра
    for i in range(len(lines)):
        html = make_html(lines[:i+1])
        save_html(html, os.path.join(html_dir, f'{i:03}.html'))

    # Создаём скриншоты каждого HTML с использованием Playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1080})
        for i in range(len(lines)):
            html_path = os.path.abspath(os.path.join(html_dir, f'{i:03}.html'))
            page.goto(f'file:///{html_path}')
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.screenshot(path=os.path.join(frame_dir, f'{i:03}.png'), omit_background=True)
        browser.close()

    # Создаём видеоклипы для каждого кадра с учетом длительности
    clips = []
        # загружаем видеофон
    bg_clip = VideoFileClip(str(bg_video_path))

    # длительность — как сумма всех durations
    total_duration = sum(durations)

    # обрезаем видео по длительности
    start_duration = random.randint(0, int(bg_clip.duration-total_duration)-1)
    bg_clip = bg_clip.subclipped(start_duration, start_duration+total_duration)

    # масштабируем до вертикального формата
    # Масштабируем bg_clip так, чтобы оно вписывалось в размеры экрана
    bg_clip = bg_clip.resized(height=1920)
    if bg_clip.size[0] < 1080:
        bg_clip = bg_clip.resized(width=1080)
    bg_clip = bg_clip.cropped(x_center=bg_clip.size[0] // 2, width=1080)

    for i in range(len(lines)):
        img_path = os.path.join(frame_dir, f'{i:03}.png')
        img = ImageClip(img_path).resized(1.5).with_duration(durations[i])
        clips.append(img)

    # Загружаем все аудиофайлы из папки output/voiceover
    audio_files = sorted(Path('output/voiceover').glob('*.wav'))  # Находим все mp3 файлы
    audio_clips = [AudioFileClip(str(file)) for file in audio_files]

    # Объединяем все аудиофайлы в один
    final_audio = concatenate_audioclips(audio_clips)
    print("final_audio.duration =", final_audio.duration)
    final_audio = final_audio.subclipped(0, total_duration)
    print("final_audio.duration::after =", final_audio.duration)


    # Создаём финальное видео
    chat_overlay = concatenate_videoclips(clips, method="compose").with_position("center")

    final_video = CompositeVideoClip([bg_clip, chat_overlay])
    final_video = final_video.with_audio(final_audio)
    if final_video.audio is None:
        print("Audio is missing!")
    else:
        print("Audio added successfully!")


    print("final_video.size =", final_video.size)
    print("bg_clip.size =", bg_clip.size)
    print("chat_overlay.size =", chat_overlay.size)
    print("total_duration =", total_duration)
    print("start_duration =", start_duration)
    # Записываем финальный результат
    final_video.write_videofile(
        output,
        fps=24
    )
