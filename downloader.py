import os
import subprocess
from yt_dlp import YoutubeDL
from pydub import AudioSegment

def download_and_convert(url: str, folder: str, filename: str):
    """
    Scarica l'audio da YouTube con yt-dlp e converte in mp3 con pydub.
    Restituisce messaggi di log con yield.
    """
    # Definisci percorso file temporaneo e finale
    temp_path = os.path.join(folder, filename + ".webm")
    final_path = os.path.join(folder, filename + ".mp3")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': temp_path,
        'quiet': True,
        'no_warnings': True,
        'progress_hooks': [],
    }

    yield f"[INFO] Download audio in corso..."
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    yield f"[INFO] Download completato: {temp_path}"

    yield f"[INFO] Conversione in MP3 in corso..."
    # Conversione con pydub (usa ffmpeg)
    audio = AudioSegment.from_file(temp_path)
    audio.export(final_path, format="mp3")
    yield f"[INFO] File convertito e salvato come: {final_path}"

    # Rimuovi file temporaneo
    try:
        os.remove(temp_path)
        yield f"[INFO] File temporaneo rimosso"
    except Exception as e:
        yield f"[WARN] Non è stato possibile rimuovere il file temporaneo: {e}"
