# ================================================================
# IMAGE SIZER v5
# KIVY + PILLOW
# PYDROID 3 / ANDROID
#
# FORCED LANDSCAPE
# CROPPING + OPTIONAL RESIZING
#
# SAFER / SIMPLIFIED KIVY VERSION
#
# AUTO-SAVES ITS PROGRESS TO A JSON FILE (same folder as the
# error log) SO IT CAN CONTINUE AFTER PYDROID 3 CLOSES IT
# ================================================================


# ================================================================
# KIVY CONFIG
# MUST BE BEFORE OTHER KIVY IMPORTS
# ================================================================

from kivy.config import Config

# ----------------------------------------------------------------
# These calls run before any file logging exists, so on a weak or
# unusual GPU (budget phones especially) a native SDL2/GL failure
# here can kill the app before a single line of Python logging
# happens - hence the try/except around every individual call
# instead of one block, and multisamples forced to 0, which is a
# common cause of instant black-screen exits on low-end Android
# GPUs that don't support the requested multisample buffer.
# ----------------------------------------------------------------

try:
    Config.set("graphics", "multisamples", "0")
except Exception:
    pass

try:
    Config.set("graphics", "orientation", "landscape")
except Exception:
    pass

try:
    Config.set("graphics", "resizable", "1")
except Exception:
    pass

try:
    Config.set("graphics", "borderless", "0")
except Exception:
    pass


# ================================================================
# STANDARD LIBRARY
# ================================================================

import os
import sys
import json
import shutil
import threading
import traceback
import time

from pathlib import Path
from collections import deque


# ================================================================
# EARLY LOGGING
# ================================================================

def get_log_directory():

    locations = [
        Path("/storage/emulated/0/ImageSizer"),
        Path("/sdcard/ImageSizer"),
        Path.home() / "ImageSizer",
        Path.cwd() / "ImageSizer"
    ]

    for directory in locations:

        try:

            directory.mkdir(
                parents=True,
                exist_ok=True
            )

            test_file = directory / ".test"

            test_file.write_text(
                "test",
                encoding="utf-8"
            )

            try:
                test_file.unlink()
            except Exception:
                pass

            return directory

        except Exception:
            continue

    return Path.cwd()


LOG_DIRECTORY = get_log_directory()

LOG_FILE = LOG_DIRECTORY / "image_sizer_error.log"


def write_log(message):

    try:

        with open(
            LOG_FILE,
            "a",
            encoding="utf-8"
        ) as file:

            file.write("\n")
            file.write("=" * 70)
            file.write("\n")
            file.write(
                time.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )
            file.write("\n")
            file.write(str(message))
            file.write("\n")

    except Exception:
        pass


def exception_handler(
    exc_type,
    exc_value,
    exc_traceback
):

    try:

        error = "".join(
            traceback.format_exception(
                exc_type,
                exc_value,
                exc_traceback
            )
        )

        write_log(
            "UNCAUGHT EXCEPTION\n"
            + error
        )

        print(error)

    except Exception:
        pass


sys.excepthook = exception_handler


write_log(
    "APPLICATION STARTING"
)


# ================================================================
# KIVY IMPORTS
# ================================================================

try:

    from kivy.app import App
    from kivy.clock import Clock
    from kivy.core.window import Window
    from kivy.metrics import dp, sp

    from kivy.graphics import Color, Rectangle, RoundedRectangle

    from kivy.properties import (
        StringProperty,
        NumericProperty,
        BooleanProperty
    )

    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.floatlayout import FloatLayout
    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.image import Image as KivyImage
    from kivy.uix.label import Label
    from kivy.uix.button import Button
    from kivy.uix.progressbar import ProgressBar
    from kivy.uix.scrollview import ScrollView
    from kivy.uix.widget import Widget
    from kivy.uix.popup import Popup
    from kivy.uix.textinput import TextInput
    from kivy.uix.behaviors import ButtonBehavior

except Exception:

    write_log(
        "KIVY IMPORT FAILED\n"
        + traceback.format_exc()
    )

    raise


# ================================================================
# PILLOW
# ================================================================

try:

    from PIL import Image

except Exception:

    write_log(
        "PILLOW IMPORT FAILED\n"
        + traceback.format_exc()
    )

    raise


# ================================================================
# WINDOW
# ================================================================

try:

    Window.clearcolor = (
        18 / 255,
        18 / 255,
        22 / 255,
        1
    )

except Exception:

    write_log(
        "WINDOW SETUP ERROR\n"
        + traceback.format_exc()
    )


# ================================================================
# COLORS
# ================================================================

BACKGROUND = (
    18 / 255,
    18 / 255,
    22 / 255,
    1
)

PANEL = (
    26 / 255,
    26 / 255,
    32 / 255,
    1
)

CARD = (
    42 / 255,
    42 / 255,
    51 / 255,
    1
)

CARD_BORDER = (
    58 / 255,
    58 / 255,
    68 / 255,
    1
)

BUTTON = (
    52 / 255,
    52 / 255,
    63 / 255,
    1
)

GREEN = (
    45 / 255,
    110 / 255,
    70 / 255,
    1
)

TEXT = (
    0.90,
    0.90,
    0.92,
    1
)

MUTED = (
    0.65,
    0.65,
    0.70,
    1
)


# ================================================================
# IMAGE SETTINGS
# ================================================================

IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".bmp",
    ".webp",
    ".gif",
    ".tif",
    ".tiff"
}

ALPHA_THRESHOLD = 10

COLOR_DISTANCE_THRESHOLD = 30

MIN_ISLAND_PIXELS = 6

MIN_OBJECT_WIDTH = 20

MIN_OBJECT_HEIGHT = 20

MIN_OBJECT_AREA = 150

RELATIVE_MIN_SIZE = 0.04


# ================================================================
# FILE HELPERS
# ================================================================

def is_image_file(path):

    try:

        return (
            path.is_file()
            and path.suffix.lower()
            in IMAGE_EXTENSIONS
        )

    except Exception:

        return False


def find_start_directory():

    locations = [
        "/storage/emulated/0/Pictures",
        "/storage/emulated/0/DCIM",
        "/storage/emulated/0",
        "/sdcard/Pictures",
        "/sdcard",
        str(Path.home()),
        str(Path.cwd())
    ]

    for location in locations:

        try:

            path = Path(location)

            if path.exists() and path.is_dir():

                return path

        except Exception:
            pass

    return Path.cwd()


def open_image(path):

    with Image.open(path) as image:

        return image.convert(
            "RGBA"
        ).copy()


# ================================================================
# SAVED PROGRESS (JSON) + CROP CACHE
#
# image_sizer_state.json  -> what the app was doing
# image_sizer_cache/      -> crops already made (PNG files)
#
# Both live in the same folder as image_sizer_error.log.
# The JSON is written after every finished image / saved crop,
# using a temp file + rename so a sudden close can never leave
# a half-written file behind.
# ================================================================

STATE_FILE = LOG_DIRECTORY / "image_sizer_state.json"

CACHE_DIRECTORY = LOG_DIRECTORY / "image_sizer_cache"

STATE_VERSION = 1

# If one image keeps killing the app, skip it after this many tries
MAX_FILE_ATTEMPTS = 3

state_write_lock = threading.Lock()


def new_job():

    return {
        "version": STATE_VERSION,
        "phase": "idle",
        "updated": "",
        "last_directory": "",
        "selected_files": [],
        "scale_enabled": False,
        "target_width": None,
        "target_height": None,
        "files_done": 0,
        "failed_files": [],
        "crash_counts": {},
        "crops": [],
        "preview_index": 0,
        "output_directory": "",
        "saved_cache": []
    }


def write_state(job):

    try:

        text = json.dumps(
            job,
            indent=2
        )

    except Exception:

        write_log(
            "STATE ENCODE ERROR\n"
            + traceback.format_exc()
        )

        return False

    with state_write_lock:

        temp = STATE_FILE.with_name(
            STATE_FILE.name + ".tmp"
        )

        try:

            with open(
                temp,
                "w",
                encoding="utf-8"
            ) as file:

                file.write(text)

                file.flush()

                try:
                    os.fsync(file.fileno())
                except Exception:
                    pass

            os.replace(
                str(temp),
                str(STATE_FILE)
            )

            return True

        except Exception:

            # Some storage types refuse the rename - fall back
            # to writing the file directly.

            try:

                with open(
                    STATE_FILE,
                    "w",
                    encoding="utf-8"
                ) as file:

                    file.write(text)

                return True

            except Exception:

                write_log(
                    "STATE WRITE ERROR\n"
                    + traceback.format_exc()
                )

                return False


