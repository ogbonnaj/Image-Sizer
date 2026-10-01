[app]

# Application name
title = Image Sizer

# Package name
package.name = imagesizer

# Package domain
package.domain = org.ogbonnaj

# Source directory
source.dir = .

# Main Python file
source.main = main.py

# Files required by the application
source.include_exts = py,png,jpg,jpeg,kv,atlas,json,txt

# Application version
version = 1.0.0

# Python-for-Android requirements
requirements = python3,kivy,pillow

# Use the stable Python-for-Android branch
p4a.branch = master

# Screen orientation
orientation = landscape

# Fullscreen application
fullscreen = 1

# Application icon
icon.filename = %(source.dir)s/icon.png

# Android presplash
presplash.filename = %(source.dir)s/icon.png

# Android API
android.api = 35

# Minimum Android API
android.minapi = 23

# Android NDK
android.ndk = 28c

# NDK API
android.ndk_api = 23

# Android architecture
android.archs = arm64-v8a

# Automatically accept Android SDK licenses
# Required for unattended GitHub Actions builds
android.accept_sdk_license = True

# Android entry point
android.entrypoint = org.kivy.android.PythonActivity

# Android permissions
android.permissions = READ_MEDIA_IMAGES,READ_MEDIA_VIDEO

# Disable Android backup
android.allow_backup = False

# Don't automatically update SDK packages unnecessarily
android.skip_update = False


[buildozer]

# Buildozer logging
log_level = 2

# Warn when Buildozer is run as root
warn_on_root = 1
