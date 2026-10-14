#!/usr/bin/env python3
"""Small window for building TriFlex variants with cad/build.py.

Usage:
    .venv/bin/python cad/gui.py
"""

from __future__ import annotations

import queue
import re
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
import tomllib
from pathlib import Path
from tkinter import messagebox, ttk

REPO = Path(__file__).resolve().parent.parent
VARIANTS = REPO / "cad" / "variants"
PROFILES = REPO / "cad" / "profiles"
CURA_APP = "Ultimaker-Cura"
NO_COMPARE = "(yok)"

FIELDS = [
    # key, label, default, minimum, maximum, step, V30/V31 value
    ("arm.diameter_mm", "Kol çapı (mm)", 3.29, 2.0, 4.0, 0.05, "3.29"),
    ("arm.taper_mm", "Kök/boyun geçiş uzunluğu (mm)", 2.5, 0.5, 6.0, 0.5, "2.5"),
    ("membrane.thickness_mm", "Membran kalınlığı (mm)", 1.30, 0.8, 2.0, 0.05, "1.30"),
]


def revision_number(name: str) -> int:
    match = re.fullmatch(r"v(\d+)", name)
    return int(match.group(1)) if match else -1


def revisions() -> list[str]:
    names = {p.stem for p in PROFILES.glob("*.json")}
    names |= {p.name.removeprefix("triflex-").removesuffix("-experimental.stl")
              for p in (REPO / "models" / "experimental").glob("triflex-*-experimental.stl")}
    names |= {p.stem.removeprefix("triflex-") for p in (REPO / "models" / "stable").glob("triflex-*.stl")}
    return sorted(names, key=lambda n: (revision_number(n), n))


def next_name() -> str:
    return f"v{max(revision_number(n) for n in revisions()) + 1}"


def latest_variant() -> dict:
    files = sorted(VARIANTS.glob("*.toml"), key=lambda p: (revision_number(p.stem), p.stem))
    if not files:
        return {}
    with open(files[-1], "rb") as handle:
        return tomllib.load(handle)


