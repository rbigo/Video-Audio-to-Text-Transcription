from __future__ import annotations

import os
import queue
import subprocess
import sys
import threading
from pathlib import Path
from tkinter import DISABLED, END, NORMAL, Button, Checkbutton, Entry, Label, StringVar, Text, Tk, filedialog, ttk

from .config import DEFAULT_COMPUTE_TYPE, DEFAULT_DEVICE, DEFAULT_FASTER_WHISPER_MODEL, DEFAULT_LANGUAGE, apply_local_environment
from .paths import AUDIO_DIR, ROOT, TRANSCRIPTS_DIR, ensure_dirs


class BiliWhisperGui:
    def __init__(self) -> None:
        ensure_dirs()
        apply_local_environment()
        self.root = Tk()
        self.root.title("Bili Whisper")
        self.root.geometry("920x640")
        self.queue: queue.Queue[str | tuple[str, int]] = queue.Queue()
        self.process: subprocess.Popen[str] | None = None

        self.input_var = StringVar()
        self.mode_var = StringVar(value="all")
        self.engine_var = StringVar(value="faster-whisper")
        self.model_var = StringVar(value=DEFAULT_FASTER_WHISPER_MODEL)
        self.device_var = StringVar(value=DEFAULT_DEVICE)
        self.compute_var = StringVar(value=DEFAULT_COMPUTE_TYPE)
        self.language_var = StringVar(value=DEFAULT_LANGUAGE)
        self.status_var = StringVar(value="Ready")

        self._build()
        self.root.after(100, self._drain_queue)

    def run(self) -> None:
        self.root.mainloop()

    def _build(self) -> None:
        pad = {"padx": 8, "pady": 5}
        Label(self.root, text="URL or local media file").grid(row=0, column=0, sticky="w", **pad)
        Entry(self.root, textvariable=self.input_var).grid(row=0, column=1, columnspan=5, sticky="ew", **pad)
        Button(self.root, text="Browse", command=self._browse).grid(row=0, column=6, sticky="ew", **pad)

        Label(self.root, text="Mode").grid(row=1, column=0, sticky="w", **pad)
        ttk.Combobox(
            self.root,
            textvariable=self.mode_var,
            values=[
                "all",
                "transcribe",
                "transcribe-playlist",
                "list-playlist",
                "compare",
                "extract-audio",
                "download-audio",
                "list-subs",
            ],
            state="readonly",
        ).grid(row=1, column=1, sticky="ew", **pad)

        Label(self.root, text="Engine").grid(row=1, column=2, sticky="w", **pad)
        ttk.Combobox(self.root, textvariable=self.engine_var, values=["faster-whisper", "funasr"], state="readonly").grid(row=1, column=3, sticky="ew", **pad)

        Label(self.root, text="Model").grid(row=1, column=4, sticky="w", **pad)
        Entry(self.root, textvariable=self.model_var).grid(row=1, column=5, columnspan=2, sticky="ew", **pad)

        Label(self.root, text="Device").grid(row=2, column=0, sticky="w", **pad)
        ttk.Combobox(self.root, textvariable=self.device_var, values=["cuda", "cpu"], state="readonly").grid(row=2, column=1, sticky="ew", **pad)

        Label(self.root, text="Compute").grid(row=2, column=2, sticky="w", **pad)
        ttk.Combobox(self.root, textvariable=self.compute_var, values=["float16", "int8_float16", "int8"], state="readonly").grid(row=2, column=3, sticky="ew", **pad)

        Label(self.root, text="Language").grid(row=2, column=4, sticky="w", **pad)
        Entry(self.root, textvariable=self.language_var).grid(row=2, column=5, sticky="ew", **pad)

        Button(self.root, text="Run", command=self._start).grid(row=3, column=0, sticky="ew", **pad)
        Button(self.root, text="Stop", command=self._stop).grid(row=3, column=1, sticky="ew", **pad)
        Button(self.root, text="Open Outputs", command=self._open_outputs).grid(row=3, column=2, sticky="ew", **pad)
        Button(self.root, text="Doctor", command=self._doctor).grid(row=3, column=3, sticky="ew", **pad)
        Label(self.root, textvariable=self.status_var).grid(row=3, column=4, columnspan=3, sticky="w", **pad)

        self.log = Text(self.root, wrap="word")
        self.log.grid(row=4, column=0, columnspan=7, sticky="nsew", padx=8, pady=8)

        for col in range(7):
            self.root.columnconfigure(col, weight=1)
        self.root.rowconfigure(4, weight=1)

    def _browse(self) -> None:
        path = filedialog.askopenfilename(
            title="Choose audio or video",
            filetypes=[
                ("Media files", "*.wav *.mp3 *.m4a *.aac *.flac *.ogg *.opus *.mp4 *.mkv *.mov *.avi *.webm"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self.input_var.set(path)

    def _doctor(self) -> None:
        self._run_command(["doctor"])

    def _start(self) -> None:
        value = self.input_var.get().strip()
        if not value:
            self._append("Please enter a URL or choose a local file.\n")
            return
        mode = self.mode_var.get()
        args = [mode, value]
        if mode in {"all", "transcribe", "transcribe-playlist"}:
            args.extend(["--engine", self.engine_var.get()])
            model = self.model_var.get().strip()
            if model:
                args.extend(["--model", model])
            args.extend(["--device", self.device_var.get()])
            args.extend(["--compute-type", self.compute_var.get()])
            args.extend(["--language", self.language_var.get().strip() or DEFAULT_LANGUAGE])
        elif mode == "compare":
            args.extend(["--language", self.language_var.get().strip() or DEFAULT_LANGUAGE])
        self._run_command(args)

    def _run_command(self, args: list[str]) -> None:
        if self.process and self.process.poll() is None:
            self._append("A task is already running.\n")
            return
        self.log.configure(state=NORMAL)
        self.log.delete("1.0", END)
        self.log.configure(state=DISABLED)
        command = [sys.executable, "-m", "bili_whisper", *args]
        self.status_var.set("Running")
        thread = threading.Thread(target=self._worker, args=(command,), daemon=True)
        thread.start()

    def _worker(self, command: list[str]) -> None:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        self.queue.put("> " + subprocess.list2cmdline(command) + "\n\n")
        self.process = subprocess.Popen(
            command,
            cwd=str(ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
        assert self.process.stdout is not None
        for line in self.process.stdout:
            self.queue.put(line)
        code = self.process.wait()
        self.queue.put(("DONE", code))

    def _stop(self) -> None:
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.status_var.set("Stopping")

    def _open_outputs(self) -> None:
        target = AUDIO_DIR if self.mode_var.get() in {"extract-audio", "download-audio"} else TRANSCRIPTS_DIR
        os.startfile(str(target))

    def _drain_queue(self) -> None:
        try:
            while True:
                item = self.queue.get_nowait()
                if isinstance(item, tuple) and item[0] == "DONE":
                    self.status_var.set("Done" if item[1] == 0 else f"Failed ({item[1]})")
                else:
                    self._append(str(item))
        except queue.Empty:
            pass
        self.root.after(100, self._drain_queue)

    def _append(self, text: str) -> None:
        self.log.configure(state=NORMAL)
        self.log.insert(END, text)
        self.log.see(END)
        self.log.configure(state=DISABLED)


def main() -> None:
    BiliWhisperGui().run()
