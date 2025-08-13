# buildozer.spec
# ---------------
[app]
title = Contract Generator
package.name = contractgenerator
package.domain = org.example
source.dir = .
source.include_exts = py,kv,txt,docx
version = 0.1

# Библиотеки
requirements = python3,kivy,python-docx,lxml,plyer

# Ориентация экрана (можно поменять на portrait)
orientation = landscape
fullscreen = 0

# Android таргеты
android.minapi = 27
android.api = 35
android.archs = arm64-v8a,armeabi-v7a

# Разрешения (для доступа к файлам; на Android 11+ используется SAF через plyer)
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# Иконка/сплэш (по желанию)
# icon.filename = %(source.dir)s/icon.png
# presplash.filename = %(source.dir)s/presplash.png

# Логи сборки
[buildozer]
log_level = 2
warn_on_root = 0