def read_state():

    try:

        if not STATE_FILE.exists():

            return None

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if not isinstance(data, dict):

            raise ValueError(
                "state file is not a JSON object"
            )

        job = new_job()

        job.update(data)

        for key in (
            "selected_files",
            "failed_files",
            "crops",
            "saved_cache"
        ):

            if not isinstance(job.get(key), list):

                job[key] = []

        if not isinstance(job.get("crash_counts"), dict):

            job["crash_counts"] = {}

        job["crops"] = [
            entry
            for entry in job["crops"]
            if (
                isinstance(entry, dict)
                and "filename" in entry
                and "cache" in entry
            )
        ]

        try:

            job["files_done"] = max(
                0,
                int(job.get("files_done", 0))
            )

        except Exception:

            job["files_done"] = 0

        return job

    except Exception:

        write_log(
            "STATE READ ERROR (file ignored)\n"
            + traceback.format_exc()
        )

        try:

            os.replace(
                str(STATE_FILE),
                str(
                    STATE_FILE.with_name(
                        "image_sizer_state_corrupt.json"
                    )
                )
            )

        except Exception:
            pass

        return None


def clear_cache():

    try:

        shutil.rmtree(
            str(CACHE_DIRECTORY),
            ignore_errors=True
        )

    except Exception:
        pass


def save_crop_to_cache(
    image,
    cache_name
):

    CACHE_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True
    )

    image.save(
        str(CACHE_DIRECTORY / cache_name),
        "PNG",
        compress_level=1
    )


def load_cached_crops(entries):

    results = []

    valid = []

    for entry in entries:

        try:

            cache_name = str(entry.get("cache", ""))

            if not cache_name:

                continue

            with Image.open(
                CACHE_DIRECTORY / cache_name
            ) as source:

                image = source.convert(
                    "RGBA"
                ).copy()

            results.append(
                (
                    image,
                    str(entry["filename"])
                )
            )

            valid.append(entry)

        except Exception:

            write_log(
                "CACHED CROP MISSING (skipped)\n"
                + str(entry)
                + "\n"
                + traceback.format_exc()
            )

    return results, valid


# ================================================================
# PILLOW -> KIVY
# ================================================================

def pillow_to_texture(image):

    image = image.convert("RGBA")

    width, height = image.size

    from kivy.graphics.texture import Texture

    texture = Texture.create(
        size=(width, height),
        colorfmt="rgba"
    )

    texture.blit_buffer(
        image.tobytes(),
        colorfmt="rgba",
        bufferfmt="ubyte"
    )

    texture.flip_vertical()

    return texture


# ================================================================
# COLOR DISTANCE
# ================================================================

def color_distance(a, b):

    dr = int(a[0]) - int(b[0])
    dg = int(a[1]) - int(b[1])
    db = int(a[2]) - int(b[2])

    return (
        dr * dr +
        dg * dg +
        db * db
    ) ** 0.5


# ================================================================
# CORNER SAMPLE
# ================================================================

def sample_corner(
    pixels,
    center_x,
    center_y,
    width,
    height
):

    r = 0
    g = 0
    b = 0
    count = 0

    for dy in range(-2, 3):

        for dx in range(-2, 3):

            x = center_x + dx
            y = center_y + dy

            if x < 0 or y < 0:
                continue

            if x >= width or y >= height:
                continue

            pixel = pixels[x, y]

            r += pixel[0]
            g += pixel[1]
            b += pixel[2]

            count += 1

    if count == 0:

        return (0, 0, 0)

    return (
        r // count,
        g // count,
        b // count
    )


# ================================================================
# FOREGROUND MASK
# ================================================================

def make_foreground_mask(image):

    image = image.convert("RGBA")

    width, height = image.size

    pixels = image.load()

    sample_x = max(
        1,
        width // 50
    )

    sample_y = max(
        1,
        height // 50
    )

    has_transparency = False

    for y in range(
        0,
        height,
        sample_y
    ):

        for x in range(
            0,
            width,
            sample_x
        ):

            if pixels[x, y][3] < 250:

                has_transparency = True

                break

        if has_transparency:

            break

    mask = bytearray(
        width * height
    )

    # ------------------------------------------------------------
    # TRANSPARENT IMAGE
    # ------------------------------------------------------------

    if has_transparency:

        index = 0

        for y in range(height):

            for x in range(width):

                if pixels[x, y][3] > ALPHA_THRESHOLD:

                    mask[index] = 1

                index += 1

        return mask

    # ------------------------------------------------------------
    # SOLID BACKGROUND
    # ------------------------------------------------------------

    corners = [

        sample_corner(
            pixels,
            2,
            2,
            width,
            height
        ),

        sample_corner(
            pixels,
            width - 3,
            2,
            width,
            height
        ),

        sample_corner(
            pixels,
            2,
            height - 3,
            width,
            height
        ),

        sample_corner(
            pixels,
            width - 3,
            height - 3,
            width,
            height
        )
    ]

    background = (

        sum(c[0] for c in corners) // 4,

        sum(c[1] for c in corners) // 4,

        sum(c[2] for c in corners) // 4
    )

    index = 0

    for y in range(height):

        for x in range(width):

            if color_distance(
                pixels[x, y],
                background
            ) > COLOR_DISTANCE_THRESHOLD:

                mask[index] = 1

            index += 1

    return mask


# ================================================================
# CONNECTED COMPONENTS
# ================================================================

def find_connected_objects(
    mask,
    width,
    height
):

    visited = bytearray(
        width * height
    )

    objects = []

    neighbors = (
        (-1, -1),
        (0, -1),
        (1, -1),
        (-1, 0),
        (1, 0),
        (-1, 1),
        (0, 1),
        (1, 1)
    )

    for y in range(height):

        for x in range(width):

            index = y * width + x

            if not mask[index]:
                continue

            if visited[index]:
                continue

            queue = deque()

            queue.append((x, y))

            visited[index] = 1

            min_x = x
            max_x = x
            min_y = y
            max_y = y

            count = 0

            while queue:

                current_x, current_y = queue.popleft()

                count += 1

                min_x = min(
                    min_x,
                    current_x
                )

                max_x = max(
                    max_x,
                    current_x
                )

                min_y = min(
                    min_y,
                    current_y
                )

                max_y = max(
                    max_y,
                    current_y
                )

                for dx, dy in neighbors:

                    nx = current_x + dx
                    ny = current_y + dy

                    if nx < 0 or ny < 0:
                        continue

                    if nx >= width or ny >= height:
                        continue

                    next_index = ny * width + nx

                    if (
                        mask[next_index]
                        and not visited[next_index]
                    ):

                        visited[next_index] = 1

                        queue.append(
                            (nx, ny)
                        )

            if count >= MIN_ISLAND_PIXELS:

                objects.append(
                    (
                        min_x,
                        min_y,
                        max_x,
                        max_y,
                        count
                    )
                )

    objects.sort(
        key=lambda item: (
            item[1],
            item[0]
        )
    )

    return objects


# ================================================================
# FILTER OBJECTS
# ================================================================

def filter_objects(objects):

    if not objects:

        return []

    valid = []

    for item in objects:

        min_x, min_y, max_x, max_y, count = item

        width = max_x - min_x + 1
        height = max_y - min_y + 1

        if width < MIN_OBJECT_WIDTH:
            continue

        if height < MIN_OBJECT_HEIGHT:
            continue

        if count < MIN_OBJECT_AREA:
            continue

        valid.append(item)

    if not valid:

        return []

    largest = max(
        item[4]
        for item in valid
    )

    return [
        item
        for item in valid
        if item[4] >= largest * RELATIVE_MIN_SIZE
    ]


# ================================================================
# CROP
# ================================================================

