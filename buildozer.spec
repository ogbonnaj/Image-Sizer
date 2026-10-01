[app]
# Image Sizer v5 - Android build configuration
# GitHub Actions builds a debug APK automatically.

# (str) Title of your application
title = Image Sizer

# (str) Package name
package.name = imagesizer

# (str) Package domain (used for Android application ID)
package.domain = org.imagesizer

# (str) Source code directory
source.dir = .


# (str) Application version
version = 5.0.0

# (str) Source file extensions to include
source.include_exts = py,png,jpg,jpeg,json,kv,atlas,txt

# (str) Application icon
icon.filename = %(source.dir)s/icon.png

# (str) Presplash image (not required)
# presplash.filename = %(source.dir)s/presplash.png

# (list) Application requirements
requirements = python3,kivy,pillow

# (str) Orientation
orientation = landscape

# (bool) Fullscreen application
fullscreen = 1

# (str) Supported Android architectures
android.archs = arm64-v8a

# (int) Android API used to compile the app
android.api = 35

# (int) Minimum supported Android API
android.minapi = 23

# (str) Android permissions needed by the existing image browser/storage flow.
# READ_MEDIA_IMAGES is used by Android 13+; the legacy permissions cover older devices.
android.permissions = READ_MEDIA_IMAGES,READ_MEDIA_VIDEO,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# Keep the Android app lightweight and predictable.
android.accept_sdk_license = True
android.allow_backup = True

# (str) Android activity configuration
android.activity_class_name = org.kivy.android.PythonActivity

# (bool) Do not automatically show a console window on desktop builds
log_level = 2

# (str) Python-for-Android bootstrap
p4a.bootstrap = sdl2

# (bool) Keep build artifacts outside the source tree's tracked files.

[buildozer]
# (int) Log level (0 = error, 1 = warning, 2 = info, 3 = debug)
log_level = 2

# (int) Display warnings about configuration options
warn_on_root = 1

# (str) Build directory
build_dir = .buildozer

# (str) Output directory
bin_dir = bin