def to_toml(name: str, base: str, compare_with: str, values: dict) -> str:
    lines = [f'name = "{name}"', f'base = "{base}"']
    if compare_with != NO_COMPARE:
        lines.append(f'compare_with = "{compare_with}"')
    for section in ("arm", "membrane"):
        lines += ["", f"[{section}]"]
        lines += [f"{key.split('.')[1]} = {value}" for key, value in values.items()
                  if key.startswith(section + ".")]
    return "\n".join(lines) + "\n"


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.output = queue.Queue()
        self.stl_path: Path | None = None
        root.title("TriFlex varyant oluşturucu")
        root.minsize(720, 560)

        form = ttk.Frame(root, padding=12)
        form.pack(fill="x")
        template = latest_variant()
        names = revisions()

        self.name = tk.StringVar(value=next_name())
        self.base = tk.StringVar(value=template.get("base", "v31"))
        self.compare = tk.StringVar(value=template.get("compare_with", NO_COMPARE))
        ttk.Label(form, text="Ad").grid(row=0, column=0, sticky="w", pady=3)
        ttk.Entry(form, textvariable=self.name, width=12).grid(row=0, column=1, sticky="w")
        ttk.Label(form, text="Başlangıç profili").grid(row=1, column=0, sticky="w", pady=3)
        ttk.Combobox(form, textvariable=self.base, state="readonly", width=10,
                     values=[p.stem for p in sorted(PROFILES.glob("*.json"))]).grid(row=1, column=1, sticky="w")
        ttk.Label(form, text="Karşılaştır").grid(row=2, column=0, sticky="w", pady=3)
        ttk.Combobox(form, textvariable=self.compare, state="readonly", width=10,
                     values=[NO_COMPARE, *names]).grid(row=2, column=1, sticky="w")

        self.values = {}
        for row, (key, label, default, low, high, step, reference) in enumerate(FIELDS, start=3):
            section, field = key.split(".")
            value = template.get(section, {}).get(field, default)
            variable = tk.StringVar(value=f"{value:.2f}")
            self.values[key] = (variable, low, high)
            ttk.Label(form, text=label).grid(row=row, column=0, sticky="w", pady=3)
            ttk.Spinbox(form, textvariable=variable, from_=low, to=high, increment=step,
                        format="%.2f", width=8).grid(row=row, column=1, sticky="w")
            ttk.Label(form, text=f"V30/V31: {reference}   aralık {low}–{high}",
                      foreground="gray").grid(row=row, column=2, sticky="w", padx=10)
        ttk.Label(form, foreground="gray", text=(
            "Taban, kök kavisleri, boyun ve tepe diski her zaman V30'dan alınır. "
            "Her varyantta tek değer değiştirin."), wraplength=660).grid(
            row=len(FIELDS) + 3, column=0, columnspan=3, sticky="w", pady=(8, 0))

        buttons = ttk.Frame(root, padding=(12, 0))
        buttons.pack(fill="x")
        self.build_button = ttk.Button(buttons, text="Oluştur", command=self.build)
        self.build_button.pack(side="left")
        self.cura_button = ttk.Button(buttons, text="Cura'da aç", state="disabled",
                                      command=lambda: self.open_file(["-a", CURA_APP]))
        self.cura_button.pack(side="left", padx=6)
        self.finder_button = ttk.Button(buttons, text="Finder'da göster", state="disabled",
                                        command=lambda: self.open_file(["-R"]))
        self.finder_button.pack(side="left")
        self.status = ttk.Label(buttons, text="")
        self.status.pack(side="left", padx=12)

        self.log = tk.Text(root, height=20, font=("Menlo", 11), wrap="word")
        self.log.pack(fill="both", expand=True, padx=12, pady=12)
        root.after(100, self.poll)

    def read_values(self) -> dict | None:
        result = {}
        for key, (variable, low, high) in self.values.items():
            try:
                value = round(float(variable.get().replace(",", ".")), 3)
            except ValueError:
                messagebox.showerror("Geçersiz değer", f"{key}: sayı girin")
                return None
            if not low <= value <= high:
                messagebox.showerror("Geçersiz değer", f"{key} = {value}, aralık {low}–{high}")
                return None
            result[key] = value
        return result

    def build(self, force: bool = False):
        values = self.read_values()
        name = self.name.get().strip()
        if values is None:
            return
        self.toml = to_toml(name, self.base.get(), self.compare.get(), values)
        handle = tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False)
        handle.write(self.toml)
        handle.close()
        self.variant_name = name
        self.log.delete("1.0", "end")
        self.set_running(True)
        command = [sys.executable, "-u", str(REPO / "cad" / "build.py"), handle.name]
        if force:
            command.append("--force")
        threading.Thread(target=self.run, args=(command, handle.name), daemon=True).start()

    def run(self, command: list[str], toml_path: str):
        process = subprocess.Popen(command, cwd=REPO, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            self.output.put(("line", line))
        process.wait()
        Path(toml_path).unlink(missing_ok=True)
        self.output.put(("done", process.returncode))

    def poll(self):
        while not self.output.empty():
            kind, payload = self.output.get()
            if kind == "line":
                self.log.insert("end", payload)
                self.log.see("end")
            else:
                self.finish(payload)
        self.root.after(100, self.poll)

    def finish(self, code: int):
        self.set_running(False)
        log = self.log.get("1.0", "end")
        if code == 0:
            (VARIANTS / f"{self.variant_name}.toml").write_text(self.toml)
            self.stl_path = REPO / "models" / "experimental" / f"triflex-{self.variant_name}-experimental.stl"
            self.status.config(text=f"Hazır: {self.stl_path.name}", foreground="green")
            self.cura_button.config(state="normal")
            self.finder_button.config(state="normal")
        elif "already exists with different content" in log and "--force" in log:
            self.status.config(text="Bu ad zaten kullanılıyor", foreground="red")
            if messagebox.askyesno(
                    "Ad zaten kullanılıyor",
                    f"{self.variant_name} farklı değerlerle zaten var.\n\n"
                    "Bu revizyon basıldıysa HAYIR deyin ve yeni bir ad verin.\n"
                    "Basılmadıysa üzerine yazılsın mı?", default="no", icon="warning"):
                self.build(force=True)
        else:
            self.status.config(text="Hata, kayda bakın", foreground="red")

    def set_running(self, running: bool):
        self.build_button.config(state="disabled" if running else "normal")
        if running:
            self.status.config(text="Oluşturuluyor… (~30 sn)", foreground="black")
            self.cura_button.config(state="disabled")
            self.finder_button.config(state="disabled")

    def open_file(self, options: list[str]):
        if self.stl_path:
            subprocess.Popen(["open", *options, str(self.stl_path)])


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