def crop_image(
    image,
    mask,
    object_box
):

    min_x, min_y, max_x, max_y, _ = object_box

    crop = image.crop(
        (
            min_x,
            min_y,
            max_x + 1,
            max_y + 1
        )
    ).copy()

    pixels = crop.load()

    source_width = image.width

    crop_width = crop.width
    crop_height = crop.height

    for y in range(crop_height):

        source_y = min_y + y

        source_row = (
            source_y *
            source_width
        )

        for x in range(crop_width):

            source_x = min_x + x

            source_index = (
                source_row +
                source_x
            )

            if not mask[source_index]:

                r, g, b, a = pixels[x, y]

                pixels[x, y] = (
                    r,
                    g,
                    b,
                    0
                )

    return crop


# ================================================================
# RESIZE
# ================================================================

def resize_crop(
    crop,
    target_width,
    target_height
):

    return crop.resize(
        (
            int(target_width),
            int(target_height)
        ),
        Image.Resampling.LANCZOS
    )


# ================================================================
# PROCESS ONE IMAGE
# ================================================================

def process_image(
    path,
    scale_enabled=False,
    target_width=None,
    target_height=None
):

    image = open_image(path)

    width, height = image.size

    mask = make_foreground_mask(image)

    objects = find_connected_objects(
        mask,
        width,
        height
    )

    objects = filter_objects(objects)

    if not objects:

        return []

    base_name = Path(path).stem

    results = []

    for number, object_box in enumerate(
        objects,
        start=1
    ):

        crop = crop_image(
            image,
            mask,
            object_box
        )

        if scale_enabled:

            crop = resize_crop(
                crop,
                target_width,
                target_height
            )

        filename = (
            base_name
            + "_"
            + str(number).zfill(2)
            + ".png"
        )

        results.append(
            (
                crop,
                filename
            )
        )

    return results


# ================================================================
# SAFE BUTTON
# ================================================================

class AppButton(Button):

    primary = BooleanProperty(False)

    def __init__(
        self,
        **kwargs
    ):

        super().__init__(**kwargs)

        self.size_hint_y = None

        if "height" not in kwargs:

            self.height = dp(54)

        self.font_size = sp(16)
        self.color = TEXT

        # Hide Kivy's default square button texture. The button is
        # drawn below with a true rounded/pill shape instead.
        self.background_normal = ""
        self.background_down = ""
        self.background_disabled_normal = ""
        self.background_disabled_down = ""
        self.background_color = (0, 0, 0, 0)

        with self.canvas.before:
            self._pill_color = Color(*BUTTON)
            self._pill = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[(dp(27), dp(27))] * 4
            )

        self.bind(
            pos=self._sync_pill,
            size=self._sync_pill,
            state=self.update_background,
            primary=self.update_background,
            disabled=self.update_background
        )

        self.update_background()

    def _sync_pill(self, *args):

        self._pill.pos = self.pos
        self._pill.size = self.size

    def update_background(self, *args):

        if self.disabled:

            color = (
                48 / 255,
                48 / 255,
                56 / 255,
                0.55
            )

        elif self.state == "down":

            color = (
                35 / 255,
                150 / 255,
                95 / 255,
                1
            )

        elif self.primary:

            color = GREEN

        else:

            color = BUTTON

        self._pill_color.rgba = color
        self.background_color = (0, 0, 0, 0)


# ================================================================
# BACKGROUND MIXIN
# A tiny helper so any widget can carry a solid,
# persistent background rectangle that tracks its
# own size/position instead of leaving the layout
# transparent.
# ================================================================

class BackgroundMixin:

    def set_background(
        self,
        color,
        radius=None
    ):

        # radius is accepted but ignored - plain rectangles only.
        # Some low-end Android GPU drivers are unreliable with the
        # stencil/shader work RoundedRectangle needs, and it's not
        # worth risking a crash for rounded corners.

        with self.canvas.before:

            self._bg_color = Color(
                *color
            )

            self._bg_rect = Rectangle(
                pos=self.pos,
                size=self.size
            )

        self.bind(
            pos=self._update_background,
            size=self._update_background
        )

    def _update_background(
        self,
        *args
    ):

        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size


# ================================================================
# IMAGE CARD
# ================================================================

class ImageCard(
    BackgroundMixin,
    ButtonBehavior,
    FloatLayout
):

    selected = BooleanProperty(False)

    def __init__(
        self,
        path,
        texture,
        **kwargs
    ):

        super().__init__(**kwargs)

        self.path = path

        self.size_hint_y = None

        self.height = dp(270)

        self.set_background(
            CARD,
            radius=dp(10)
        )

        self.background = KivyImage(
            texture=texture,
            allow_stretch=True,
            keep_ratio=True,
            size_hint=(
                0.92,
                None
            ),
            height=dp(195),
            pos_hint={
                "center_x": 0.5,
                "top": 0.96
            }
        )

        self.add_widget(
            self.background
        )

        self.label = Label(
            text=path.name,
            color=TEXT,
            font_size=sp(13),
            halign="center",
            valign="middle",
            shorten=True,
            size_hint=(
                0.90,
                None
            ),
            height=dp(42),
            pos_hint={
                "center_x": 0.5,
                "y": 0.03
            }
        )

        self.label.bind(
            size=lambda instance, value:
            setattr(
                instance,
                "text_size",
                value
            )
        )

        self.add_widget(
            self.label
        )

        self.check = Label(
            text="✓",
            color=(
                0.3,
                1,
                0.5,
                1
            ),
            bold=True,
            font_size=sp(26),
            size_hint=(
                None,
                None
            ),
            size=(
                dp(40),
                dp(40)
            ),
            pos_hint={
                "right": 0.97,
                "top": 0.97
            },
            opacity=0
        )

        self.add_widget(
            self.check
        )

        self.bind(
            selected=self.selection_changed
        )

    def selection_changed(
        self,
        instance,
        value
    ):

        self.check.opacity = (
            1 if value else 0
        )

        # Highlight the card border color when selected
        # by swapping the background color slightly.
        self._bg_color.rgba = (
            GREEN if value else CARD
        )


# ================================================================
# FOLDER CARD
# ================================================================

class FolderCard(
    BackgroundMixin,
    ButtonBehavior,
    FloatLayout
):

    def __init__(
        self,
        path,
        **kwargs
    ):

        super().__init__(**kwargs)

        self.path = path

        self.size_hint_y = None

        self.height = dp(270)

        self.set_background(
            CARD,
            radius=dp(10)
        )

        folder = Label(
            text="[ FOLDER ]",
            color=TEXT,
            bold=True,
            font_size=sp(20),
            halign="center",
            valign="middle",
            size_hint=(
                1,
                0.68
            ),
            pos_hint={
                "x": 0,
                "top": 0.93
            }
        )

        self.add_widget(folder)

        label = Label(
            text=path.name,
            color=TEXT,
            font_size=sp(14),
            halign="center",
            valign="middle",
            shorten=True,
            size_hint=(
                0.90,
                None
            ),
            height=dp(46),
            pos_hint={
                "center_x": 0.5,
                "y": 0.04
            }
        )

        self.add_widget(label)


# ================================================================
# IMAGE BROWSER
# ================================================================

