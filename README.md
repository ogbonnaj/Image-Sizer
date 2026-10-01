# Image Sizer v5 — Android APK

A Kivy + Pillow image cropping/resizing application packaged for Android.

## Included

- `main.py` — application source, based on the supplied Image Sizer v5 app.
- `buildozer.spec` — Android APK configuration.
- `requirements.txt` — runtime Python dependencies.
- `requirements-build.txt` — GitHub Actions build tooling.
- `icon.png` — generated application icon.
- `.gitignore` — excludes Buildozer output, caches, logs, and local state.
- `.github/workflows/build-apk.yml` — automatically builds a debug APK on GitHub Actions and uploads it as an artifact.

## UI update

All standard application buttons use the shared `AppButton` class. It has been updated to render as rounded pill-shaped buttons, including pressed and primary states, so the styling stays consistent across the app and its popups.

## Android build

1. Create a GitHub repository.
2. Upload/extract all files from this project into the repository root.
3. Push to `main` or `master`, or manually run the **Build Image Sizer APK** workflow from the Actions tab.
4. Open the completed workflow run.
5. Download the `Image-Sizer-APK` artifact.

The workflow caches Buildozer/p4a and Gradle data between builds to reduce subsequent build times.

## Local Linux build

Install Buildozer and its system dependencies, then run:

```bash
buildozer -v android debug
```

The APK will be placed in `bin/`.

## Notes

- The app is forced to landscape mode.
- The build targets ARM64 Android (`arm64-v8a`).
- Runtime dependencies are Kivy and Pillow.
- The existing app's image browsing, cropping, optional resizing, progress handling, saved state, crop cache, logging, and Android lifecycle handling are retained.
- Android storage behavior can vary by Android version because modern Android uses scoped storage. The build configuration includes image/media read permissions and legacy storage permissions for compatibility with the existing direct-path browser/output implementation.
