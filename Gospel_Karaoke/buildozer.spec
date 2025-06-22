[app]
title = GospelKaraoke
package.name = gospelkaraoke
package.domain = org.example
source.dir = .
source.include_exts = py,kv,txt,mp3,wav
version = 1.0
requirements = python3,kivy,kivymd,plyer,pydub
android.permissions = RECORD_AUDIO
orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1
