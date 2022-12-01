from . import bot_utils
from typing import Union

MAX_DURATION = 300
MAX_SIZE = 20 * 1024 * 1024 #MB

OGG_FILE_NAME = '/tmp/audio.ogg'
WAV_FILE_NAME = '/tmp/audio.wav'
AAC_FILE_NAME = '/tmp/audio.aac'
MP4_FILE_NAME = '/tmp/video.mp4'
OUT_FILE_NAME = '/tmp/out%03d.wav'
OUT_BLOB = '/tmp/out*.wav'

def __download_file(file_id: str, file_name: str) -> None:
    file_info = bot_utils.bot.get_file(file_id)
    downloaded_file = bot_utils.bot.download_file(file_info.file_path)
    with open(file_name, 'wb') as new_file:
        new_file.write(downloaded_file)

def __get_file_id(file) -> Union[str, None]:
    file_size = file.get('file_size')
    if file_size <= MAX_SIZE:
        return file.get('file_id')

def __get_voice_file(voice) -> Union[str, None]:
    import subprocess

    file_id = __get_file_id(voice)
    if file_id is None:
        return

    __download_file(file_id, OGG_FILE_NAME)

    subprocess.Popen(['ffmpeg', '-y', '-i', OGG_FILE_NAME, WAV_FILE_NAME]).wait()

    return WAV_FILE_NAME

def __get_video_file(video) -> Union[str, None]:
    import subprocess

    file_id = __get_file_id(video)
    if file_id is None:
        return

    __download_file(file_id, MP4_FILE_NAME)

    subprocess.Popen(['ffmpeg', '-y', '-i', MP4_FILE_NAME, '-vn', '-acodec', 'copy', AAC_FILE_NAME]).wait()
    subprocess.Popen(['ffmpeg', '-y', '-i', AAC_FILE_NAME, WAV_FILE_NAME]).wait()

    return WAV_FILE_NAME

def __split_file(file: str):
    import subprocess
    import glob

    subprocess.Popen(['ffmpeg', '-y', '-i', file, '-f', 'segment', '-segment_time', str(MAX_DURATION), '-c', 'copy', OUT_FILE_NAME]).wait()
    return glob.glob(OUT_BLOB)

def get_files(message) -> Union[list[str], None]:
    voice = message.get('voice')
    file = None
    duration = None
    if voice:
        file = __get_voice_file(voice)
        duration = voice.get('duration')

    video = message.get('video_note')
    if video:
        file = __get_video_file(video)
        duration = video.get('duration')

    if file:
        if duration and duration <= MAX_DURATION:
            return [file]
        else:
            return __split_file(file)