class ImageBrowser(
    BackgroundMixin,
    FloatLayout
):

    def __init__(
        self,
        start_directory,
        callback,
        **kwargs
    ):

        super().__init__(**kwargs)

        self.callback = callback

        self.current_directory = Path(
            start_directory
        )

        if not self.current_directory.exists():

            self.current_directory = (
                find_start_directory()
            )

        self.selected = set()

        self.cache = {}

        # Solid, persistent panel background so the
        # browser never looks see-through against
        # whatever is behind it, and doesn't flicker
        # or change as the grid refreshes.
        self.set_background(PANEL)

        self.build_ui()

        Clock.schedule_once(
            self.refresh,
            0
        )

    # ============================================================
    # UI
    # ============================================================

    def build_ui(self):

        top = BoxLayout(
            orientation="horizontal",
            size_hint=(
                1,
                None
            ),
            height=dp(72),
            pos_hint={
                "top": 1
            },
            spacing=dp(14),
            padding=dp(14)
        )

        self.up_button = AppButton(
            text="UP",
            size_hint_x=None,
            width=dp(100)
        )

        self.path_label = Label(
            text="",
            color=TEXT,
            font_size=sp(13),
            halign="center",
            valign="middle",
            shorten=True
        )

        self.cancel_button = AppButton(
            text="CANCEL",
            size_hint_x=None,
            width=dp(120)
        )

        top.add_widget(
            self.up_button
        )

        top.add_widget(
            self.path_label
        )

        top.add_widget(
            self.cancel_button
        )

        self.add_widget(top)

        self.scroll = ScrollView(
            size_hint=(
                1,
                None
            ),
            pos_hint={
                "x": 0,
                "y": 0.14
            },
            do_scroll_x=False
        )

        self.grid = GridLayout(
            cols=4,
            spacing=dp(16),
            padding=dp(16),
            size_hint_y=None
        )

        self.grid.bind(
            minimum_height=self.grid.setter(
                "height"
            )
        )

        self.scroll.add_widget(
            self.grid
        )

        self.add_widget(
            self.scroll
        )

        bottom = BoxLayout(
            orientation="horizontal",
            size_hint=(
                1,
                None
            ),
            height=dp(82),
            pos_hint={
                "x": 0,
                "y": 0
            },
            padding=dp(14)
        )

        self.add_files = AppButton(
            text="ADD FILES (0)",
            primary=True,
            size_hint_x=None,
            width=dp(270)
        )

        bottom.add_widget(
            Widget()
        )

        bottom.add_widget(
            self.add_files
        )

        bottom.add_widget(
            Widget()
        )

        self.add_widget(bottom)

        self.up_button.bind(
            on_release=self.go_up
        )

        self.cancel_button.bind(
            on_release=self.cancel
        )

        self.add_files.bind(
            on_release=self.confirm
        )

        self.bind(
            size=self.resize
        )

    # ============================================================
    # RESIZE
    # ============================================================

    def resize(
        self,
        *args
    ):

        self.scroll.height = max(
            dp(270),
            self.height - dp(160)
        )

        if self.width >= dp(1100):

            self.grid.cols = 5

        elif self.width >= dp(800):

            self.grid.cols = 4

        else:

            self.grid.cols = 3

    # ============================================================
    # REFRESH
    # ============================================================

    def refresh(
        self,
        *args
    ):

        try:

            self.selected.clear()

            self.cache.clear()

            folders = []
            images = []

            try:

                entries = list(
                    self.current_directory.iterdir()
                )

            except Exception:

                entries = []

            for entry in entries:

                try:

                    if entry.is_dir():

                        folders.append(entry)

                    elif is_image_file(entry):

                        images.append(entry)

                except Exception:
                    pass

            folders.sort(
                key=lambda p:
                p.name.lower()
            )

            images.sort(
                key=lambda p:
                p.name.lower()
            )

            self.grid.clear_widgets()

            items = []

            for folder in folders:

                items.append(
                    ("folder", folder)
                )

            for image in images:

                items.append(
                    ("image", image)
                )

            columns = max(
                1,
                self.grid.cols
            )

            for start in range(
                0,
                len(items),
                columns
            ):

                row = BoxLayout(
                    orientation="horizontal",
                    size_hint_y=None,
                    height=dp(280),
                    spacing=dp(16)
                )

                row_items = items[
                    start:
                    start + columns
                ]

                for item_type, path in row_items:

                    if item_type == "folder":

                        card = FolderCard(
                            path
                        )

                        card.bind(
                            on_release=lambda instance,
                            p=path:
                            self.open_folder(p)
                        )

                    else:

                        texture = self.thumbnail(path)

                        card = ImageCard(
                            path,
                            texture
                        )

                        card.bind(
                            on_release=lambda instance,
                            p=path,
                            c=card:
                            self.toggle(p, c)
                        )

                    row.add_widget(card)

                while len(row.children) < columns:

                    row.add_widget(
                        Widget()
                    )

                self.grid.add_widget(row)

            self.path_label.text = str(
                self.current_directory
            )

            self.update_counter()

        except Exception:

            write_log(
                "BROWSER REFRESH ERROR\n"
                + traceback.format_exc()
            )

    # ============================================================
    # THUMBNAIL
    # ============================================================

    def thumbnail(
        self,
        path
    ):

        key = str(path)

        if key in self.cache:

            return self.cache[key]

        try:

            with Image.open(path) as source:

                image = source.convert(
                    "RGBA"
                )

                image.thumbnail(
                    (
                        220,
                        180
                    ),
                    Image.Resampling.LANCZOS
                )

                texture = pillow_to_texture(
                    image
                )

            self.cache[key] = texture

            return texture

        except Exception:

            write_log(
                "THUMBNAIL ERROR\n"
                + str(path)
                + "\n"
                + traceback.format_exc()
            )

            self.cache[key] = None

            return None

    # ============================================================
    # FOLDER
    # ============================================================

    def open_folder(
        self,
        path,
        *args
    ):

        try:

            if path.is_dir():

                self.current_directory = path

                self.refresh()

                self.scroll.scroll_y = 1

        except Exception:

            write_log(
                "OPEN FOLDER ERROR\n"
                + traceback.format_exc()
            )

    # ============================================================
    # UP
    # ============================================================

    def go_up(
        self,
        *args
    ):

        try:

            parent = self.current_directory.parent

            if parent != self.current_directory:

                self.current_directory = parent

                self.refresh()

        except Exception:

            write_log(
                "GO UP ERROR\n"
                + traceback.format_exc()
            )

    # ============================================================
    # SELECT
    # ============================================================

    def toggle(
        self,
        path,
        card
    ):

        key = str(path)

        if key in self.selected:

            self.selected.remove(key)

            card.selected = False

        else:

            self.selected.add(key)

            card.selected = True

        self.update_counter()

    # ============================================================
    # COUNTER
    # ============================================================

    def update_counter(self):

        self.add_files.text = (
            "ADD FILES ("
            + str(len(self.selected))
            + ")"
        )

    # ============================================================
    # CANCEL
    # ============================================================

    def cancel(
        self,
        *args
    ):

        self.callback(
            False,
            []
        )

    # ============================================================
    # CONFIRM
    # ============================================================

    def confirm(
        self,
        *args
    ):

        if not self.selected:

            App.get_running_app().show_message(
                "No images selected",
                "Select one or more images first."
            )

            return

        self.callback(
            True,
            list(self.selected)
        )


# ================================================================
# MAIN APP
# ================================================================

