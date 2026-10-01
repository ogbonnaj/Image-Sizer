[app]

# ---------------------------------------------------------
# Application
# ---------------------------------------------------------

title = Image Sizer
package.name = imagesizer
package.domain = org.ogbonnaj

source.dir = .
source.main = main.py

version = 1.0.0

# Include the files used by the application
source.include_exts = py,png,jpg,jpeg,kv,atlas,json,txt

# ---------------------------------------------------------
# Python / Kivy dependencies
# ---------------------------------------------------------

requirements = python3,kivy,pillow

# Use the stable python-for-android branch.
p4a.branch = master

# SDL2 is the normal Kivy Android bootstrap.
p4a.bootstrap = sdl2

# ---------------------------------------------------------
# Screen / appearance
# ---------------------------------------------------------

orientation = landscape
fullscreen = 1

icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/icon.png

# ---------------------------------------------------------
# Android SDK / NDK
# ---------------------------------------------------------

# Android target API
android.api = 35

# Minimum Android version
android.minapi = 23

# NDK version used by the Android build
android.ndk = 28c

# NDK API must match the minimum API used by the build
android.ndk_api = 23

# Build only for modern 64-bit Android devices
android.archs = arm64-v8a

# Automatically accept SDK licenses in GitHub Actions
android.accept_sdk_license = True

# ---------------------------------------------------------
# Android application
# ---------------------------------------------------------

android.entrypoint = org.kivy.android.PythonActivity

android.allow_backup = False

# Keep the app in landscape
android.orientation = landscape

# ---------------------------------------------------------
# Permissions
# ---------------------------------------------------------

android.permissions = READ_MEDIA_IMAGES,READ_MEDIA_VIDEO

# ---------------------------------------------------------
# Build behavior
# ---------------------------------------------------------

# APK for debug builds
android.debug_artifact = apk

# AAB for release builds
android.release_artifact = aab

# Allow Buildozer to update/download required SDK components
android.skip_update = False

# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------

log_level = 2


[buildozer]

# Buildozer logging
log_level = 2

# Warn instead of silently allowing root builds
warn_on_root = 1
