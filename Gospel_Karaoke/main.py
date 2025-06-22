from kivy.lang import Builder
from kivy.core.audio import SoundLoader
from kivy.clock import Clock
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.filemanager import MDFileManager
from kivy.utils import platform
import os
import time
import re
import threading
import sounddevice as sd
import wave
from pydub import AudioSegment

KV = """
MDScreen:
    MDBoxLayout:
        orientation: 'vertical'
        spacing: dp(10)
        padding: dp(20)

        MDLabel:
            id: title
            text: "Gospel Karaoke App"
            halign: "center"
            font_style: "H5"

        MDLabel:
            id: song_label
            text: "No song selected"
            halign: "center"
            theme_text_color: "Secondary"

        MDLabel:
            id: lyrics_label
            text: ""
            halign: "center"
            theme_text_color: "Primary"
            font_style: "Subtitle1"

        MDRaisedButton:
            text: "Select Song"
            on_release: app.file_manager_open()

        MDRaisedButton:
            id: play_button
            text: "Play"
            on_release: app.toggle_play()

        MDRaisedButton:
            text: "Record Cover (10s)"
            on_release: app.start_recording()
"""

class GospelKaraokeApp(MDApp):
    def build(self):
        self.sound = None
        self.is_playing = False
        self.current_song = None
        self.samplerate = 44100
        self.lyrics = []
        self.manager = MDFileManager(exit_manager=self.file_manager_close, select_path=self.select_song)
        return Builder.load_string(KV)

    def file_manager_open(self):
        self.manager.show(os.getcwd() + "/instrumentals")

    def file_manager_close(self, *args):
        self.manager.close()

    def select_song(self, path):
        self.current_song = path
        self.root.ids.song_label.text = os.path.basename(path)
        self.file_manager_close()

    def toggle_play(self):
        if not self.current_song:
            return
        if not self.is_playing:
            self.sound = SoundLoader.load(self.current_song)
            if self.sound:
                self.sound.play()
                self.is_playing = True
                self.root.ids.play_button.text = "Pause"
                self.lyrics = self.load_lyrics(self.current_song)
                Clock.schedule_interval(self.update_lyrics, 0.5)
        else:
            self.sound.stop()
            self.is_playing = False
            self.root.ids.play_button.text = "Play"

    def load_lyrics(self, song_path):
        base = os.path.basename(song_path).split('.')[0]
        lyrics_file = f"lyrics/{base}.txt"
        if not os.path.exists(lyrics_file):
            return []
        with open(lyrics_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        pattern = re.compile(r'\[(\d+):(\d+)\]\s*(.*)')
        timestamps = []
        for line in lines:
            match = pattern.match(line)
            if match:
                minutes = int(match.group(1))
                seconds = int(match.group(2))
                text = match.group(3)
                time_sec = minutes * 60 + seconds
                timestamps.append((time_sec, text))
        return timestamps

    def update_lyrics(self, dt):
        if self.sound:
            position = self.sound.get_pos() / 1000
            for ts, line in self.lyrics:
                if abs(position - ts) < 0.5:
                    self.root.ids.lyrics_label.text = line
                    break

    def start_recording(self):
        if not self.current_song:
            return
        filename = f"recordings/{os.path.basename(self.current_song).split('.')[0]}_cover.wav"
        threading.Thread(target=self.record_audio, args=(filename,)).start()
        threading.Timer(11, self.combine_tracks, args=(self.current_song, filename)).start()

    def record_audio(self, filename):
        audio = sd.rec(int(10 * self.samplerate), samplerate=self.samplerate, channels=2)
        sd.wait()
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(self.samplerate)
            wf.writeframes(audio.tobytes())

    def combine_tracks(self, song_path, cover_path):
        song = AudioSegment.from_file(song_path)
        cover = AudioSegment.from_wav(cover_path)
        if len(cover) > len(song):
            cover = cover[:len(song)]
        else:
            song = song[:len(cover)]
        combined = song.overlay(cover)
        output_path = f"recordings/combined_{os.path.basename(song_path).split('.')[0]}.wav"
        combined.export(output_path, format="wav")

if __name__ == '__main__':
    GospelKaraokeApp().run()