class ImageSizerApp(App):

    title = "Image Sizer v5"

    status_text = StringProperty(
        "READY"
    )

    progress_value = NumericProperty(0)

    progress_max = NumericProperty(1)

    processing = BooleanProperty(False)

    def __init__(
        self,
        **kwargs
    ):

        super().__init__(**kwargs)

        self.root_layout = None

        self.browser = None

        self.selected_files = []

        self.crops = []

        self.preview_index = 0

        self.last_directory = str(
            find_start_directory()
        )

        self.messages = deque()

        self.worker = None

        self.stop_worker = False

        self.scale_enabled = False

        self.target_width = None

        self.target_height = None

        self.spinner_index = 0

        self.status = None

        self.preview = None

        self.progress = None

        self.spinner = None

        self.job = new_job()

        self.job_lock = threading.Lock()

    # ============================================================
    # BUILD
    # ============================================================

    def build(self):

        write_log(
            "BUILD STARTED"
        )

        try:

            root = FloatLayout()

            self.root_layout = root

            # ----------------------------------------------------
            # TOP BAR
            # ----------------------------------------------------

            top = BoxLayout(
                orientation="horizontal",
                size_hint=(
                    1,
                    None
                ),
                height=dp(70),
                pos_hint={
                    "top": 1
                },
                padding=dp(12),
                spacing=dp(12)
            )

            self.browse = AppButton(
                text="BROWSE",
                size_hint_x=None,
                width=dp(125)
            )

            self.process = AppButton(
                text="PROCESS",
                size_hint_x=None,
                width=dp(130)
            )

            self.save = AppButton(
                text="SAVE",
                primary=True,
                size_hint_x=None,
                width=dp(110)
            )

            top.add_widget(self.browse)
            top.add_widget(self.process)
            top.add_widget(self.save)

            top.add_widget(
                Widget()
            )

            self.previous = AppButton(
                text="<",
                size_hint_x=None,
                width=dp(58)
            )

            self.next = AppButton(
                text=">",
                size_hint_x=None,
                width=dp(58)
            )

            top.add_widget(self.previous)
            top.add_widget(self.next)

            root.add_widget(top)

            # ----------------------------------------------------
            # STATUS
            # ----------------------------------------------------

            self.status = Label(
                text="READY",
                color=TEXT,
                font_size=sp(14),
                halign="center",
                valign="middle",
                shorten=True,
                size_hint=(
                    0.90,
                    None
                ),
                height=dp(30),
                pos_hint={
                    "center_x": 0.5,
                    "top": 0.88
                }
            )

            self.status.bind(
                size=lambda instance, value:
                setattr(
                    instance,
                    "text_size",
                    value
                )
            )

            root.add_widget(
                self.status
            )

            # ----------------------------------------------------
            # PREVIEW
            # ----------------------------------------------------

            self.preview = KivyImage(
                allow_stretch=True,
                keep_ratio=True,
                size_hint=(
                    0.90,
                    0.68
                ),
                pos_hint={
                    "center_x": 0.5,
                    "center_y": 0.45
                }
            )

            root.add_widget(
                self.preview
            )

            # ----------------------------------------------------
            # PROGRESS
            # ----------------------------------------------------

            self.progress = ProgressBar(
                max=1,
                value=0,
                size_hint=(
                    0.75,
                    None
                ),
                height=dp(8),
                pos_hint={
                    "center_x": 0.5,
                    "y": 0.055
                },
                opacity=0
            )

            root.add_widget(
                self.progress
            )

            # ----------------------------------------------------
            # SPINNER
            # ----------------------------------------------------

            self.spinner = Label(
                text="",
                color=(
                    0.40,
                    0.90,
                    0.60,
                    1
                ),
                font_size=sp(14),
                size_hint=(
                    0.8,
                    None
                ),
                height=dp(25),
                pos_hint={
                    "center_x": 0.5,
                    "y": 0.085
                },
                opacity=0
            )

            root.add_widget(
                self.spinner
            )

            # ----------------------------------------------------
            # EVENTS
            # ----------------------------------------------------

            self.browse.bind(
                on_release=self.open_browser
            )

            self.process.bind(
                on_release=self.start_process_confirmation
            )

            self.save.bind(
                on_release=self.start_saving
            )

            self.previous.bind(
                on_release=self.previous_crop
            )

            self.next.bind(
                on_release=self.next_crop
            )

            self.bind(
                status_text=self.status_changed
            )

            self.bind(
                progress_value=self.progress_changed
            )

            Clock.schedule_interval(
                self.poll_worker,
                0.10
            )

            Clock.schedule_interval(
                self.animate_spinner,
                0.25
            )

            self.set_status(
                "READY - TAP BROWSE"
            )

            Clock.schedule_once(
                self.restore_state,
                0.6
            )

            write_log(
                "BUILD FINISHED SUCCESSFULLY"
            )

            return root

        except Exception:

            write_log(
                "BUILD CRASH\n"
                + traceback.format_exc()
            )

            raise

    # ============================================================
    # STATUS
    # ============================================================

    def set_status(
        self,
        text
    ):

        self.status_text = str(text)

    def status_changed(
        self,
        instance,
        value
    ):

        if self.status:

            self.status.text = str(value)

    def progress_changed(
        self,
        instance,
        value
    ):

        if self.progress:

            self.progress.max = max(
                1,
                self.progress_max
            )

            self.progress.value = value

    # ============================================================
    # BROWSER
    # ============================================================

    def open_browser(
        self,
        *args
    ):

        if self.processing:

            self.set_status(
                "BUSY - CURRENT JOB IS RUNNING"
            )

            return

        try:

            self.browser = ImageBrowser(
                self.last_directory,
                self.browser_finished
            )

            self.root_layout.add_widget(
                self.browser
            )

        except Exception:

            write_log(
                "OPEN BROWSER CRASH\n"
                + traceback.format_exc()
            )

            self.show_message(
                "Browser error",
                "Could not open the image browser."
            )

    # ============================================================
    # BROWSER RESULT
    # ============================================================

    def browser_finished(
        self,
        confirmed,
        files
    ):

        try:

            if self.browser:

                self.root_layout.remove_widget(
                    self.browser
                )

                self.browser = None

            if not confirmed:

                self.set_status(
                    "BROWSE CANCELLED"
                )

                return

            if not files:

                return

            self.selected_files = list(files)

            self.last_directory = str(
                Path(files[0]).parent
            )

            self.crops = []

            self.preview.texture = None

            self.preview_index = 0

            self.reset_job("selected")

            self.update_job(
                selected_files=list(files)
            )

            self.set_status(
                str(len(files))
                + " IMAGE(S) READY - TAP PROCESS"
            )

        except Exception:

            write_log(
                "BROWSER FINISH ERROR\n"
                + traceback.format_exc()
            )

    # ============================================================
    # PROCESS BUTTON
    # ============================================================

    def start_process_confirmation(
        self,
        *args
    ):

        if self.processing:

            self.set_status(
                "ALREADY WORKING..."
            )

            return

        if not self.selected_files:

            self.show_message(
                "No images",
                "Tap BROWSE and select images first."
            )

            return

        self.show_scale_confirmation()

    # ============================================================
    # SCALE QUESTION
    # ============================================================

    def show_scale_confirmation(self):

        box = BoxLayout(
            orientation="vertical",
            padding=dp(15),
            spacing=dp(12)
        )

        message = Label(
            text=(
                "Do you want to scale the "
                "cropped images to another size?"
            ),
            color=TEXT,
            font_size=sp(17),
            halign="center",
            valign="middle"
        )

        message.bind(
            size=lambda instance, value:
            setattr(
                instance,
                "text_size",
                value
            )
        )

        buttons = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(55),
            spacing=dp(10)
        )

        no_button = AppButton(
            text="NO"
        )

        yes_button = AppButton(
            text="YES",
            primary=True
        )

        buttons.add_widget(no_button)
        buttons.add_widget(yes_button)

        box.add_widget(message)
        box.add_widget(buttons)

        popup = Popup(
            title="Scale Cropped Images?",
            content=box,
            size_hint=(
                0.70,
                0.40
            ),
            auto_dismiss=False
        )

        no_button.bind(
            on_release=lambda *args:
            self.scale_no(popup)
        )

        yes_button.bind(
            on_release=lambda *args:
            self.scale_yes(popup)
        )

        popup.open()

    # ============================================================
    # NO SCALING
    # ============================================================

    def scale_no(
        self,
        popup
    ):

        popup.dismiss()

        self.scale_enabled = False

        self.target_width = None

        self.target_height = None

        self.begin_processing()

    # ============================================================
    # YES SCALING
    # ============================================================

    def scale_yes(
        self,
        popup
    ):

        popup.dismiss()

        self.show_dimensions_popup()

    # ============================================================
    # DIMENSIONS
    # ============================================================

    def show_dimensions_popup(self):

        box = BoxLayout(
            orientation="vertical",
            padding=dp(15),
            spacing=dp(10)
        )

        info = Label(
            text="Enter the output width and height in pixels.",
            color=TEXT,
            font_size=sp(15),
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(45)
        )

        info.bind(
            size=lambda instance, value:
            setattr(
                instance,
                "text_size",
                value
            )
        )

        fields = BoxLayout(
            orientation="horizontal",
            spacing=dp(15),
            size_hint_y=None,
            height=dp(70)
        )

        width_box = BoxLayout(
            orientation="vertical",
            spacing=dp(4)
        )

        height_box = BoxLayout(
            orientation="vertical",
            spacing=dp(4)
        )

        width_label = Label(
            text="WIDTH",
            color=MUTED,
            size_hint_y=None,
            height=dp(25)
        )

        height_label = Label(
            text="HEIGHT",
            color=MUTED,
            size_hint_y=None,
            height=dp(25)
        )

        self.width_input = TextInput(
            hint_text="Width",
            input_filter="int",
            multiline=False,
            font_size=sp(18),
            halign="center"
        )

        self.height_input = TextInput(
            hint_text="Height",
            input_filter="int",
            multiline=False,
            font_size=sp(18),
            halign="center"
        )

        width_box.add_widget(width_label)
        width_box.add_widget(self.width_input)

        height_box.add_widget(height_label)
        height_box.add_widget(self.height_input)

        fields.add_widget(width_box)
        fields.add_widget(height_box)

        buttons = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(55),
            spacing=dp(10)
        )

        cancel = AppButton(
            text="CANCEL"
        )

        continue_button = AppButton(
            text="CONTINUE",
            primary=True
        )

        buttons.add_widget(cancel)
        buttons.add_widget(continue_button)

        box.add_widget(info)
        box.add_widget(fields)
        box.add_widget(Widget())
        box.add_widget(buttons)

        popup = Popup(
            title="Crop Output Size",
            content=box,
            size_hint=(
                0.70,
                0.58
            ),
            auto_dismiss=False
        )

        cancel.bind(
            on_release=lambda *args:
            popup.dismiss()
        )

        continue_button.bind(
            on_release=lambda *args:
            self.accept_dimensions(popup)
        )

        popup.open()

        Clock.schedule_once(
            lambda dt:
            setattr(
                self.width_input,
                "focus",
                True
            ),
            0.2
        )

    # ============================================================
    # ACCEPT DIMENSIONS
    # ============================================================

    def accept_dimensions(
        self,
        popup
    ):

        width_text = (
            self.width_input.text.strip()
        )

        height_text = (
            self.height_input.text.strip()
        )

        if not width_text:

            self.show_message(
                "Width required",
                "Enter a width in digits."
            )

            return

        if not height_text:

            self.show_message(
                "Height required",
                "Enter a height in digits."
            )

            return

        try:

            width = int(width_text)
            height = int(height_text)

        except Exception:

            self.show_message(
                "Invalid dimensions",
                "Width and height must contain digits only."
            )

            return

        if width <= 0 or height <= 0:

            self.show_message(
                "Invalid dimensions",
                "Width and height must be greater than zero."
            )

            return

        if width > 20000 or height > 20000:

            self.show_message(
                "Dimensions too large",
                "Maximum allowed size is 20,000 × 20,000."
            )

            return

        self.scale_enabled = True

        self.target_width = width

        self.target_height = height

        popup.dismiss()

        self.begin_processing()

    # ============================================================
    # BEGIN PROCESSING
    # ============================================================

    def begin_processing(self):

        self.crops = []

        self.preview.texture = None

        self.preview_index = 0

        clear_cache()

        self.update_job(
            phase="processing",
            selected_files=list(self.selected_files),
            scale_enabled=self.scale_enabled,
            target_width=self.target_width,
            target_height=self.target_height,
            files_done=0,
            failed_files=[],
            crash_counts={},
            crops=[],
            preview_index=0,
            output_directory="",
            saved_cache=[]
        )

        self.stop_worker = False

        self.processing = True

        self.progress_value = 0

        self.progress_max = len(
            self.selected_files
        )

        self.progress.opacity = 1

        self.spinner.opacity = 1

        if self.scale_enabled:

            self.set_status(
                "PROCESSING + SCALING..."
            )

            message = (
                "Processing has started.\n\n"
                "Output size: "
                + str(self.target_width)
                + " × "
                + str(self.target_height)
                + " pixels."
            )

        else:

            self.set_status(
                "PROCESSING CROPS..."
            )

            message = (
                "Processing has started.\n\n"
                "The crops will keep their "
                "normal detected dimensions."
            )

        self.show_message(
            "PROCESS STARTED",
            message
            + "\n\n"
            "The work is running in the background.\n"
            "Progress is saved automatically.",
            auto_close=True
        )

        self.worker = threading.Thread(
            target=self.processing_worker,
            args=(
                list(self.selected_files),
                self.scale_enabled,
                self.target_width,
                self.target_height
            ),
            daemon=True
        )

        self.worker.start()

    # ============================================================
    # SAVED PROGRESS (JSON)
    #
    # Every important step is written to image_sizer_state.json
    # (same folder as the error log). If Pydroid 3 closes the
    # app in the background, the next launch reads that file and
    # carries on from where it stopped.
    # ============================================================

    def stamp_job(self):

        self.job["updated"] = time.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    def update_job(
        self,
        **changes
    ):

        try:

            with self.job_lock:

                self.job.update(changes)

                self.stamp_job()

                write_state(self.job)

        except Exception:

            write_log(
                "UPDATE JOB ERROR\n"
                + traceback.format_exc()
            )

    def mutate_job(
        self,
        function
    ):

        try:

            with self.job_lock:

                function(self.job)

                self.stamp_job()

                write_state(self.job)

        except Exception:

            write_log(
                "MUTATE JOB ERROR\n"
                + traceback.format_exc()
            )

    def reset_job(
        self,
        phase="idle"
    ):

        clear_cache()

        with self.job_lock:

            self.job = new_job()

            self.job["phase"] = phase

            self.job["last_directory"] = str(
                self.last_directory
            )

            self.stamp_job()

            write_state(self.job)

    def snapshot_state(self):

        self.update_job(
            preview_index=self.preview_index,
            last_directory=str(
                self.last_directory
            )
        )

    def job_file_started(
        self,
        path
    ):

        def change(job):

            counts = job.setdefault(
                "crash_counts",
                {}
            )

            counts[path] = (
                int(counts.get(path, 0)) + 1
            )

        self.mutate_job(change)

    def job_file_finished(
        self,
        current,
        path,
        cache_entries
    ):

        def change(job):

            job["crops"].extend(
                cache_entries
            )

            job["files_done"] = current

            job.setdefault(
                "crash_counts",
                {}
            ).pop(path, None)

        self.mutate_job(change)

    def job_file_failed(
        self,
        current,
        path
    ):

        def change(job):

            job["failed_files"].append(path)

            job["files_done"] = current

            job.setdefault(
                "crash_counts",
                {}
            ).pop(path, None)

        self.mutate_job(change)

    def job_crop_saved(
        self,
        cache_name
    ):

        def change(job):

            job["saved_cache"].append(
                cache_name
            )

        self.mutate_job(change)

    # ============================================================
    # RESTORE ON START
    # ============================================================

    def restore_state(
        self,
        *args
    ):

        try:

            if self.processing:

                return

            job = read_state()

            if not job:

                return

            phase = job.get(
                "phase",
                "idle"
            )

            files = [
                str(item)
                for item in job.get(
                    "selected_files",
                    []
                )
            ]

            with self.job_lock:

                self.job = job

            last_directory = str(
                job.get("last_directory", "")
                or ""
            )

            if (
                last_directory
                and Path(last_directory).exists()
            ):

                self.last_directory = last_directory

            self.selected_files = files

            self.scale_enabled = bool(
                job.get("scale_enabled", False)
            )

            self.target_width = job.get(
                "target_width"
            )

            self.target_height = job.get(
                "target_height"
            )

            try:

                self.preview_index = max(
                    0,
                    int(job.get("preview_index", 0))
                )

            except Exception:

                self.preview_index = 0

            write_log(
                "SAVED JOB FOUND - PHASE: "
                + str(phase)
            )

            if phase == "selected" and files:

                self.set_status(
                    str(len(files))
                    + " IMAGE(S) READY - TAP PROCESS"
                )

            elif phase == "processing" and files:

                done = int(
                    job.get("files_done", 0)
                )

                write_log(
                    "RESUMING PROCESSING AT IMAGE "
                    + str(done + 1)
                    + " OF "
                    + str(len(files))
                )

                self.show_message(
                    "RESUMING JOB",
                    "Continuing where the app stopped."
                    "\n\n"
                    "Image "
                    + str(
                        min(done + 1, len(files))
                    )
                    + " of "
                    + str(len(files)),
                    auto_close=True
                )

                self.resume_processing()

            elif (
                phase in ("processed", "saving")
                and job.get("crops")
            ):

                if phase == "saving":

                    action = "save"

                else:

                    action = "review"

                write_log(
                    "RESTORING SAVED CROPS - NEXT: "
                    + action
                )

                self.processing = True

                self.stop_worker = False

                self.spinner.opacity = 1

                self.set_status(
                    "RESTORING SAVED CROPS..."
                )

                self.worker = threading.Thread(
                    target=self.restore_worker,
                    args=(action,),
                    daemon=True
                )

                self.worker.start()

        except Exception:

            write_log(
                "RESTORE STATE ERROR\n"
                + traceback.format_exc()
            )

    def resume_processing(self):

        self.crops = []

        self.preview.texture = None

        self.stop_worker = False

        self.processing = True

        self.progress_max = max(
            1,
            len(self.selected_files)
        )

        self.progress_value = int(
            self.job.get("files_done", 0)
        )

        self.progress.opacity = 1

        self.spinner.opacity = 1

        self.set_status(
            "RESUMING..."
        )

        self.worker = threading.Thread(
            target=self.processing_worker,
            args=(
                list(self.selected_files),
                self.scale_enabled,
                self.target_width,
                self.target_height,
                True
            ),
            daemon=True
        )

        self.worker.start()

    def restore_worker(
        self,
        action
    ):

        try:

            with self.job_lock:

                entries = list(
                    self.job.get("crops", [])
                )

            results, valid = load_cached_crops(
                entries
            )

            if len(valid) != len(entries):

                self.update_job(
                    crops=valid
                )

            self.messages.append(
                (
                    "restore_finished",
                    results,
                    action
                )
            )

        except Exception:

            write_log(
                "RESTORE THREAD CRASH\n"
                + traceback.format_exc()
            )

            self.messages.append(
                (
                    "fatal",
                    "Restoring the saved job crashed."
                )
            )

    # ============================================================
    # PROCESS WORKER
    # ============================================================

    def processing_worker(
        self,
        files,
        scale_enabled,
        target_width,
        target_height,
        resume=False
    ):

        results = []

        try:

            total = len(files)

            with self.job_lock:

                files_done = int(
                    self.job.get("files_done", 0)
                )

            # --------------------------------------------------------
            # RESUME - reload the crops the earlier run already made
            # --------------------------------------------------------

            if resume:

                with self.job_lock:

                    entries = list(
                        self.job.get("crops", [])
                    )

                results, valid = load_cached_crops(
                    entries
                )

                if len(valid) != len(entries):

                    self.update_job(
                        crops=valid
                    )

            for current, path in enumerate(
                files,
                start=1
            ):

                if self.stop_worker:

                    break

                # Already finished before the app was closed
                if current <= files_done:

                    continue

                # --------------------------------------------------
                # An image that keeps killing the app is skipped
                # --------------------------------------------------

                with self.job_lock:

                    crashes = int(
                        self.job.get(
                            "crash_counts",
                            {}
                        ).get(path, 0)
                    )

                if crashes >= MAX_FILE_ATTEMPTS:

                    write_log(
                        "SKIPPING IMAGE - IT STOPPED THE APP "
                        + str(crashes)
                        + " TIMES\n"
                        + str(path)
                    )

                    self.job_file_failed(
                        current,
                        path
                    )

                    self.messages.append(
                        (
                            "file_error",
                            Path(path).name,
                            "Skipped - it stopped the app "
                            + str(crashes)
                            + " times"
                        )
                    )

                    continue

                self.job_file_started(path)

                try:

                    output = process_image(
                        path,
                        scale_enabled,
                        target_width,
                        target_height
                    )

                    cache_entries = []

                    for crop, filename in output:

                        cache_name = (
                            str(current).zfill(5)
                            + "_"
                            + filename
                        )

                        try:

                            save_crop_to_cache(
                                crop,
                                cache_name
                            )

                        except Exception:

                            write_log(
                                "CACHE WRITE ERROR\n"
                                + cache_name
                                + "\n"
                                + traceback.format_exc()
                            )

                            cache_name = ""

                        cache_entries.append(
                            {
                                "filename": filename,
                                "cache": cache_name
                            }
                        )

                    results.extend(output)

                    self.job_file_finished(
                        current,
                        path,
                        cache_entries
                    )

                    self.messages.append(
                        (
                            "process_progress",
                            current,
                            total,
                            Path(path).name,
                            len(output)
                        )
                    )

                except Exception as exc:

                    write_log(
                        "IMAGE PROCESS ERROR\n"
                        + str(path)
                        + "\n\n"
                        + traceback.format_exc()
                    )

                    self.job_file_failed(
                        current,
                        path
                    )

                    self.messages.append(
                        (
                            "file_error",
                            Path(path).name,
                            str(exc)
                        )
                    )

            if not self.stop_worker:

                if results:

                    self.update_job(
                        phase="processed"
                    )

                else:

                    self.update_job(
                        phase="selected"
                    )

            self.messages.append(
                (
                    "process_finished",
                    results
                )
            )

        except Exception:

            write_log(
                "PROCESS THREAD CRASH\n"
                + traceback.format_exc()
            )

            self.messages.append(
                (
                    "fatal",
                    "Processing crashed."
                )
            )

    # ============================================================
    # SAVE
    # ============================================================

    def start_saving(
        self,
        *args,
        resume=False
    ):

        if self.processing:

            self.set_status(
                "CURRENT JOB STILL RUNNING"
            )

            return

        if not self.crops:

            self.show_message(
                "Nothing to save",
                "Process the images first."
            )

            return

        output_directory = ""

        already_saved = []

        if resume:

            with self.job_lock:

                output_directory = str(
                    self.job.get(
                        "output_directory",
                        ""
                    ) or ""
                )

                already_saved = list(
                    self.job.get(
                        "saved_cache",
                        []
                    )
                )

        if not output_directory:

            if self.selected_files:

                output_directory = str(
                    Path(
                        self.selected_files[0]
                    ).parent / "crops"
                )

            else:

                output_directory = str(
                    LOG_DIRECTORY / "crops"
                )

        self.update_job(
            phase="saving",
            output_directory=output_directory,
            saved_cache=list(already_saved)
        )

        self.processing = True

        self.stop_worker = False

        self.progress_max = len(
            self.crops
        )

        self.progress_value = len(
            already_saved
        )

        self.progress.opacity = 1

        self.spinner.opacity = 1

        self.set_status(
            "SAVING CROPS..."
        )

        if resume:

            self.show_message(
                "SAVE RESUMED",
                "Continuing to save the crops where "
                "the app stopped.",
                auto_close=True
            )

        else:

            self.show_message(
                "SAVE STARTED",
                "Saving crops into the crops folder.",
                auto_close=True
            )

        self.worker = threading.Thread(
            target=self.saving_worker,
            args=(
                output_directory,
                set(already_saved)
            ),
            daemon=True
        )

        self.worker.start()

    # ============================================================
    # SAVE WORKER
    # ============================================================

    def saving_worker(
        self,
        output_directory,
        already_saved
    ):

        try:

            output_directory = Path(
                output_directory
            )

            output_directory.mkdir(
                parents=True,
                exist_ok=True
            )

            with self.job_lock:

                entries = list(
                    self.job.get("crops", [])
                )

            crops = list(self.crops)

            saved = 0

            errors = []

            total = len(crops)

            for current, item in enumerate(
                crops,
                start=1
            ):

                if self.stop_worker:

                    break

                image, filename = item

                cache_name = ""

                if current - 1 < len(entries):

                    cache_name = str(
                        entries[current - 1].get(
                            "cache",
                            ""
                        )
                    )

                # Saved before the app was closed
                if (
                    cache_name
                    and cache_name in already_saved
                ):

                    saved += 1

                    self.messages.append(
                        (
                            "save_progress",
                            current,
                            total,
                            filename
                        )
                    )

                    continue

                try:

                    output_path = (
                        output_directory /
                        filename
                    )

                    image.save(
                        str(output_path),
                        "PNG"
                    )

                    saved += 1

                    if cache_name:

                        self.job_crop_saved(
                            cache_name
                        )

                    self.messages.append(
                        (
                            "save_progress",
                            current,
                            total,
                            filename
                        )
                    )

                except Exception as exc:

                    errors.append(
                        filename
                        + ": "
                        + str(exc)
                    )

                    write_log(
                        "SAVE ERROR\n"
                        + filename
                        + "\n"
                        + traceback.format_exc()
                    )

            # All saved cleanly -> the job is finished and the
            # temporary crop cache is no longer needed.
            # Problems or a stop -> keep everything so the crops
            # can still be saved again.

            if errors or self.stop_worker:

                self.update_job(
                    phase="processed"
                )

            else:

                clear_cache()

                self.update_job(
                    phase="done",
                    crops=[],
                    saved_cache=[]
                )

            self.messages.append(
                (
                    "save_finished",
                    str(output_directory),
                    saved,
                    errors
                )
            )

        except Exception:

            write_log(
                "SAVE THREAD CRASH\n"
                + traceback.format_exc()
            )

            self.messages.append(
                (
                    "fatal",
                    "Saving crashed."
                )
            )

    # ============================================================
    # MESSAGE PUMP
    # ============================================================

    def poll_worker(
        self,
        *args
    ):

        while self.messages:

            message = self.messages.popleft()

            kind = message[0]

            if kind == "process_progress":

                (
                    _,
                    current,
                    total,
                    filename,
                    found
                ) = message

                self.progress_max = total

                self.progress_value = current

                self.set_status(
                    "PROCESSING "
                    + str(current)
                    + "/"
                    + str(total)
                    + " - "
                    + filename
                    + " - "
                    + str(found)
                    + " CROPS"
                )

            elif kind == "file_error":

                _, filename, error = message

                self.set_status(
                    "ERROR: " + filename
                )

                write_log(
                    filename
                    + "\n"
                    + error
                )

            elif kind == "process_finished":

                _, results = message

                self.crops = results

                self.processing = False

                self.progress.opacity = 0

                self.spinner.opacity = 0

                self.worker = None

                if self.crops:

                    self.preview_index = 0

                    self.show_crop()

                    if self.scale_enabled:

                        self.set_status(
                            "FOUND "
                            + str(len(self.crops))
                            + " SCALED CROPS - TAP SAVE"
                        )

                    else:

                        self.set_status(
                            "FOUND "
                            + str(len(self.crops))
                            + " CROPS - TAP SAVE"
                        )

                else:

                    self.set_status(
                        "NO LARGE OBJECTS FOUND"
                    )

                    self.show_message(
                        "Finished",
                        "No large enough objects were found."
                    )

            elif kind == "save_progress":

                (
                    _,
                    current,
                    total,
                    filename
                ) = message

                self.progress_max = total

                self.progress_value = current

                self.set_status(
                    "SAVING "
                    + str(current)
                    + "/"
                    + str(total)
                    + " - "
                    + filename
                )

            elif kind == "save_finished":

                (
                    _,
                    directory,
                    saved,
                    errors
                ) = message

                self.processing = False

                self.progress.opacity = 0

                self.spinner.opacity = 0

                self.worker = None

                self.set_status(
                    "SAVED "
                    + str(saved)
                    + " FILE(S)"
                )

                if errors:

                    self.show_message(
                        "Save finished with errors",
                        "Saved: "
                        + str(saved)
                        + "\n\n"
                        + "\n".join(errors[:10])
                    )

                else:

                    self.show_message(
                        "SAVE COMPLETE",
                        "Saved "
                        + str(saved)
                        + " crop(s).\n\n"
                        "Location:\n"
                        + directory
                    )

            elif kind == "restore_finished":

                _, results, action = message

                self.crops = results

                self.processing = False

                self.progress.opacity = 0

                self.spinner.opacity = 0

                self.worker = None

                if self.crops:

                    if self.preview_index >= len(
                        self.crops
                    ):

                        self.preview_index = 0

                    self.show_crop()

                    if action == "save":

                        self.start_saving(
                            resume=True
                        )

                    else:

                        self.set_status(
                            "RESTORED "
                            + str(len(self.crops))
                            + " CROPS - TAP SAVE"
                        )

                else:

                    self.set_status(
                        "NOTHING TO RESTORE"
                    )

            elif kind == "fatal":

                _, error = message

                self.processing = False

                self.progress.opacity = 0

                self.spinner.opacity = 0

                self.worker = None

                self.set_status(
                    "ERROR - CHECK LOG"
                )

                self.show_message(
                    "IMAGE SIZER ERROR",
                    str(error)
                    + "\n\nLOG:\n"
                    + str(LOG_FILE)
                )

    # ============================================================
    # SPINNER
    # ============================================================

    def animate_spinner(
        self,
        *args
    ):

        if not self.processing:

            return

        frames = [
            "WORKING.",
            "WORKING..",
            "WORKING..."
        ]

        self.spinner_index += 1

        self.spinner.text = frames[
            self.spinner_index %
            len(frames)
        ]

    # ============================================================
    # SHOW CROP
    # ============================================================

    def show_crop(self):

        if not self.crops:

            self.preview.texture = None

            return

        if self.preview_index >= len(
            self.crops
        ):

            self.preview_index = 0

        image, filename = self.crops[
            self.preview_index
        ]

        try:

            self.preview.texture = (
                pillow_to_texture(image)
            )

            self.set_status(
                filename
                + "   "
                + str(image.width)
                + " × "
                + str(image.height)
                + "   ["
                + str(self.preview_index + 1)
                + "/"
                + str(len(self.crops))
                + "]"
            )

        except Exception:

            write_log(
                "PREVIEW ERROR\n"
                + traceback.format_exc()
            )

    # ============================================================
    # PREVIOUS
    # ============================================================

    def previous_crop(
        self,
        *args
    ):

        if self.processing:
            return

        if not self.crops:
            return

        self.preview_index -= 1

        if self.preview_index < 0:

            self.preview_index = (
                len(self.crops) - 1
            )

        self.show_crop()

        self.snapshot_state()

    # ============================================================
    # NEXT
    # ============================================================

    def next_crop(
        self,
        *args
    ):

        if self.processing:
            return

        if not self.crops:
            return

        self.preview_index += 1

        if self.preview_index >= len(
            self.crops
        ):

            self.preview_index = 0

        self.show_crop()

        self.snapshot_state()

    # ============================================================
    # MESSAGE POPUP
    # ============================================================

    def show_message(
        self,
        title,
        message,
        auto_close=False
    ):

        def create_popup(dt):

            try:

                box = BoxLayout(
                    orientation="vertical",
                    padding=dp(12),
                    spacing=dp(10)
                )

                label = Label(
                    text=str(message),
                    color=TEXT,
                    font_size=sp(15),
                    halign="center",
                    valign="middle"
                )

                label.bind(
                    size=lambda instance, value:
                    setattr(
                        instance,
                        "text_size",
                        value
                    )
                )

                close = AppButton(
                    text="OK",
                    primary=True,
                    size_hint_y=None,
                    height=dp(50)
                )

                box.add_widget(label)
                box.add_widget(close)

                popup = Popup(
                    title=str(title),
                    content=box,
                    size_hint=(
                        0.70,
                        0.50
                    ),
                    auto_dismiss=True
                )

                close.bind(
                    on_release=popup.dismiss
                )

                popup.open()

                if auto_close:

                    Clock.schedule_once(
                        lambda dt:
                        popup.dismiss(),
                        1.6
                    )

            except Exception:

                write_log(
                    "POPUP ERROR\n"
                    + traceback.format_exc()
                )

        Clock.schedule_once(
            create_popup,
            0
        )

    # ============================================================
    # ANDROID
    # ============================================================

    def on_pause(self):

        write_log(
            "APP PAUSED"
        )

        self.snapshot_state()

        return True

    def on_resume(self):

        write_log(
            "APP RESUMED"
        )

        if self.processing:

            self.set_status(
                "STILL WORKING..."
            )

    def on_stop(self):

        write_log(
            "APP STOPPED"
        )

        self.snapshot_state()


# ================================================================
# MAIN
# ================================================================

def main():

    print("")
    print("========================================")
    print("IMAGE SIZER v5")
    print("FORCED LANDSCAPE")
    print("CROPPING + OPTIONAL SCALING")
    print("========================================")
    print("")
    print("ERROR LOG:")
    print(str(LOG_FILE))
    print("")
    print("SAVED PROGRESS (JSON):")
    print(str(STATE_FILE))
    print("")
    print("========================================")

    write_log(
        "MAIN STARTING"
    )

    try:

        app = ImageSizerApp()

        write_log(
            "APP OBJECT CREATED"
        )

        app.run()

        write_log(
            "APP.RUN RETURNED"
        )

    except Exception:

        error = (
            "APPLICATION CRASH\n\n"
            + traceback.format_exc()
        )

        write_log(error)

        print(error)

        raise


# ================================================================
# START
# ================================================================

if __name__ == "__main__":

    main()