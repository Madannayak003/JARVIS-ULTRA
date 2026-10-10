import cv2
import threading
import datetime
import os
import subprocess
import wave

import sounddevice as sd

from core.paths import RECORDINGS
from config.settings import get_assistant_display_name

FFMPEG_PATH = r"C:\Users\madan\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0-full_build\bin\ffmpeg.exe"

class CameraManager:

    def __init__(self):

        self.camera = None
        self.index = 0

        self.preview = False
        self.thread = None

        self.current_frame = None

        # * Video recording
        self.recording = False
        self.writer = None

        # * Audio recording
        self.audio_recording = False
        self.audio_thread = None
        self.audio_data = []

        self.audio_sample_rate = 44100
        self.audio_channels = 1

        self.audio_file = None
        self.video_file = None

    # * ---------------------------------------------------------
    # * CAMERA
    # * ---------------------------------------------------------

    def start(self):

        if (
            self.camera is not None
            and self.camera.isOpened()
        ):
            return True

        print("[CAMERA] Starting camera...")

        self.camera = cv2.VideoCapture(
            self.index,
            cv2.CAP_DSHOW
        )

        if not self.camera.isOpened():

            print("[CAMERA] Failed to open camera")

            self.camera.release()
            self.camera = None

            return False

        self.camera.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            1280
        )

        self.camera.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            720
        )

        print("[CAMERA] Camera ready")

        return True

    # * ---------------------------------------------------------

    def frame(self):

        if not self.start():
            return None

        ok, frame = self.camera.read()

        if ok:

            self.current_frame = frame

            return frame

        return None

    # * ---------------------------------------------------------

    def capture_with_countdown(self, seconds=3):

        if not self.start():
            return None

        window = f"{get_assistant_display_name()} Camera"

        frame = None

        for sec in range(seconds, 0, -1):

            start = cv2.getTickCount()

            while True:

                ok, frame = self.camera.read()

                if not ok:
                    continue

                self.current_frame = frame

                display = frame.copy()

                cv2.putText(
                    display,
                    str(sec),
                    (
                        display.shape[1] // 2 - 40,
                        display.shape[0] // 2
                    ),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    5,
                    (0, 255, 0),
                    8
                )

                cv2.imshow(
                    window,
                    display
                )

                key = cv2.waitKey(1)

                if key == 27:

                    self.stop()

                    return None

                elapsed = (
                    cv2.getTickCount() - start
                ) / cv2.getTickFrequency()

                if elapsed >= 1:
                    break

        # * Flash effect

        if frame is not None:

            flash = frame.copy()

            flash[:] = 255

            cv2.imshow(
                window,
                flash
            )

            cv2.waitKey(120)

        ok, frame = self.camera.read()

        if ok:

            self.current_frame = frame

        return self.current_frame

    # * ---------------------------------------------------------
    # * PREVIEW
    # * ---------------------------------------------------------

    def _preview_loop(self):

        self.preview = True

        print("[CAMERA] Preview thread started.")

        while self.preview:

            if self.camera is None:
                break

            ok, frame = self.camera.read()

            if not ok:
                continue

            self.current_frame = frame

            # * Write video frame while recording
            if self.recording and self.writer:

                self.writer.write(frame)

            cv2.imshow(
                f"{get_assistant_display_name()} Camera",
                frame
            )

            key = cv2.waitKey(1)

            if key == 27:

                self.preview = False

                break

        print(
            "[CAMERA] Preview thread stopped."
        )

    # * ---------------------------------------------------------

    def show(self):

        if (
            self.thread
            and self.thread.is_alive()
        ):
            return True

        if not self.start():
            return False

        self.thread = threading.Thread(
            target=self._preview_loop,
            daemon=True
        )

        self.thread.start()

        return True

    # * ---------------------------------------------------------
    # * RECORDING
    # * ---------------------------------------------------------

    def start_recording(self):

        if self.recording:

            print("[CAMERA] Already recording.")

            return

        # * Make sure camera exists
        if not self.start():

            print(
                "[CAMERA] Camera unavailable."
            )

            return

        # * Start preview automatically
        if not (
            self.thread
            and self.thread.is_alive()
        ):

            self.preview = True

            self.thread = threading.Thread(
                target=self._preview_loop,
                daemon=True
            )

            self.thread.start()

        timestamp = datetime.datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        video_path = (
            RECORDINGS
            / f"Video_{timestamp}_temp.mp4"
        )

        audio_path = (
            RECORDINGS
            / f"Audio_{timestamp}.wav"
        )

        fourcc = cv2.VideoWriter_fourcc(
            *"mp4v"
        )

        width = int(
            self.camera.get(
                cv2.CAP_PROP_FRAME_WIDTH
            )
        )

        height = int(
            self.camera.get(
                cv2.CAP_PROP_FRAME_HEIGHT
            )
        )

        self.writer = cv2.VideoWriter(
            str(video_path),
            fourcc,
            30,
            (width, height)
        )

        if not self.writer.isOpened():

            print(
                "[CAMERA] Video writer failed."
            )

            self.writer.release()
            self.writer = None

            return

        self.video_file = video_path
        self.audio_file = audio_path

        self.audio_data = []

        self.audio_recording = True

        # * -------------------------------------------------
        # * AUDIO THREAD
        # * -------------------------------------------------

        def record_audio():

            try:

                with sd.InputStream(
                    samplerate=self.audio_sample_rate,
                    channels=self.audio_channels,
                    dtype="int16"
                ) as stream:

                    while self.audio_recording:

                        data, overflowed = (
                            stream.read(1024)
                        )

                        self.audio_data.append(
                            data.copy()
                        )

            except Exception as e:

                print(
                    f"[AUDIO ERROR] {e}"
                )

                self.audio_recording = False

        self.audio_thread = threading.Thread(
            target=record_audio,
            daemon=True
        )

        self.audio_thread.start()

        self.recording = True

        print(
            f"[CAMERA] Recording started: "
            f"{video_path}"
        )

        print(
            "[AUDIO] Recording started"
        )

    # * ---------------------------------------------------------

    def stop_recording(self):

        if not self.recording:

            print(
                "[CAMERA] Not recording."
            )

            return

        print(
            "[CAMERA] Stopping recording..."
        )

        # * -------------------------------------------------
        # * STOP RECORDING FLAGS
        # * -------------------------------------------------

        self.recording = False
        self.audio_recording = False

        # * -------------------------------------------------
        # * STOP AUDIO THREAD
        # * -------------------------------------------------

        if (
            self.audio_thread
            and self.audio_thread.is_alive()
        ):

            self.audio_thread.join(
                timeout=3
            )

        # * -------------------------------------------------
        # * SAVE AUDIO
        # * -------------------------------------------------

        try:

            if self.audio_data:

                audio_bytes = b"".join(
                    chunk.tobytes()
                    for chunk in self.audio_data
                )

                with wave.open(
                    str(self.audio_file),
                    "wb"
                ) as wf:

                    wf.setnchannels(
                        self.audio_channels
                    )

                    wf.setsampwidth(2)

                    wf.setframerate(
                        self.audio_sample_rate
                    )

                    wf.writeframes(
                        audio_bytes
                    )

                print(
                    f"[AUDIO] Audio saved: "
                    f"{self.audio_file}"
                )

            else:

                print(
                    "[AUDIO] No audio data captured."
                )

        except Exception as e:

            print(
                f"[AUDIO ERROR] Save failed: {e}"
            )

        # * -------------------------------------------------
        # * STOP VIDEO WRITER
        # * -------------------------------------------------

        if self.writer:

            self.writer.release()

            self.writer = None

            print(
                f"[CAMERA] Video saved: "
                f"{self.video_file}"
            )

        # * -------------------------------------------------
        # * STOP PREVIEW THREAD
        # * -------------------------------------------------

        self.preview = False

        if (
            self.thread
            and self.thread.is_alive()
            and threading.current_thread()
            != self.thread
        ):

            print(
                "[CAMERA] Closing preview window..."
            )

            self.thread.join(
                timeout=3
            )

        self.thread = None

        # * -------------------------------------------------
        # * RELEASE CAMERA
        # * -------------------------------------------------

        if self.camera:

            self.camera.release()

            self.camera = None

        # * -------------------------------------------------
        # * CLOSE OPENCV WINDOW
        # * -------------------------------------------------

        try:

            cv2.destroyAllWindows()
            cv2.waitKey(1)

        except Exception:
            pass

        print(
            "[CAMERA] Camera released."
        )

        # * -------------------------------------------------
        # * CHECK AUDIO
        # * -------------------------------------------------

        if not self.audio_file:

            print(
                "[CAMERA] Audio file missing."
            )

        # * -------------------------------------------------
        # * COMBINE VIDEO + AUDIO
        # * -------------------------------------------------

        final_file = self.video_file.with_name(
            self.video_file.name.replace(
                "_temp",
                ""
            )
        )

        command = [

            FFMPEG_PATH,

            "-y",

            "-i",
            str(self.video_file),

            "-i",
            str(self.audio_file),

            "-c:v",
            "copy",

            "-c:a",
            "aac",

            "-shortest",

            str(final_file)
        ]

        try:

            print(
                "[FFMPEG] Combining video + audio..."
            )

            print(
                f"[FFMPEG] Using: {FFMPEG_PATH}"
            )

            result = subprocess.run(

                command,

                stdout=subprocess.DEVNULL,

                stderr=subprocess.PIPE,

                text=True
            )

            if result.returncode == 0:

                print(
                    "[CAMERA] Final recording saved: "
                    f"{final_file}"
                )

                # * -------------------------------------------------
                # * DELETE TEMP FILES
                # * -------------------------------------------------

                try:

                    if self.video_file.exists():

                        os.remove(
                            self.video_file
                        )

                    if self.audio_file.exists():

                        os.remove(
                            self.audio_file
                        )

                    print(
                        "[CAMERA] Temporary files removed."
                    )

                except Exception as e:

                    print(
                        f"[CLEANUP] {e}"
                    )

            else:

                print(
                    "[FFMPEG ERROR]"
                )

                print(
                    result.stderr
                )

        except Exception as e:

            print(
                f"[FFMPEG ERROR] {e}"
            )

        # * -------------------------------------------------
        # * RESET STATE
        # * -------------------------------------------------

        self.video_file = None
        self.audio_file = None
        self.audio_data = []
        self.audio_thread = None

        self.recording = False
        self.audio_recording = False
        self.preview = False

        print(
            "[CAMERA] Recording finished."
        )

    # * ---------------------------------------------------------
    # * STOP CAMERA
    # * ---------------------------------------------------------

    def stop(self):

        self.preview = False

        if (
            self.thread
            and self.thread.is_alive()
            and threading.current_thread()
            != self.thread
        ):

            self.thread.join(
                timeout=1
            )

        self._cleanup()

    # * ---------------------------------------------------------

    def _cleanup(self):

        self.preview = False

        if self.writer:

            self.writer.release()

            self.writer = None

        if self.camera:

            self.camera.release()

            self.camera = None

        cv2.destroyAllWindows()

    # * ---------------------------------------------------------

    def opened(self):

        return (
            self.camera is not None
            and self.camera.isOpened()
        )

    # * ---------------------------------------------------------

    def switch(self, index):

        self.stop()

        self.index = index

        self.start()


camera = CameraManager()
