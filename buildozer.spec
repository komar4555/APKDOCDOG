# buildozer.spec — без python-docx/lxml
[app]
title = Contract Generator
package.name = contractgenerator
package.domain = org.example
source.dir = .
source.include_exts = py,kv,txt,docx
version = 0.1

# критично: только pure-python зависимости
requirements = python3,kivy,plyer

orientation = landscape
fullscreen = 0

android.minapi = 27
android.api = 35
android.archs = arm64-v8a,armeabi-v7a
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

[buildozer]
log_level = 2
warn_on_root = 0
