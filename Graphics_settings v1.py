"""
Graphics Settings - Elden Ring
Unified editor for ERSS-FG mod and in-game graphics config.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import tomllib
import os
import re
import json
import base64
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET

# ── Config paths ────────────────────────────────────────────────────────
ERSS_TOML_CANDIDATES = [
    r"E:\eldenring\ERSS2\ERSS-FG.toml",
    r"C:\Program Files (x86)\Steam\steamapps\common\ELDEN RING\Game\ERSS2\ERSS-FG.toml",
]
GAME_XML_CANDIDATES = [
    os.path.join(os.environ.get("APPDATA", ""), "EldenRing", "GraphicsConfig.xml"),
]
MEMORY_FILE = os.path.join(os.environ.get("APPDATA", ""), "EldenRingSettingsEditor", "paths.json")

# ── Keys to hide from ERSS UI ───────────────────────────────────────────
HIDDEN_ERSS_KEYS = {
    "ImGuiUseGamepadNav", "DatePopup", "ShowAdvancedSettingsWindow",
    "DateFirstLaunch", "DPIOverride", "PrevDPI",
    "bIsFPSUnlockWarningAccepted", "CPUMask", "ImGuiUseGamepadToggle",
    "OverlayToggleKey",
}

# ── Friendly label overrides ────────────────────────────────────────────
LABEL_OVERRIDES = {
    "IsHDR":                "HDR",
    "ScalingMode":          "Upscaling Mode",
    "LatencyReductionMode": "Latency Reduction",
    "RemoveFPSLimit":       "Remove FPS Limit",
    "MaxFPS":               "Max FPS",
    "HDRGamma":             "HDR Gamma",
    "HDRGammaHUD":          "HDR Gamma (HUD)",
    "HDRBrightness":        "HDR Brightness",
    "HDRSaturation":        "HDR Saturation",
    "HDRBrightnessHUD":     "HUD Brightness",
    "HDRSceneHDRPassthrough":"HDR Passthrough",
    "GammaLevel":           "Gamma Level",
    "OverrideFullscreenState": "Override Fullscreen",
    "OverrideColorSpace":   "Override Color Space",
    "OverrideRefreshRate":  "Override Refresh Rate",
    "Force10Bit":           "Force 10-bit Color",
    "BindDepth":            "Bind Depth Buffer",
    "DLSSPreset":           "DLSS Preset",
    "DLSSMode":             "DLSS Quality",
    "SharpenMode":          "Sharpening Mode",
    "Sharpness":            "Sharpness",
    "LimitFrameRate":       "Limit Frame Rate",
    "NumGenFrames":         "Generated Frames",
    "ReflexMode":           "NVIDIA Reflex",
    "FrameGenMode":         "Frame Gen Mode",
    "GIGlitchMitigation":   "GI Glitch Fix",
    "EnableFrameGen":       "Enable Frame Generation",
    "QualityMode":          "Quality Mode",
    "UseSharpen":           "Use Sharpening",
    # Game XML labels
    "ScreenMode":           "Screen Mode",
    "TextureQuality":       "Texture Quality",
    "Antialiasing":         "Anti-aliasing",
    "SSAO":                 "Ambient Occlusion",
    "DepthOfField":         "Depth of Field",
    "MotionBlur":           "Motion Blur",
    "ShadowQuality":        "Shadow Quality",
    "LightingQuality":      "Lighting Quality",
    "EffectsQuality":       "Effects Quality",
    "ReflectionQuality":    "Reflection Quality",
    "WaterSurfaceQuality":  "Water Quality",
    "ShadeQuality":         "Shade Quality",
    "VolumetricEffectQuality": "Volumetric Effects",
    "RaytracingQuality":    "Ray Tracing Quality",
    "GIDataQuality":        "Global Illumination",
    "GrassQuality":         "Grass Quality",
    "Auto-detectBestRenderingSettings": "Auto-detect Settings",
}

# ── Palette ─────────────────────────────────────────────────────────────
BG_DARK    = "#0e0c09"
BG_MID     = "#1a1710"
BG_PANEL   = "#211f16"
GOLD       = "#c8a84b"
GOLD_LIGHT = "#e8c96a"
GOLD_DIM   = "#7a6328"
RED_ACCENT = "#8b1a1a"
TEXT_MAIN  = "#d4c9a0"
TEXT_DIM   = "#7a7060"
TEXT_BRIGHT= "#f0e6c0"
SEPARATOR  = "#3a3420"
BLUE_INFO  = "#4a7a9b"

FONT_TITLE   = ("Georgia", 16, "bold")
FONT_SECTION = ("Georgia", 11, "bold")
FONT_LABEL   = ("Georgia", 9)
FONT_VALUE   = ("Consolas", 9)
FONT_BUTTON  = ("Georgia", 10, "bold")
FONT_SMALL   = ("Georgia", 8)

# ── Elden Ring icon as base64 PNG (sword & crest minimal icon) ──────────
ER_ICON_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABmJLR0QA/wD/AP+gvaeTAAAA"
    "CXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH6AUSCiUGmbZJVAAAAB1pVFh0Q29tbWVudAAA"
    "AAAAQ3JlYXRlZCB3aXRoIEdJTVBkLmUHAAABvklEQVRYw+2Xv0oDQRDGf3t3IZhKJJWFYCH"
    "4AoKFhYWFD6BPYOcD+AAWFhYWgk9gJ9iJnYWFhYW9kEIwkpBgJHf+7c3OzoS7S3IXuEuKg"
    "YVlh52db2d2dldEhISEhISEfhARAREQEREQEREQEQEREREREREREREREREREREREREREREQEQ"
    "EREREREREREREREREREREREREREREREQEREQEREQEREQEREQEREQEREQEREQEREQEREQEREQEREQ"
    "EREQEREQEREQEREQEREQEREQEREQEREQEREQEREQEREQEREQEREQEREQEREQEREQEREQEREQER"
    "EQEREQEREQEREQEREQEREQEREQEREQEREQEREQEREQEREQEREQEREQEREQEREQEREQEREQEREQ"
    "EREQEREQEREQEREQEREQEREQEREQEREQEREQEREQEREQEREQEREQEREQEREQEREQEREQEREQER"
    "EQEREQEREQEREQEREQEREQEREQEREQEREQEREQEREQEREQEREQEREQEREQEREQEREQEREQEREQ"
    "ERERERERERERExB8AAAD//2QABAABAAEAAf8AAAAAABJRU5ErkJggg=="
)

# ── Memory helpers ───────────────────────────────────────────────────────
def load_memory():
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_memory(data):
    try:
        os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
        with open(MEMORY_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass

def find_file(candidates, memory_key):
    mem = load_memory()
    if memory_key in mem and os.path.exists(mem[memory_key]):
        return mem[memory_key]
    for path in candidates:
        if os.path.exists(path):
            mem[memory_key] = path
            save_memory(mem)
            return path
    return None

# ── TOML helpers ─────────────────────────────────────────────────────────
def load_toml(path):
    with open(path, "rb") as f:
        return tomllib.load(f)

def save_toml(path, data_map):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    current_section = None
    out = []
    for line in lines:
        stripped = line.strip()
        m = re.match(r'^\[([^\]]+)\]', stripped)
        if m:
            current_section = m.group(1)
            out.append(line)
            continue
        kv = re.match(r'^(\w+)\s*=\s*(.+)', stripped)
        if kv:
            key = kv.group(1)
            lookup = (current_section, key) if current_section else (None, key)
            if lookup in data_map:
                out.append(f"{key} = {data_map[lookup]}\n")
                continue
        out.append(line)
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(out)

# ── XML helpers ──────────────────────────────────────────────────────────
def load_xml(path):
    content = Path(path).read_bytes()
    # strip BOM if present
    for enc in ("utf-16", "utf-8-sig", "utf-8"):
        try:
            text = content.decode(enc)
            break
        except Exception:
            continue
    root = ET.fromstring(text.lstrip('\ufeff'))
    result = {}
    for child in root:
        tag = child.tag
        val = child.text or ""
        result[tag] = val
    return result

def save_xml(path, updates):
    content = Path(path).read_bytes()
    for enc in ("utf-16", "utf-8-sig", "utf-8"):
        try:
            text = content.decode(enc)
            break
        except Exception:
            continue
    for key, val in updates.items():
        text = re.sub(
            f'<{re.escape(key)}>[^<]*</{re.escape(key)}>',
            f'<{key}>{val}</{key}>',
            text
        )
    Path(path).write_bytes(text.encode("utf-16"))

# ── Value formatters ──────────────────────────────────────────────────────
def py_to_toml(val):
    if isinstance(val, bool):   return "true" if val else "false"
    if isinstance(val, str):    return f'"{val}"'
    if isinstance(val, float):  return f"{val}"
    if isinstance(val, int):    return f"{val}"
    return str(val)

def friendly_label(key):
    return LABEL_OVERRIDES.get(key, re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', key).replace("_", " "))

# ── Main App ──────────────────────────────────────────────────────────────
class EldenEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Graphics Settings  –  Elden Ring")
        self.configure(bg=BG_DARK)
        self.resizable(True, True)
        self.geometry("860x900")
        self.minsize(760, 600)

        # Dark title bar on Windows
        try:
            self.update()
            HWND = self.winfo_id()
            import ctypes
            dwmapi = ctypes.WinDLL("dwmapi")
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            value = ctypes.c_int(1)
            dwmapi.DwmSetWindowAttribute(HWND, DWMWA_USE_IMMERSIVE_DARK_MODE,
                                          ctypes.byref(value), ctypes.sizeof(value))
        except Exception:
            pass

        # Window icon
        try:
            icon_data = base64.b64decode(ER_ICON_B64)
            import tempfile
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            tmp.write(icon_data)
            tmp.close()
            img = tk.PhotoImage(file=tmp.name)
            self.iconphoto(True, img)
        except Exception:
            pass

        self.vars      = {}   # (section, key) -> tk var or tuple
        self.xml_vars  = {}   # xml_key -> tk var
        self.erss_raw  = {}
        self.xml_raw   = {}
        self.erss_path = None
        self.xml_path  = None
        self._change_pending = False

        self._build_styles()
        self._discover_paths()
        self._auto_accept_fps_warning()
        self._build_ui()

    # ── Path discovery ────────────────────────────────────────────────────
    def _discover_paths(self):
        self.erss_path = find_file(ERSS_TOML_CANDIDATES, "erss_toml")
        self.xml_path  = find_file(GAME_XML_CANDIDATES,  "game_xml")
        if self.erss_path:
            try:
                self.erss_raw = load_toml(self.erss_path)
            except Exception as e:
                messagebox.showerror("Failed to load ERSS config", str(e))
        if self.xml_path:
            try:
                self.xml_raw = load_xml(self.xml_path)
            except Exception as e:
                messagebox.showerror("Failed to load game config", str(e))

    def _auto_accept_fps_warning(self):
        """Silently accept the FPS unlock warning if not already accepted."""
        if not self.erss_path or not self.erss_raw:
            return
        if not self.erss_raw.get("bIsFPSUnlockWarningAccepted", True):
            try:
                save_toml(self.erss_path, {(None, "bIsFPSUnlockWarningAccepted"): "true"})
                self.erss_raw["bIsFPSUnlockWarningAccepted"] = True
            except Exception:
                pass

    # ── Styles ────────────────────────────────────────────────────────────
    def _build_styles(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TFrame",       background=BG_DARK)
        s.configure("Panel.TFrame", background=BG_MID)
        s.configure("Inner.TFrame", background=BG_PANEL)
        s.configure("TLabel",       background=BG_PANEL, foreground=TEXT_MAIN, font=FONT_LABEL)
        s.configure("Title.TLabel", background=BG_DARK,  foreground=GOLD,      font=FONT_TITLE)
        s.configure("Section.TLabel", background=BG_MID, foreground=GOLD_LIGHT, font=FONT_SECTION)
        s.configure("Dim.TLabel",   background=BG_PANEL, foreground=TEXT_DIM,  font=FONT_SMALL)

        s.configure("TCheckbutton",
                    background=BG_PANEL, foreground=TEXT_MAIN,
                    font=FONT_LABEL, selectcolor=GOLD_DIM,
                    indicatorcolor=GOLD_DIM, indicatorrelief="flat")
        s.map("TCheckbutton",
              foreground=[("active", GOLD_LIGHT)],
              background=[("active", BG_PANEL)])

        s.configure("TCombobox",
                    fieldbackground=BG_PANEL, background=GOLD_DIM,
                    foreground=TEXT_BRIGHT, font=FONT_VALUE,
                    selectbackground=GOLD_DIM, selectforeground=TEXT_BRIGHT,
                    arrowcolor=GOLD)
        s.map("TCombobox",
              fieldbackground=[("readonly", BG_PANEL)],
              foreground=[("readonly", TEXT_BRIGHT)])

        # Buttons use tk.Button (not ttk) to avoid theme rendering issues on Windows
        s.configure("TScrollbar",
                    background=BG_MID, troughcolor=BG_DARK,
                    arrowcolor=GOLD_DIM, borderwidth=0)

    def _make_button(self, parent, text, command, color=GOLD_DIM, hover=GOLD, side="right", padx=(8,0)):
        """Native tk.Button to avoid ttk black-box rendering bug on Windows."""
        btn = tk.Button(
            parent, text=text, command=command,
            bg=color, fg=TEXT_BRIGHT, activebackground=hover,
            activeforeground=BG_DARK, font=FONT_BUTTON,
            relief="flat", bd=0, padx=16, pady=7,
            cursor="hand2"
        )
        btn.pack(side=side, padx=padx)
        return btn

    # ── UI ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=BG_DARK, pady=10)
        hdr.pack(fill="x", padx=20, pady=(16, 0))

        tk.Label(hdr, text="⚔", font=("Georgia", 20), bg=BG_DARK, fg=GOLD).pack(side="left", padx=(0, 10))
        title_block = tk.Frame(hdr, bg=BG_DARK)
        title_block.pack(side="left")
        tk.Label(title_block, text="Graphics Settings",
                 font=FONT_TITLE, bg=BG_DARK, fg=GOLD).pack(anchor="w")

        # Adaptive path display
        paths = []
        if self.erss_path:
            paths.append(f"ERSS: {self.erss_path}")
        if self.xml_path:
            paths.append(f"Game: {self.xml_path}")
        path_text = "  |  ".join(paths) if paths else "No config files found"
        tk.Label(title_block, text=path_text,
                 font=FONT_SMALL, bg=BG_DARK, fg=TEXT_DIM).pack(anchor="w")

        tk.Frame(self, bg=GOLD_DIM, height=1).pack(fill="x", padx=20, pady=(10, 0))

        # Tabs
        nb_frame = tk.Frame(self, bg=BG_DARK)
        nb_frame.pack(fill="x", padx=20, pady=(8, 0))

        self.active_tab = tk.StringVar(value="game")
        self._tab_buttons = {}
        tabs = []
        if self.xml_path:
            tabs.append(("game", "🎮  Game Settings"))
        if self.erss_path:
            tabs.append(("erss", "⚙  ERSS-FG Mod"))

        for tab_id, tab_label in tabs:
            btn = tk.Button(
                nb_frame, text=tab_label,
                bg=GOLD_DIM, fg=TEXT_BRIGHT,
                activebackground=GOLD, activeforeground=BG_DARK,
                font=FONT_BUTTON, relief="flat", bd=0,
                padx=18, pady=6, cursor="hand2",
                command=lambda t=tab_id: self._switch_tab(t)
            )
            btn.pack(side="left", padx=(0, 4))
            self._tab_buttons[tab_id] = btn

        if not tabs:
            tk.Label(nb_frame, text="No configuration files found.",
                     font=FONT_LABEL, bg=BG_DARK, fg=RED_ACCENT).pack(side="left")

        tk.Frame(self, bg=GOLD_DIM, height=1).pack(fill="x", padx=20, pady=(6, 0))

        # Scrollable body
        outer = tk.Frame(self, bg=BG_DARK)
        outer.pack(fill="both", expand=True, padx=20, pady=10)

        self.canvas = tk.Canvas(outer, bg=BG_DARK, highlightthickness=0, bd=0)
        scroll = ttk.Scrollbar(outer, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.body = tk.Frame(self.canvas, bg=BG_DARK)
        win_id = self.canvas.create_window((0, 0), window=self.body, anchor="nw")

        def _on_resize(e):
            self.canvas.itemconfig(win_id, width=e.width)
        self.canvas.bind("<Configure>", _on_resize)

        def _on_frame_configure(e):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.body.bind("<Configure>", _on_frame_configure)

        self.canvas.bind_all("<MouseWheel>",
                             lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        # Footer
        tk.Frame(self, bg=GOLD_DIM, height=1).pack(fill="x", padx=20)
        foot = tk.Frame(self, bg=BG_DARK, pady=12)
        foot.pack(fill="x", padx=20)

        self.status = tk.StringVar(value="Ready.")
        tk.Label(foot, textvariable=self.status,
                 font=FONT_SMALL, bg=BG_DARK, fg=TEXT_DIM).pack(side="left")

        self._make_button(foot, "⟳  Reload", self._reload, color=RED_ACCENT, hover="#b02222")
        self._make_button(foot, "✦  Save Settings", self._save, color=GOLD_DIM, hover=GOLD)

        # Initial tab
        if tabs:
            self._switch_tab(tabs[0][0])

    def _switch_tab(self, tab_id):
        self.active_tab.set(tab_id)
        for tid, btn in self._tab_buttons.items():
            btn.config(bg=GOLD if tid == tab_id else GOLD_DIM,
                       fg=BG_DARK if tid == tab_id else TEXT_BRIGHT)
        for w in self.body.winfo_children():
            w.destroy()
        self.vars.clear()
        self.xml_vars.clear()
        if tab_id == "erss":
            self._render_erss()
        elif tab_id == "game":
            self._render_game()
        self.canvas.yview_moveto(0)

    # ── ERSS Renderer ─────────────────────────────────────────────────────
    def _render_erss(self):
        d = self.erss_raw
        top_keys = {k: v for k, v in d.items()
                    if not isinstance(v, dict) and k not in HIDDEN_ERSS_KEYS}
        if top_keys:
            self._make_section("General", None, top_keys, "erss")

        section_meta = {
            "Renderer":        "🖥   Renderer",
            "SwapChain":       "⛓   Swap Chain",
            "DLSS":            "✦   DLSS Upscaling",
            "DLSS-G":          "✦✦  DLSS Frame Generation",
            "FrameGeneration": "🎞   Frame Generation",
            "FSR3U":           "◈   FSR 3 Upscaler",
            "XESS":            "◇   Intel XeSS",
            "NIS":             "◈   NIS Sharpener",
            "ReShade":         "🎨  ReShade",
            "Reflex":          "⚡  NVIDIA Reflex",
        }
        for key, label in section_meta.items():
            if key in d and isinstance(d[key], dict):
                self._make_section(label, key, d[key], "erss")

    # ── Game XML Renderer ─────────────────────────────────────────────────
    def _render_game(self):
        if not self.xml_raw:
            tk.Label(self.body, text="Game config not found.",
                     font=FONT_LABEL, bg=BG_DARK, fg=RED_ACCENT).pack(pady=20)
            return

        # Group game settings
        screen_keys    = ["ScreenMode"]
        resolution_keys= [k for k in self.xml_raw if "Width" in k or "Height" in k]
        quality_keys   = [k for k in self.xml_raw
                          if k not in screen_keys + resolution_keys
                          and k not in ("Auto-detectBestRenderingSettings", "QualitySetting")]
        misc_keys      = ["Auto-detectBestRenderingSettings"]

        self._make_xml_section("🖥   Display", screen_keys)
        self._make_xml_section("📐  Resolution", resolution_keys)
        self._make_xml_section("🎨  Quality Settings", quality_keys)
        self._make_xml_section("⚙   Misc", misc_keys)

    def _make_xml_section(self, title, keys):
        keys = [k for k in keys if k in self.xml_raw]
        if not keys:
            return
        wrap = tk.Frame(self.body, bg=BG_MID,
                        highlightbackground=GOLD_DIM, highlightthickness=1)
        wrap.pack(fill="x", pady=(0, 10))
        hdr = tk.Frame(wrap, bg=BG_MID, pady=6)
        hdr.pack(fill="x", padx=12)
        tk.Label(hdr, text=title, font=FONT_SECTION, bg=BG_MID, fg=GOLD_LIGHT).pack(side="left")
        tk.Frame(hdr, bg=GOLD_DIM, height=1).pack(side="left", fill="x", expand=True, padx=(10, 0), pady=6)
        inner = tk.Frame(wrap, bg=BG_PANEL, padx=14, pady=10)
        inner.pack(fill="x", padx=8, pady=(0, 8))
        inner.columnconfigure(1, weight=1)
        for row, key in enumerate(keys):
            self._make_xml_row(inner, row, key, self.xml_raw[key])

    def _make_xml_row(self, parent, row, key, val):
        label = friendly_label(key)
        tk.Label(parent, text=label, font=FONT_LABEL, bg=BG_PANEL, fg=TEXT_MAIN,
                 anchor="w", width=24).grid(row=row, column=0, sticky="w", pady=3, padx=(0, 12))

        xml_options = {
            "ScreenMode":    ["FULLSCREEN", "BORDERLESS", "WINDOWED"],
            "TextureQuality": ["LOW", "MEDIUM", "HIGH", "MAX"],
            "Antialiasing":   ["LOW", "MEDIUM", "HIGH"],
            "SSAO":           ["LOW", "MEDIUM", "HIGH", "MAX"],
            "DepthOfField":   ["LOW", "MEDIUM", "HIGH", "MAX"],
            "MotionBlur":     ["DISABLE", "LOW", "MEDIUM", "HIGH"],
            "ShadowQuality":  ["LOW", "MEDIUM", "HIGH", "MAX"],
            "LightingQuality":["LOW", "MEDIUM", "HIGH", "MAX"],
            "EffectsQuality": ["LOW", "MEDIUM", "HIGH", "MAX"],
            "ReflectionQuality": ["LOW", "MEDIUM", "HIGH", "MAX"],
            "WaterSurfaceQuality": ["LOW", "MEDIUM", "HIGH"],
            "ShadeQuality":   ["LOW", "MEDIUM", "HIGH"],
            "VolumetricEffectQuality": ["LOW", "MEDIUM", "HIGH", "MAX"],
            "RaytracingQuality": ["LOW", "MEDIUM", "HIGH", "MAX"],
            "GIDataQuality":  ["LOW", "MEDIUM", "HIGH"],
            "GrassQuality":   ["LOW", "MEDIUM", "HIGH", "MAX"],
            "Auto-detectBestRenderingSettings": ["ON", "OFF"],
        }

        if key in xml_options:
            var = tk.StringVar(value=val)
            self.xml_vars[key] = var
            combo = ttk.Combobox(parent, textvariable=var,
                                 values=xml_options[key],
                                 state="readonly", width=20, font=FONT_VALUE)
            combo.grid(row=row, column=1, sticky="w", pady=3)
            combo.bind("<<ComboboxSelected>>", lambda e: self._mark_changed())
        elif val.lstrip('-').isdigit():
            var = tk.StringVar(value=val)
            self.xml_vars[key] = var
            ent = tk.Entry(parent, textvariable=var, width=12,
                           bg=BG_DARK, fg=TEXT_BRIGHT, insertbackground=GOLD,
                           relief="flat", font=FONT_VALUE,
                           highlightbackground=GOLD_DIM, highlightthickness=1)
            ent.grid(row=row, column=1, sticky="w", pady=3)
            var.trace_add("write", lambda *a: self._mark_changed())
        else:
            var = tk.StringVar(value=val)
            self.xml_vars[key] = var
            tk.Label(parent, textvariable=var, font=FONT_VALUE,
                     bg=BG_PANEL, fg=TEXT_DIM, anchor="w").grid(row=row, column=1, sticky="w", pady=3)

    # ── ERSS Section builder ──────────────────────────────────────────────
    def _make_section(self, title, section_key, data, source):
        filtered = {k: v for k, v in data.items() if k not in HIDDEN_ERSS_KEYS}
        if not filtered:
            return
        wrap = tk.Frame(self.body, bg=BG_MID,
                        highlightbackground=GOLD_DIM, highlightthickness=1)
        wrap.pack(fill="x", pady=(0, 10))
        hdr = tk.Frame(wrap, bg=BG_MID, pady=6)
        hdr.pack(fill="x", padx=12)
        tk.Label(hdr, text=title, font=FONT_SECTION, bg=BG_MID, fg=GOLD_LIGHT).pack(side="left")
        tk.Frame(hdr, bg=GOLD_DIM, height=1).pack(side="left", fill="x", expand=True, padx=(10, 0), pady=6)
        inner = tk.Frame(wrap, bg=BG_PANEL, padx=14, pady=10)
        inner.pack(fill="x", padx=8, pady=(0, 8))
        inner.columnconfigure(1, weight=1)
        for row, (key, val) in enumerate(filtered.items()):
            self._make_row(inner, row, section_key, key, val)

    def _make_row(self, parent, row, section, key, val):
        lookup = (section, key)
        label = friendly_label(key)
        tk.Label(parent, text=label, font=FONT_LABEL, bg=BG_PANEL, fg=TEXT_MAIN,
                 anchor="w", width=24).grid(row=row, column=0, sticky="w", pady=3, padx=(0, 12))

        if isinstance(val, bool):
            var = tk.BooleanVar(value=val)
            self.vars[lookup] = var
            cb = ttk.Checkbutton(parent, variable=var, style="TCheckbutton",
                                 onvalue=True, offvalue=False,
                                 command=self._mark_changed)
            cb.grid(row=row, column=1, sticky="w", pady=3)

        elif isinstance(val, int) and self._known_options(section, key):
            opts, labels = self._known_options(section, key)
            var = tk.StringVar(value=labels.get(val, str(val)))
            self.vars[lookup] = (var, opts, labels)
            combo = ttk.Combobox(parent, textvariable=var,
                                 values=list(labels.values()),
                                 state="readonly", width=28, font=FONT_VALUE)
            combo.grid(row=row, column=1, sticky="w", pady=3)
            combo.bind("<<ComboboxSelected>>", lambda e: self._mark_changed())

        elif isinstance(val, float):
            frame = tk.Frame(parent, bg=BG_PANEL)
            frame.grid(row=row, column=1, sticky="ew", pady=3)
            lo, hi, step = self._float_range(section, key)
            var = tk.DoubleVar(value=val)
            self.vars[lookup] = var
            entry = tk.Entry(frame, textvariable=var, width=7,
                             bg=BG_DARK, fg=TEXT_BRIGHT, insertbackground=GOLD,
                             relief="flat", font=FONT_VALUE,
                             highlightbackground=GOLD_DIM, highlightthickness=1)
            entry.pack(side="left", padx=(0, 8))
            sl = tk.Scale(frame, from_=lo, to=hi, resolution=step,
                          orient="horizontal", variable=var,
                          bg=BG_PANEL, fg=TEXT_DIM, troughcolor=BG_DARK,
                          activebackground=GOLD, highlightthickness=0,
                          sliderrelief="flat", showvalue=False, length=180, bd=0)
            sl.pack(side="left")
            var.trace_add("write", lambda *a: self._mark_changed())

        elif isinstance(val, str) and not val.startswith("20"):
            var = tk.StringVar(value=val)
            self.vars[lookup] = var
            opts = self._string_options(section, key)
            if opts:
                combo = ttk.Combobox(parent, textvariable=var, values=opts,
                                     state="readonly", width=28, font=FONT_VALUE)
                combo.grid(row=row, column=1, sticky="w", pady=3)
                combo.bind("<<ComboboxSelected>>", lambda e: self._mark_changed())
            else:
                ent = tk.Entry(parent, textvariable=var, width=30,
                               bg=BG_DARK, fg=TEXT_BRIGHT, insertbackground=GOLD,
                               relief="flat", font=FONT_VALUE,
                               highlightbackground=GOLD_DIM, highlightthickness=1)
                ent.grid(row=row, column=1, sticky="w", pady=3)
                var.trace_add("write", lambda *a: self._mark_changed())

        elif isinstance(val, int):
            var = tk.IntVar(value=val)
            self.vars[lookup] = var
            ent = tk.Entry(parent, textvariable=var, width=10,
                           bg=BG_DARK, fg=TEXT_BRIGHT, insertbackground=GOLD,
                           relief="flat", font=FONT_VALUE,
                           highlightbackground=GOLD_DIM, highlightthickness=1)
            ent.grid(row=row, column=1, sticky="w", pady=3)
            var.trace_add("write", lambda *a: self._mark_changed())
        else:
            tk.Label(parent, text=str(val), font=FONT_VALUE,
                     bg=BG_PANEL, fg=TEXT_DIM, anchor="w").grid(row=row, column=1, sticky="w", pady=3)

    def _mark_changed(self):
        if not self._change_pending:
            self._change_pending = True
            self.status.set("⚠  Unsaved changes — click Save Settings to apply.")

    # ── Option maps ───────────────────────────────────────────────────────
    def _known_options(self, section, key):
        maps = {
            ("Renderer","LatencyReductionMode"): {0:"Off", 1:"Enabled", 2:"Boost"},
            ("Renderer","GammaLevel"):           {0:"0",1:"1",2:"2",3:"3",4:"4",5:"5",6:"6"},
            ("DLSS","DLSSMode"):                 {0:"Off",1:"Max Performance",2:"Performance",3:"Balanced",4:"Quality",5:"Ultra Quality",6:"DLAA"},
            ("DLSS","DLSSPreset"):               {0:"Default",1:"A",2:"B",3:"C",4:"D",5:"E",6:"F",7:"G"},
            ("DLSS","SharpenMode"):              {0:"Off",1:"Sharpening"},
            ("DLSS-G","NumGenFrames"):           {1:"1",2:"2",3:"3",4:"4"},
            ("FrameGeneration","FrameGenMode"):  {0:"Off",1:"DLSS-G",2:"Auto"},
            ("FrameGeneration","GIGlitchMitigation"): {0:"Off",1:"On"},
            ("FSR3U","QualityMode"):             {0:"Native AA",1:"Quality",2:"Balanced",3:"Performance",4:"Ultra Performance"},
            ("XESS","QualityMode"):              {100:"Ultra Performance",101:"Performance",102:"Balanced",103:"Quality",104:"Ultra Quality",105:"Ultra Quality+",106:"Native AA"},
            ("XESS","SharpenMode"):              {0:"Off",1:"Sharpening"},
            ("NIS","ScalingMode"):               {0:"Off",1:"NIS"},
            ("Reflex","ReflexMode"):             {0:"Off",1:"Enabled",2:"Boost"},
        }
        d = maps.get((section, key))
        return (d, d) if d else None

    def _float_range(self, section, key):
        ranges = {
            ("Renderer","MaxFPS"):         (0.0,  360.0, 1.0),
            ("Renderer","HDRGammaHUD"):    (0.1,  3.0,   0.01),
            ("Renderer","HDRBrightness"):  (100,  1000,  10),
            ("Renderer","HDRGamma"):       (0.5,  3.0,   0.05),
            ("Renderer","HDRSaturation"):  (0.0,  2.0,   0.05),
            ("Renderer","HDRBrightnessHUD"): (0.1, 2.0,  0.01),
            ("DLSS","Sharpness"):          (0.0,  1.0,   0.05),
            ("FSR3U","Sharpness"):         (0.0,  1.0,   0.05),
            ("XESS","Sharpness"):          (0.0,  1.0,   0.05),
            ("NIS","Sharpness"):           (0.0,  1.0,   0.05),
        }
        return ranges.get((section, key), (0.0, 1.0, 0.01))

    def _string_options(self, section, key):
        opts = {
            ("Renderer","ScalingMode"): ["Native","DLSS","FSR3","XESS","NIS"],
        }
        return opts.get((section, key), [])

    # ── Save ──────────────────────────────────────────────────────────────
    def _save(self):
        errors = []
        # Save ERSS toml
        if self.vars and self.erss_path:
            data_map = {}
            for lookup, var in self.vars.items():
                if isinstance(var, tuple):
                    str_var, opts_dict, labels_dict = var
                    rev = {v: k for k, v in labels_dict.items()}
                    raw_val = rev.get(str_var.get(), str_var.get())
                    data_map[lookup] = py_to_toml(raw_val)
                elif isinstance(var, tk.BooleanVar):
                    data_map[lookup] = py_to_toml(var.get())
                elif isinstance(var, tk.DoubleVar):
                    data_map[lookup] = py_to_toml(round(var.get(), 4))
                elif isinstance(var, tk.IntVar):
                    data_map[lookup] = py_to_toml(var.get())
                elif isinstance(var, tk.StringVar):
                    data_map[lookup] = py_to_toml(var.get())
            try:
                save_toml(self.erss_path, data_map)
            except Exception as e:
                errors.append(f"ERSS: {e}")

        # Save game XML
        if self.xml_vars and self.xml_path:
            updates = {k: v.get() for k, v in self.xml_vars.items()}
            try:
                save_xml(self.xml_path, updates)
            except Exception as e:
                errors.append(f"Game XML: {e}")

        if errors:
            messagebox.showerror("Save failed", "\n".join(errors))
            self.status.set("✘  Save failed.")
        else:
            self._change_pending = False
            self.status.set(f"✦  Saved at {datetime.now().strftime('%H:%M:%S')}")

    def _reload(self):
        self._discover_paths()
        self._auto_accept_fps_warning()
        self._change_pending = False
        tab = self.active_tab.get()
        self._switch_tab(tab)
        self.status.set("⟳  Reloaded from disk.")


if __name__ == "__main__":
    app = EldenEditor()
    app.mainloop()
