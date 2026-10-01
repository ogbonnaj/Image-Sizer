[app]

# App name
title = Image Sizer

# Package name
package.name = imagesizer

# Package domain
package.domain = org.ogbonnaj

# Source directory
source.dir = .

# Main Python file
source.main = main.py

# Application version
version = 1.0.0

# Python dependencies
# Pin Python to 3.13 to avoid the Python 3.14 Android
# compilation issue seen in the GitHub Actions build.
requirements = python3==3.13.5,hostpython3==3.13.5,kivy,pillow

# Orientation
orientation = landscape

# Android configuration
android.api = 35
android.minapi = 23

# Android architecture
android.archs = arm64-v8a

# Android permissions
android.permissions = READ_MEDIA_IMAGES,READ_MEDIA_VIDEO

# Fullscreen
fullscreen = 1

# Presplash
presplash.filename = %(source.dir)s/icon.png

# Application icon
icon.filename = %(source.dir)s/icon.png

# Android entry point
android.entrypoint = org.kivy.android.PythonActivity

# Android backup
android.allow_backup = False

# Android theme
android.aminapi = 23

# Log level
log_level = 2


[buildozer]

# Build output/log directory
log_level = 2

# Warning: Buildozer will create .buildozer locally.
# It should remain ignored by .gitignore.
warn_on_root = 1
