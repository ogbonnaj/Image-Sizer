[app]

# =========================================================
# IMAGE SIZER
# =========================================================

title = Image Sizer
package.name = imagesizer
package.domain = org.ogbonnaj

source.dir = .
source.main = main.py

version = 1.0.0

# Include application files and image assets
source.include_exts = py,png,jpg,jpeg,kv,atlas,json,txt

# =========================================================
# PYTHON / KIVY
# =========================================================

# IMPORTANT:
# Pin target Python and host Python to EXACTLY the same version.
#
# This prevents python-for-android from selecting Python 3.14,
# which caused the preadv/pwritev Android compilation failure.

requirements = python3==3.12.9,hostpython3==3.12.9,kivy,pillow

# Stable python-for-android branch
p4a.branch = master

# Kivy Android bootstrap
p4a.bootstrap = sdl2

# =========================================================
# DISPLAY
# =========================================================

orientation = landscape
fullscreen = 1

# =========================================================
# APP ICON / SPLASH
# =========================================================

icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/icon.png

# =========================================================
# ANDROID SDK
# =========================================================

android.api = 35
android.minapi = 23

# =========================================================
# ANDROID NDK
# =========================================================

android.ndk = 28c
android.ndk_api = 23

# =========================================================
# ARCHITECTURE
# =========================================================

android.archs = arm64-v8a

# =========================================================
# AUTOMATED GITHUB ACTIONS BUILD
# =========================================================

# Automatically accept Android SDK licenses.
android.accept_sdk_license = True

# Allow Buildozer to install/update required SDK components.
android.skip_update = False

# =========================================================
# ANDROID APPLICATION
# =========================================================

android.entrypoint = org.kivy.android.PythonActivity

android.allow_backup = False

# Keep application in landscape mode.
android.orientation = landscape

# =========================================================
# PERMISSIONS
# =========================================================

android.permissions = READ_MEDIA_IMAGES,READ_MEDIA_VIDEO

# =========================================================
# BUILD OUTPUT
# =========================================================

android.debug_artifact = apk
android.release_artifact = aab

# =========================================================
# BUILD LOGGING
# =========================================================

log_level = 2


[buildozer]

log_level = 2
warn_on_root = 1
