"""
Remastered Settings - Elden Ring
Unified editor: ERSS-FG mod, game graphics, character saves, co-op settings.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tomllib, configparser
import os, re, json, struct, shutil, subprocess, ctypes
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET

# ── Paths ─────────────────────────────────────────────────────────────────
ERSS_TOML_CANDIDATES = [
    r"E:\eldenring\ERSS2\ERSS-FG.toml",
    r"C:\Program Files (x86)\Steam\steamapps\common\ELDEN RING\Game\ERSS2\ERSS-FG.toml",
]
GAME_XML_CANDIDATES = [
    os.path.join(os.environ.get("APPDATA",""), "EldenRing", "GraphicsConfig.xml"),
]
COOP_INI_CANDIDATES = [
    r"E:\eldenring\SeamlessCoop\ersc_settings.ini",
    r"C:\Program Files (x86)\Steam\steamapps\common\ELDEN RING\Game\SeamlessCoop\ersc_settings.ini",
]
MEMORY_FILE = os.path.join(os.environ.get("APPDATA",""), "EldenRingSettingsEditor", "paths.json")
USER_SAVES  = os.path.join(os.environ.get("APPDATA",""), "EldenRingSettingsEditor", "CharacterSaves")

# ── Binary offsets ────────────────────────────────────────────────────────
NAME_LEN=34; OFF_LEVEL=34; OFF_PLAYTIME=38; OFF_LOCATION=42; OFF_RUNES=50
FACE_MARKER=b"FACE"

# ── Location lookup ───────────────────────────────────────────────────────
LOCATION_MAP={
    0x00000:"The First Step",0x110A0:"Limgrave",0x110A1:"Stormveil Castle",
    0x11100:"Weeping Peninsula",0x11400:"Liurnia of the Lakes",0x11410:"Raya Lucaria Academy",
    0x11420:"Altus Plateau",0x11430:"Leyndell, Royal Capital",0x11440:"Mt. Gelmir",
    0x11450:"Volcano Manor",0x11500:"Caelid",0x11510:"Dragonbarrow",
    0x11600:"Mountaintops of the Giants",0x11610:"Consecrated Snowfield",
    0x11700:"Siofra River",0x11710:"Nokron, Eternal City",0x11720:"Ainsel River",
    0x11800:"Deeproot Depths",0x11900:"Lake of Rot",0x11A00:"Crumbling Farum Azula",
    0x11B00:"Ashen Leyndell",0x11C00:"Mohgwyn Palace",
    0x11D00:"Elphael, Brace of the Haligtree",0x11E00:"Miquella's Haligtree",
    0x12000:"Shadow of the Erdtree",0x12100:"Scadu Altus",0x12200:"Rauh Base",
    0x12300:"Belurat",0x12400:"Stone Coffin Fissure",
}
def location_name(lid):
    if lid==0: return "New Game"
    best=min(LOCATION_MAP,key=lambda k:abs(k-lid))
    return LOCATION_MAP[best] if abs(best-lid)<0x200 else f"Unknown (0x{lid:05X})"

# ── Hidden ERSS keys ──────────────────────────────────────────────────────
HIDDEN_ERSS={
    "ImGuiUseGamepadNav","DatePopup","ShowAdvancedSettingsWindow","DateFirstLaunch",
    "DPIOverride","PrevDPI","bIsFPSUnlockWarningAccepted","CPUMask",
    "ImGuiUseGamepadToggle","OverlayToggleKey",
}

# ── Friendly labels ───────────────────────────────────────────────────────
LABELS={
    "IsHDR":"HDR","ScalingMode":"Upscaling Mode","LatencyReductionMode":"Latency Reduction",
    "RemoveFPSLimit":"Remove FPS Limit","MaxFPS":"Max FPS","HDRGamma":"HDR Gamma",
    "HDRGammaHUD":"HDR Gamma (HUD)","HDRBrightness":"HDR Brightness",
    "HDRSaturation":"HDR Saturation","HDRBrightnessHUD":"HUD Brightness",
    "HDRSceneHDRPassthrough":"HDR Passthrough","GammaLevel":"Gamma Level",
    "OverrideFullscreenState":"Override Fullscreen","OverrideColorSpace":"Override Color Space",
    "OverrideRefreshRate":"Override Refresh Rate","Force10Bit":"Force 10-bit Color",
    "BindDepth":"Bind Depth Buffer","DLSSPreset":"DLSS Preset","DLSSMode":"DLSS Quality",
    "SharpenMode":"Sharpening Mode","Sharpness":"Sharpness","LimitFrameRate":"Limit Frame Rate",
    "NumGenFrames":"Generated Frames","ReflexMode":"NVIDIA Reflex","FrameGenMode":"Frame Gen Mode",
    "GIGlitchMitigation":"GI Glitch Fix","EnableFrameGen":"Enable Frame Generation",
    "QualityMode":"Quality Mode","UseSharpen":"Use Sharpening",
    "ShowMetricsWindow":"Show Metrics Window",
    "ScreenMode":"Screen Mode","TextureQuality":"Texture Quality",
    "Antialiasing":"Anti-aliasing","SSAO":"Ambient Occlusion","DepthOfField":"Depth of Field",
    "MotionBlur":"Motion Blur","ShadowQuality":"Shadow Quality","LightingQuality":"Lighting Quality",
    "EffectsQuality":"Effects Quality","ReflectionQuality":"Reflection Quality",
    "WaterSurfaceQuality":"Water Quality","ShadeQuality":"Shade Quality",
    "VolumetricEffectQuality":"Volumetric Effects","RaytracingQuality":"Ray Tracing Quality",
    "GIDataQuality":"Global Illumination","GrassQuality":"Grass Quality",
    "Auto-detectBestRenderingSettings":"Auto-detect Settings",
}
def friendly(k):
    if k in LABELS: return LABELS[k]
    return re.sub(r'(?<=[a-z])(?=[A-Z])',' ',k).replace("_"," ")

# ── Renderer ordering ─────────────────────────────────────────────────────
RENDERER_ORDER=[
    "ScalingMode","LatencyReductionMode","GammaLevel",
    "RemoveFPSLimit","IsHDR","HDRSceneHDRPassthrough",
    "OverrideRefreshRate","OverrideColorSpace","OverrideFullscreenState","Force10Bit",
    "MaxFPS",
    "HDRGammaHUD","HDRBrightness","HDRGamma","HDRSaturation","HDRBrightnessHUD",
]

# ── Arrow-int keys: use ◀▶ for these fields ──────────────────────────────
# Tuple: (display_lo, display_hi, step, is_fraction)
# is_fraction=True  → stored as 0.0-1.0 float, displayed as 0-100 integer
# is_fraction=False → stored and displayed as-is
ARROW_INT_KEYS={
    ("Renderer","MaxFPS"):      (0,   999,  1,   False),
    ("Renderer","HDRBrightness"):(100, 1000, 10,  False),
    ("Renderer","HDRGammaHUD"): (10,  300,  1,   True),   # 0.1-3.0 stored
    ("Renderer","HDRGamma"):    (10,  300,  1,   True),   # 0.1-3.0 stored
    ("Renderer","HDRSaturation"):(0,  200,  1,   True),   # 0.0-2.0 stored
    ("Renderer","HDRBrightnessHUD"):(10,200,1,   True),   # 0.1-2.0 stored
    ("DLSS","Sharpness"):       (0,   100,  1,   True),   # 0.0-1.0 stored
    ("FSR3U","Sharpness"):      (0,   100,  1,   True),
    ("XESS","Sharpness"):       (0,   100,  1,   True),
    ("NIS","Sharpness"):        (0,   100,  1,   True),
}

# ── Palette ───────────────────────────────────────────────────────────────
BG_DARK="#0e0c09"; BG_MID="#1a1710"; BG_PANEL="#211f16"
GOLD="#c8a84b"; GOLD_LIGHT="#e8c96a"; GOLD_DIM="#7a6328"
RED_ACCENT="#8b1a1a"; TEXT_MAIN="#d4c9a0"; TEXT_DIM="#7a7060"
TEXT_BRIGHT="#f0e6c0"; GREEN_OK="#4a7a4a"

FONT_TITLE  =("Georgia",16,"bold"); FONT_SECTION=("Georgia",11,"bold")
FONT_LABEL  =("Georgia",9);         FONT_VALUE  =("Consolas",9)
FONT_BUTTON =("Georgia",10,"bold"); FONT_SMALL  =("Georgia",8)
FONT_CHAR   =("Georgia",12,"bold"); FONT_CHAR_SUB=("Georgia",9)

# ── DLSS registry ─────────────────────────────────────────────────────────
DLSS_REG_KEY=r"SOFTWARE\NVIDIA Corporation\Global\NGXCore"
DLSS_REG_VAL="ShowDlssIndicator"

def get_dlss_indicator():
    try:
        import winreg
        k=winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,DLSS_REG_KEY)
        v,_=winreg.QueryValueEx(k,DLSS_REG_VAL); winreg.CloseKey(k); return v!=0
    except: return False

def set_dlss_indicator(enabled):
    val=1 if enabled else 0
    try:
        import winreg
        k=winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,DLSS_REG_KEY,0,winreg.KEY_SET_VALUE)
        winreg.SetValueEx(k,DLSS_REG_VAL,0,winreg.REG_DWORD,val); winreg.CloseKey(k); return True
    except PermissionError:
        cmd=f'reg add "HKLM\\{DLSS_REG_KEY}" /v {DLSS_REG_VAL} /t REG_DWORD /d {val} /f'
        try:
            subprocess.run(["powershell","-NoProfile","-Command",
                f'Start-Process cmd -ArgumentList \'/c {cmd}\' -Verb RunAs -Wait'],
                check=True,capture_output=True); return True
        except: return False
    except: return False

# ── Memory ────────────────────────────────────────────────────────────────
def load_mem():
    try:
        with open(MEMORY_FILE) as f: return json.load(f)
    except: return {}

def save_mem(d):
    try:
        os.makedirs(os.path.dirname(MEMORY_FILE),exist_ok=True)
        with open(MEMORY_FILE,"w") as f: json.dump(d,f)
    except: pass

def find_file(candidates,key):
    m=load_mem()
    if key in m and os.path.exists(m[key]): return m[key]
    for p in candidates:
        if os.path.exists(p): m[key]=p; save_mem(m); return p
    return None

# ── TOML helpers ──────────────────────────────────────────────────────────
def load_toml(path):
    with open(path,"rb") as f: return tomllib.load(f)

def save_toml(path,data_map):
    with open(path,"r",encoding="utf-8") as f: lines=f.readlines()
    sec=None; out=[]
    for line in lines:
        s=line.strip()
        m=re.match(r'^\[([^\]]+)\]',s)
        if m: sec=m.group(1); out.append(line); continue
        kv=re.match(r'^(\w+)\s*=\s*(.+)',s)
        if kv:
            k=kv.group(1); lk=(sec,k) if sec else (None,k)
            if lk in data_map: out.append(f"{k} = {data_map[lk]}\n"); continue
        out.append(line)
    with open(path,"w",encoding="utf-8") as f: f.writelines(out)

# ── XML helpers ───────────────────────────────────────────────────────────
def load_xml(path):
    raw=Path(path).read_bytes()
    for enc in ("utf-16","utf-8-sig","utf-8"):
        try: text=raw.decode(enc); break
        except: continue
    root=ET.fromstring(text.lstrip('\ufeff'))
    return {c.tag:(c.text or "") for c in root}

def save_xml(path,updates):
    raw=Path(path).read_bytes()
    for enc in ("utf-16","utf-8-sig","utf-8"):
        try: text=raw.decode(enc); break
        except: continue
    for k,v in updates.items():
        text=re.sub(f'<{re.escape(k)}>[^<]*</{re.escape(k)}>',f'<{k}>{v}</{k}>',text)
    Path(path).write_bytes(text.encode("utf-16"))

# ── INI helpers ───────────────────────────────────────────────────────────
def load_ini(path):
    cfg=configparser.ConfigParser(comment_prefixes=(';','#'),inline_comment_prefixes=(';','#'))
    cfg.read(path,encoding="utf-8"); return cfg

def save_ini(path,cfg):
    with open(path,"w",encoding="utf-8") as f: cfg.write(f)

def py_to_toml(v):
    if isinstance(v,bool): return "true" if v else "false"
    if isinstance(v,str):  return f'"{v}"'
    if isinstance(v,float):return f"{v}"
    return str(v)

# ── Save file parser ──────────────────────────────────────────────────────
def fmt_time(s):
    h=s//3600; m=(s%3600)//60; sec=s%60; return f"{h}:{m:02d}:{sec:02d}"

def scan_save_file(path):
    data=Path(path).read_bytes(); chars=[]; pos=0
    while True:
        idx=data.find(FACE_MARKER,pos)
        if idx==-1: break
        ns=idx-58
        if ns<0: pos=idx+4; continue
        try:
            name=data[ns:ns+NAME_LEN].decode("utf-16-le").rstrip('\x00').strip()
            if not name or not any(c.isalpha() for c in name): pos=idx+4; continue
            lv=struct.unpack_from("<I",data,ns+OFF_LEVEL)[0]
            pt=struct.unpack_from("<I",data,ns+OFF_PLAYTIME)[0]
            li=struct.unpack_from("<I",data,ns+OFF_LOCATION)[0]
            ru=struct.unpack_from("<I",data,ns+OFF_RUNES)[0]
            if lv==0 or lv>713: pos=idx+4; continue
            chars.append({"name":name,"level":lv,"playtime":pt,"playtime_fmt":fmt_time(pt),
                          "location":location_name(li),"loc_id":li,"runes":ru,"offset":ns})
        except: pass
        pos=idx+4
    seen=set(); unique=[]
    for c in chars:
        k=(c["name"],c["level"])
        if k not in seen: seen.add(k); unique.append(c)
    return unique

def find_save_files():
    saves=[]; er=os.path.join(os.environ.get("APPDATA",""),"EldenRing")
    if not os.path.isdir(er): return saves
    for sid in os.listdir(er):
        sd=os.path.join(er,sid)
        if not os.path.isdir(sd): continue
        for fn in os.listdir(sd):
            fp=os.path.join(sd,fn)
            if fn.endswith(".sl2"): saves.append((fp,"Offline / Standard","sl2"))
            elif fn.endswith(".co2"): saves.append((fp,"Seamless Co-op","co2"))
    return saves

# ── ER Icon as PhotoImage data (SVG-style sword rendered to XBM) ──────────
ER_SWORD_XBM="""
#define sword_width 32
#define sword_height 32
static unsigned char sword_bits[] = {
0x00,0x01,0x00,0x00,0x80,0x03,0x00,0x00,0xc0,0x07,0x00,0x00,0xe0,0x0f,0x00,
0x00,0x70,0x1c,0x00,0x00,0x38,0x38,0x00,0x00,0x1c,0x70,0x00,0x00,0x0e,0xe0,
0x00,0x00,0x07,0xc0,0x01,0x00,0x83,0x80,0x03,0x00,0xc1,0x01,0x07,0x00,0xe0,
0x00,0x0e,0x00,0x70,0x00,0x1c,0x00,0x38,0x00,0x0e,0x00,0x1c,0x00,0x07,0x00,
0x0e,0x80,0x03,0x00,0x1c,0xc0,0x01,0x00,0x38,0xe0,0x00,0x00,0x70,0x70,0x00,
0x00,0xe0,0x38,0x00,0x00,0xc0,0x1d,0x00,0x00,0x80,0x0f,0x00,0x00,0x00,0x07,
0x00,0x00,0x00,0x03,0x00,0x00,0x80,0x01,0x00,0x00,0xc0,0x00,0x00,0x00,0x60,
0x00,0x00,0x00,0x30,0x00,0x00,0x00,0x18,0x00,0x00,0x00,0x0c,0x00,0x00,0x00};
"""

# ── Main App ──────────────────────────────────────────────────────────────
class EldenEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Remastered Settings  –  Elden Ring")
        self.configure(bg=BG_DARK)
        self.resizable(True,True)
        self.geometry("920x940")
        self.minsize(800,600)
        self._dark_titlebar()
        self._set_icon()

        self.vars={}; self.xml_vars={}; self.coop_vars={}
        self.erss_raw={}; self.xml_raw={}; self.coop_cfg=None
        self.erss_path=None; self.xml_path=None; self.coop_path=None
        self._changed=False

        self._styles()
        self._discover()
        self._auto_fps_warn()
        self._build_ui()

    def _dark_titlebar(self):
        try:
            self.update()
            dwm=ctypes.WinDLL("dwmapi"); v=ctypes.c_int(1)
            dwm.DwmSetWindowAttribute(self.winfo_id(),20,ctypes.byref(v),ctypes.sizeof(v))
        except: pass

    def _set_icon(self):
        """Set a sword-themed window icon."""
        try:
            img=tk.BitmapImage(data=ER_SWORD_XBM,foreground=GOLD,background=BG_DARK)
            self.iconbitmap(bitmap="@/dev/null") if os.name!="nt" else None
            self.iconphoto(True,img)
        except: pass

    def _discover(self):
        self.erss_path=find_file(ERSS_TOML_CANDIDATES,"erss_toml")
        self.xml_path =find_file(GAME_XML_CANDIDATES,"game_xml")
        self.coop_path=find_file(COOP_INI_CANDIDATES,"coop_ini")
        if self.erss_path:
            try: self.erss_raw=load_toml(self.erss_path)
            except Exception as e: messagebox.showerror("ERSS load failed",str(e))
        if self.xml_path:
            try: self.xml_raw=load_xml(self.xml_path)
            except Exception as e: messagebox.showerror("Game XML load failed",str(e))
        if self.coop_path:
            try: self.coop_cfg=load_ini(self.coop_path)
            except Exception as e: messagebox.showerror("Co-op INI load failed",str(e))

    def _auto_fps_warn(self):
        if not self.erss_path or not self.erss_raw: return
        if not self.erss_raw.get("bIsFPSUnlockWarningAccepted",True):
            try: save_toml(self.erss_path,{(None,"bIsFPSUnlockWarningAccepted"):"true"})
            except: pass

    # ── Styles ────────────────────────────────────────────────────────────
    def _styles(self):
        s=ttk.Style(self); s.theme_use("clam")
        s.configure("TFrame",background=BG_DARK)
        s.configure("TLabel",background=BG_PANEL,foreground=TEXT_MAIN,font=FONT_LABEL)
        s.configure("TCheckbutton",background=BG_PANEL,foreground=TEXT_MAIN,
                    font=FONT_LABEL,selectcolor=GOLD_DIM,indicatorcolor=GOLD_DIM)
        s.map("TCheckbutton",foreground=[("active",GOLD_LIGHT)],background=[("active",BG_PANEL)])
        s.configure("TCombobox",fieldbackground=BG_PANEL,background=GOLD_DIM,
                    foreground=TEXT_BRIGHT,font=FONT_VALUE,arrowcolor=GOLD)
        s.map("TCombobox",fieldbackground=[("readonly",BG_PANEL)],foreground=[("readonly",TEXT_BRIGHT)])
        s.configure("TScrollbar",background=BG_MID,troughcolor=BG_DARK,
                    arrowcolor=GOLD_DIM,borderwidth=0,relief="flat")
        s.map("TScrollbar",background=[("active",GOLD_DIM),("!active",BG_MID)])

    def _btn(self,parent,text,cmd,bg=GOLD_DIM,hover=GOLD,side="right",padx=(8,0),pady=0):
        b=tk.Button(parent,text=text,command=cmd,bg=bg,fg=TEXT_BRIGHT,
                    activebackground=hover,activeforeground=BG_DARK,
                    font=FONT_BUTTON,relief="flat",bd=0,padx=14,pady=6,cursor="hand2")
        b.pack(side=side,padx=padx,pady=pady); return b

    def _arrow_int(self,parent,var,lo,hi,step=1,width=7):
        """◀ [value] ▶ — universal arrow-int widget, consistent sizing."""
        fr=tk.Frame(parent,bg=BG_PANEL)
        def dec():
            try: v=float(var.get()); var.set(str(int(max(lo,v-step)))); self._mark()
            except: pass
        def inc():
            try: v=float(var.get()); var.set(str(int(min(hi,v+step)))); self._mark()
            except: pass
        tk.Button(fr,text="◀",command=dec,bg=GOLD_DIM,fg=TEXT_BRIGHT,
                  activebackground=GOLD,activeforeground=BG_DARK,
                  font=("Georgia",8,"bold"),relief="flat",bd=0,
                  padx=5,pady=1,cursor="hand2").pack(side="left")
        tk.Entry(fr,textvariable=var,width=width,bg=BG_DARK,fg=TEXT_BRIGHT,
                 insertbackground=GOLD,relief="flat",font=FONT_VALUE,justify="center",
                 highlightbackground=GOLD_DIM,highlightthickness=1).pack(side="left",padx=2)
        tk.Button(fr,text="▶",command=inc,bg=GOLD_DIM,fg=TEXT_BRIGHT,
                  activebackground=GOLD,activeforeground=BG_DARK,
                  font=("Georgia",8,"bold"),relief="flat",bd=0,
                  padx=5,pady=1,cursor="hand2").pack(side="left")
        var.trace_add("write",lambda *a:self._mark())
        return fr

    # ── Main UI ───────────────────────────────────────────────────────────
    def _build_ui(self):
        hdr=tk.Frame(self,bg=BG_DARK,pady=10)
        hdr.pack(fill="x",padx=20,pady=(16,0))
        tk.Label(hdr,text="⚔",font=("Georgia",20),bg=BG_DARK,fg=GOLD).pack(side="left",padx=(0,10))
        tb=tk.Frame(hdr,bg=BG_DARK); tb.pack(side="left")
        tk.Label(tb,text="Remastered Settings",font=FONT_TITLE,bg=BG_DARK,fg=GOLD).pack(anchor="w")
        tk.Label(tb,text="Elden Ring",font=FONT_SMALL,bg=BG_DARK,fg=GOLD_DIM).pack(anchor="w")
        tk.Frame(self,bg=GOLD_DIM,height=1).pack(fill="x",padx=20,pady=(10,0))

        nb=tk.Frame(self,bg=BG_DARK); nb.pack(fill="x",padx=20,pady=(8,0))
        self.active_tab=tk.StringVar(value="")
        self._tabs={}
        tab_defs=[]
        if self.xml_path:  tab_defs.append(("game","🎮  Game Settings"))
        if self.erss_path: tab_defs.append(("erss","⚙  Advanced"))
        tab_defs.append(("chars","👤  Characters"))
        if self.coop_path: tab_defs.append(("coop","🤝  Multiplayer"))
        for tid,tlabel in tab_defs:
            b=tk.Button(nb,text=tlabel,bg=GOLD_DIM,fg=TEXT_BRIGHT,
                        activebackground=GOLD,activeforeground=BG_DARK,
                        font=FONT_BUTTON,relief="flat",bd=0,padx=16,pady=6,cursor="hand2",
                        command=lambda t=tid:self._switch(t))
            b.pack(side="left",padx=(0,4)); self._tabs[tid]=b
        tk.Frame(self,bg=GOLD_DIM,height=1).pack(fill="x",padx=20,pady=(6,0))

        outer=tk.Frame(self,bg=BG_DARK)
        outer.pack(fill="both",expand=True,padx=20,pady=10)
        self.canvas=tk.Canvas(outer,bg=BG_DARK,highlightthickness=0,bd=0)
        sb=ttk.Scrollbar(outer,orient="vertical",command=self.canvas.yview,style="TScrollbar")
        self.canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right",fill="y")
        self.canvas.pack(side="left",fill="both",expand=True)
        self.body=tk.Frame(self.canvas,bg=BG_DARK)
        wid=self.canvas.create_window((0,0),window=self.body,anchor="nw")
        self.canvas.bind("<Configure>",lambda e:self.canvas.itemconfig(wid,width=e.width))
        self.body.bind("<Configure>",lambda e:self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind_all("<MouseWheel>",lambda e:self.canvas.yview_scroll(int(-1*(e.delta/120)),"units"))

        tk.Frame(self,bg=GOLD_DIM,height=1).pack(fill="x",padx=20)
        foot=tk.Frame(self,bg=BG_DARK,pady=10); foot.pack(fill="x",padx=20)
        self.status=tk.StringVar(value="Ready.")
        tk.Label(foot,textvariable=self.status,font=FONT_SMALL,bg=BG_DARK,fg=TEXT_DIM).pack(side="left")
        self._btn(foot,"⟳  Reload",self._reload,bg=RED_ACCENT,hover="#b02222")
        self._btn(foot,"✦  Save Settings",self._save)

        if tab_defs: self._switch(tab_defs[0][0])

    def _switch(self,tid):
        self.active_tab.set(tid)
        for t,b in self._tabs.items():
            b.config(bg=GOLD if t==tid else GOLD_DIM,fg=BG_DARK if t==tid else TEXT_BRIGHT)
        for w in self.body.winfo_children(): w.destroy()
        self.vars.clear(); self.xml_vars.clear(); self.coop_vars.clear()
        if   tid=="erss":  self._render_erss()
        elif tid=="game":  self._render_game()
        elif tid=="chars": self._render_chars()
        elif tid=="coop":  self._render_coop()
        self.canvas.yview_moveto(0)

    # ── Co-op Settings Tab ────────────────────────────────────────────────
    def _render_coop(self):
        if not self.coop_cfg:
            tk.Label(self.body,text="Co-op settings file not found.",
                     font=FONT_LABEL,bg=BG_DARK,fg=RED_ACCENT,pady=20).pack(); return

        cfg=self.coop_cfg

        # ── Gameplay ──────────────────────────────────────────────────────
        self._coop_section("⚔   Gameplay",[
            ("GAMEPLAY","overhead_player_display","Overhead Player Display","choice",
             ["0:Off","1:None","2:Ping","3:Soul Level","4:Death Count","5:Level + Ping"]),
            ("GAMEPLAY","allow_invaders","Allow Invaders","bool",None),
            ("GAMEPLAY","death_debuffs","Death Debuffs (Rot Essence on death)","bool",None),
            ("GAMEPLAY","allow_summons","Allow Spirit Summons","bool",None),
            ("GAMEPLAY","always_spectate_on_death","Spectate on Death","bool",None),
            ("GAMEPLAY","skip_splash_screens","Skip Intro Logos","bool",None),
            ("GAMEPLAY","append_steam_id_to_players","Show Steam ID Overhead","bool",None),
        ],cfg)

        # ── Enemy Scaling ─────────────────────────────────────────────────
        self._coop_section("📈  Enemy Scaling",[
            ("SCALING","enemy_health_scaling","Enemy Health per Player (%)","arrow",(0,500,5)),
            ("SCALING","enemy_damage_scaling","Enemy Damage per Player (%)","arrow",(0,500,5)),
            ("SCALING","enemy_posture_scaling","Enemy Posture per Player (%)","arrow",(0,500,5)),
            ("SCALING","boss_health_scaling","Boss Health per Player (%)","arrow",(0,500,5)),
            ("SCALING","boss_damage_scaling","Boss Damage per Player (%)","arrow",(0,500,5)),
            ("SCALING","boss_posture_scaling","Boss Posture per Player (%)","arrow",(0,500,5)),
        ],cfg)

        # ── Session ───────────────────────────────────────────────────────
        self._coop_section("🔑  Session",[
            ("PASSWORD","cooppassword","Session Password","password",None),
            ("SAVE","save_file_extension","Save File Extension","text",None),
        ],cfg)

    def _coop_section(self,title,fields,cfg):
        wrap=tk.Frame(self.body,bg=BG_MID,highlightbackground=GOLD_DIM,highlightthickness=1)
        wrap.pack(fill="x",pady=(0,10))
        hdr=tk.Frame(wrap,bg=BG_MID,pady=6); hdr.pack(fill="x",padx=12)
        tk.Label(hdr,text=title,font=FONT_SECTION,bg=BG_MID,fg=GOLD_LIGHT).pack(side="left")
        tk.Frame(hdr,bg=GOLD_DIM,height=1).pack(side="left",fill="x",expand=True,padx=(10,0),pady=6)
        inner=tk.Frame(wrap,bg=BG_PANEL,padx=14,pady=10)
        inner.pack(fill="x",padx=8,pady=(0,8)); inner.columnconfigure(1,weight=1)

        for row,(sec,key,label,kind,opts) in enumerate(fields):
            raw=cfg.get(sec,key,fallback="").strip()
            tk.Label(inner,text=label,font=FONT_LABEL,bg=BG_PANEL,fg=TEXT_MAIN,
                     anchor="w",width=28).grid(row=row,column=0,sticky="w",pady=4,padx=(0,12))
            vk=f"{sec}.{key}"

            if kind=="bool":
                v=tk.BooleanVar(value=raw=="1")
                self.coop_vars[vk]=(v,"bool",sec,key)
                ttk.Checkbutton(inner,variable=v,style="TCheckbutton",
                                onvalue=True,offvalue=False,
                                command=self._mark).grid(row=row,column=1,sticky="w",pady=4)

            elif kind=="choice":
                # opts is list of "value:label"
                val_map={o.split(":")[0]:o.split(":",1)[1] for o in opts}
                lbl_map={o.split(":",1)[1]:o.split(":")[0] for o in opts}
                cur_lbl=val_map.get(raw,raw)
                v=tk.StringVar(value=cur_lbl)
                self.coop_vars[vk]=(v,"choice",sec,key,lbl_map)
                cb=ttk.Combobox(inner,textvariable=v,values=list(val_map.values()),
                                state="readonly",width=22,font=FONT_VALUE)
                cb.grid(row=row,column=1,sticky="w",pady=4)
                cb.bind("<<ComboboxSelected>>",lambda e:self._mark())

            elif kind=="arrow":
                lo,hi,step=opts
                v=tk.StringVar(value=raw)
                self.coop_vars[vk]=(v,"int",sec,key)
                self._arrow_int(inner,v,lo,hi,step).grid(row=row,column=1,sticky="w",pady=4)

            elif kind=="text":
                v=tk.StringVar(value=raw)
                self.coop_vars[vk]=(v,"text",sec,key)
                tk.Entry(inner,textvariable=v,width=22,bg=BG_DARK,fg=TEXT_BRIGHT,
                         insertbackground=GOLD,relief="flat",font=FONT_VALUE,
                         highlightbackground=GOLD_DIM,highlightthickness=1).grid(row=row,column=1,sticky="w",pady=4)
                v.trace_add("write",lambda *a:self._mark())

            elif kind=="password":
                # Fix 4: text entry + copy button to the right, same arrow-button style
                v=tk.StringVar(value=raw)
                self.coop_vars[vk]=(v,"text",sec,key)
                fr=tk.Frame(inner,bg=BG_PANEL); fr.grid(row=row,column=1,sticky="w",pady=4)
                tk.Entry(fr,textvariable=v,width=22,bg=BG_DARK,fg=TEXT_BRIGHT,
                         insertbackground=GOLD,relief="flat",font=FONT_VALUE,
                         highlightbackground=GOLD_DIM,highlightthickness=1).pack(side="left")
                def _copy(sv=v):
                    self.clipboard_clear(); self.clipboard_append(sv.get())
                    self.status.set("✦  Password copied to clipboard.")
                tk.Button(fr,text="⎘",command=_copy,bg=GOLD_DIM,fg=TEXT_BRIGHT,
                          activebackground=GOLD,activeforeground=BG_DARK,
                          font=("Georgia",8,"bold"),relief="flat",bd=0,
                          padx=6,pady=1,cursor="hand2").pack(side="left",padx=(4,0))
                v.trace_add("write",lambda *a:self._mark())

    # ── ERSS Tab ──────────────────────────────────────────────────────────
    def _render_erss(self):
        d=self.erss_raw
        top={k:v for k,v in d.items() if not isinstance(v,dict) and k not in HIDDEN_ERSS}
        self._section_erss_general(top)
        if "Renderer" in d and isinstance(d["Renderer"],dict):
            self._section_renderer(d["Renderer"])
        for key,label in [
            ("SwapChain","⛓   Swap Chain"),
            ("DLSS","✦   DLSS Upscaling"),("DLSS-G","✦✦  DLSS Frame Generation"),
            ("FrameGeneration","🎞   Frame Generation"),("FSR3U","◈   FSR 3 Upscaler"),
            ("XESS","◇   Intel XeSS"),("NIS","◈   NIS Sharpener"),
            ("ReShade","🎨  ReShade"),("Reflex","⚡  NVIDIA Reflex"),
        ]:
            if key in d and isinstance(d[key],dict):
                self._section(label,key,d[key])

    def _section_erss_general(self,top):
        wrap=tk.Frame(self.body,bg=BG_MID,highlightbackground=GOLD_DIM,highlightthickness=1)
        wrap.pack(fill="x",pady=(0,10))
        hdr=tk.Frame(wrap,bg=BG_MID,pady=6); hdr.pack(fill="x",padx=12)
        tk.Label(hdr,text="General",font=FONT_SECTION,bg=BG_MID,fg=GOLD_LIGHT).pack(side="left")
        tk.Frame(hdr,bg=GOLD_DIM,height=1).pack(side="left",fill="x",expand=True,padx=(10,0),pady=6)
        inner=tk.Frame(wrap,bg=BG_PANEL,padx=14,pady=10)
        inner.pack(fill="x",padx=8,pady=(0,8)); inner.columnconfigure(1,weight=1)
        row=0
        for k,v in top.items():
            self._row(inner,row,None,k,v); row+=1
        # DLSS Indicator
        tk.Label(inner,text="Disable DLSS Indicator",font=FONT_LABEL,bg=BG_PANEL,fg=TEXT_MAIN,
                 anchor="w",width=24).grid(row=row,column=0,sticky="w",pady=3,padx=(0,12))
        dlss_on=get_dlss_indicator()
        self._dlss_var=tk.BooleanVar(value=not dlss_on)
        fr=tk.Frame(inner,bg=BG_PANEL); fr.grid(row=row,column=1,sticky="w",pady=3)
        ttk.Checkbutton(fr,variable=self._dlss_var,style="TCheckbutton",
                        onvalue=True,offvalue=False,
                        command=self._toggle_dlss_indicator).pack(side="left")
        tk.Label(fr,text="(requires admin)",font=FONT_SMALL,bg=BG_PANEL,fg=TEXT_DIM).pack(side="left",padx=(6,0))

    def _toggle_dlss_indicator(self):
        want_off=self._dlss_var.get()
        ok=set_dlss_indicator(enabled=not want_off)
        if ok:
            self.status.set(f"✦  DLSS Indicator {'disabled' if want_off else 'enabled'}. Restart game to apply.")
        else:
            messagebox.showerror("Registry Error","Could not write to registry.\nTry running as Administrator.")
            self._dlss_var.set(not want_off)

    def _section_renderer(self,data):
        filt={k:v for k,v in data.items() if k not in HIDDEN_ERSS}
        wrap=tk.Frame(self.body,bg=BG_MID,highlightbackground=GOLD_DIM,highlightthickness=1)
        wrap.pack(fill="x",pady=(0,10))
        hdr=tk.Frame(wrap,bg=BG_MID,pady=6); hdr.pack(fill="x",padx=12)
        tk.Label(hdr,text="🖥   Renderer",font=FONT_SECTION,bg=BG_MID,fg=GOLD_LIGHT).pack(side="left")
        tk.Frame(hdr,bg=GOLD_DIM,height=1).pack(side="left",fill="x",expand=True,padx=(10,0),pady=6)
        inner=tk.Frame(wrap,bg=BG_PANEL,padx=14,pady=10)
        inner.pack(fill="x",padx=8,pady=(0,8)); inner.columnconfigure(1,weight=1)
        ordered=[k for k in RENDERER_ORDER if k in filt]+[k for k in filt if k not in RENDERER_ORDER]
        for row,k in enumerate(ordered):
            self._row(inner,row,"Renderer",k,filt[k])

    def _section(self,title,sec_key,data):
        filt={k:v for k,v in data.items() if k not in HIDDEN_ERSS}
        if not filt: return
        wrap=tk.Frame(self.body,bg=BG_MID,highlightbackground=GOLD_DIM,highlightthickness=1)
        wrap.pack(fill="x",pady=(0,10))
        hdr=tk.Frame(wrap,bg=BG_MID,pady=6); hdr.pack(fill="x",padx=12)
        tk.Label(hdr,text=title,font=FONT_SECTION,bg=BG_MID,fg=GOLD_LIGHT).pack(side="left")
        tk.Frame(hdr,bg=GOLD_DIM,height=1).pack(side="left",fill="x",expand=True,padx=(10,0),pady=6)
        inner=tk.Frame(wrap,bg=BG_PANEL,padx=14,pady=10)
        inner.pack(fill="x",padx=8,pady=(0,8)); inner.columnconfigure(1,weight=1)
        for row,(k,v) in enumerate(filt.items()):
            self._row(inner,row,sec_key,k,v)

    def _row(self,parent,row,sec,key,val):
        lk=(sec,key)
        tk.Label(parent,text=friendly(key),font=FONT_LABEL,bg=BG_PANEL,fg=TEXT_MAIN,
                 anchor="w",width=24).grid(row=row,column=0,sticky="w",pady=3,padx=(0,12))

        # Arrow-int widget (covers MaxFPS, HDR values, Sharpness, etc.)
        aik=ARROW_INT_KEYS.get(lk)
        if aik and isinstance(val,(int,float)):
            lo,hi,step,is_frac=aik
            if is_frac:
                display_val=int(round(float(val)*100))
            else:
                display_val=int(round(float(val)))
            sv=tk.StringVar(value=str(display_val))
            self.vars[lk]=("arrow_float",sv,is_frac)
            self._arrow_int(parent,sv,lo,hi,step).grid(row=row,column=1,sticky="w",pady=3)
            return

        if isinstance(val,bool):
            v=tk.BooleanVar(value=val); self.vars[lk]=v
            ttk.Checkbutton(parent,variable=v,style="TCheckbutton",
                            onvalue=True,offvalue=False,
                            command=self._mark).grid(row=row,column=1,sticky="w",pady=3)
        elif isinstance(val,int) and self._opts(sec,key):
            opts,labels=self._opts(sec,key)
            v=tk.StringVar(value=labels.get(val,str(val))); self.vars[lk]=(v,opts,labels)
            cb=ttk.Combobox(parent,textvariable=v,values=list(labels.values()),
                            state="readonly",width=28,font=FONT_VALUE)
            cb.grid(row=row,column=1,sticky="w",pady=3)
            cb.bind("<<ComboboxSelected>>",lambda e:self._mark())
        elif isinstance(val,float):
            # Any remaining floats not in ARROW_INT_KEYS — plain entry box
            v=tk.DoubleVar(value=val); self.vars[lk]=v
            tk.Entry(parent,textvariable=v,width=10,bg=BG_DARK,fg=TEXT_BRIGHT,
                     insertbackground=GOLD,relief="flat",font=FONT_VALUE,
                     highlightbackground=GOLD_DIM,highlightthickness=1).grid(row=row,column=1,sticky="w",pady=3)
            v.trace_add("write",lambda *a:self._mark())
        elif isinstance(val,str) and not val.startswith("20"):
            v=tk.StringVar(value=val); self.vars[lk]=v
            opts2=self._str_opts(sec,key)
            if opts2:
                cb=ttk.Combobox(parent,textvariable=v,values=opts2,state="readonly",width=28,font=FONT_VALUE)
                cb.grid(row=row,column=1,sticky="w",pady=3)
                cb.bind("<<ComboboxSelected>>",lambda e:self._mark())
            else:
                tk.Entry(parent,textvariable=v,width=30,bg=BG_DARK,fg=TEXT_BRIGHT,
                         insertbackground=GOLD,relief="flat",font=FONT_VALUE,
                         highlightbackground=GOLD_DIM,highlightthickness=1).grid(row=row,column=1,sticky="w",pady=3)
                v.trace_add("write",lambda *a:self._mark())
        elif isinstance(val,int):
            v=tk.IntVar(value=val); self.vars[lk]=v
            tk.Entry(parent,textvariable=v,width=10,bg=BG_DARK,fg=TEXT_BRIGHT,
                     insertbackground=GOLD,relief="flat",font=FONT_VALUE,
                     highlightbackground=GOLD_DIM,highlightthickness=1).grid(row=row,column=1,sticky="w",pady=3)
            v.trace_add("write",lambda *a:self._mark())

    # ── Game XML Tab ──────────────────────────────────────────────────────
    def _render_game(self):
        if not self.xml_raw:
            tk.Label(self.body,text="Game config not found.",font=FONT_LABEL,bg=BG_DARK,fg=RED_ACCENT).pack(pady=20); return
        self._xml_display_section()
        qual=[k for k in self.xml_raw
              if "Width" not in k and "Height" not in k
              and k not in ("ScreenMode","Auto-detectBestRenderingSettings","QualitySetting")]
        self._xml_section("🎨  Quality",qual)
        self._xml_section("⚙   Misc",["Auto-detectBestRenderingSettings"])

    def _xml_display_section(self):
        wrap=tk.Frame(self.body,bg=BG_MID,highlightbackground=GOLD_DIM,highlightthickness=1)
        wrap.pack(fill="x",pady=(0,10))
        hdr=tk.Frame(wrap,bg=BG_MID,pady=6); hdr.pack(fill="x",padx=12)
        tk.Label(hdr,text="🖥   Display",font=FONT_SECTION,bg=BG_MID,fg=GOLD_LIGHT).pack(side="left")
        tk.Frame(hdr,bg=GOLD_DIM,height=1).pack(side="left",fill="x",expand=True,padx=(10,0),pady=6)
        inner=tk.Frame(wrap,bg=BG_PANEL,padx=14,pady=10)
        inner.pack(fill="x",padx=8,pady=(0,8)); inner.columnconfigure(1,weight=1)
        RES_OPTIONS=["800x600","1024x768","1280x720","1280x1024","1366x768",
                     "1600x900","1920x1080","2560x1440","3440x1440","3840x2160"]
        # Screen Mode
        tk.Label(inner,text="Screen Mode",font=FONT_LABEL,bg=BG_PANEL,fg=TEXT_MAIN,
                 anchor="w",width=24).grid(row=0,column=0,sticky="w",pady=3,padx=(0,12))
        sm=tk.StringVar(value=self.xml_raw.get("ScreenMode","FULLSCREEN"))
        self.xml_vars["ScreenMode"]=sm
        cb=ttk.Combobox(inner,textvariable=sm,values=["FULLSCREEN","BORDERLESS","WINDOWED"],
                        state="readonly",width=20,font=FONT_VALUE)
        cb.grid(row=0,column=1,sticky="w",pady=3)
        cb.bind("<<ComboboxSelected>>",lambda e:self._mark())
        # Unified Resolution
        cur_w=self.xml_raw.get("Resolution-FullScreenWidth","2560")
        cur_h=self.xml_raw.get("Resolution-FullScreenHeight","1440")
        cur_res=f"{cur_w}x{cur_h}"
        tk.Label(inner,text="Resolution",font=FONT_LABEL,bg=BG_PANEL,fg=TEXT_MAIN,
                 anchor="w",width=24).grid(row=1,column=0,sticky="w",pady=3,padx=(0,12))
        fr=tk.Frame(inner,bg=BG_PANEL); fr.grid(row=1,column=1,sticky="w",pady=3)
        res_var=tk.StringVar(value=cur_res)
        RES_W=["Resolution-FullScreenWidth","Resolution-BorderlessScreenWidth","Resolution-WindowScreenWidth"]
        RES_H=["Resolution-FullScreenHeight","Resolution-BorderlessScreenHeight","Resolution-WindowScreenHeight"]
        for k in RES_W+RES_H:
            self.xml_vars[k]=tk.StringVar(value=self.xml_raw.get(k,"2560") if "Width" in k else self.xml_raw.get(k,"1440"))
        def sync(*a):
            v=res_var.get()
            if "x" in v:
                try:
                    w,h=v.split("x",1)
                    for k in RES_W: self.xml_vars[k].set(w.strip())
                    for k in RES_H: self.xml_vars[k].set(h.strip())
                except: pass
            self._mark()
        def gp():
            c=res_var.get()
            try: i=RES_OPTIONS.index(c)
            except: i=len(RES_OPTIONS)-1
            res_var.set(RES_OPTIONS[max(0,i-1)]); sync()
        def gn():
            c=res_var.get()
            try: i=RES_OPTIONS.index(c)
            except: i=0
            res_var.set(RES_OPTIONS[min(len(RES_OPTIONS)-1,i+1)]); sync()
        tk.Button(fr,text="◀",command=gp,bg=GOLD_DIM,fg=TEXT_BRIGHT,activebackground=GOLD,activeforeground=BG_DARK,
                  font=("Georgia",8,"bold"),relief="flat",bd=0,padx=6,pady=2,cursor="hand2").pack(side="left")
        tk.Entry(fr,textvariable=res_var,width=10,bg=BG_DARK,fg=TEXT_BRIGHT,insertbackground=GOLD,
                 relief="flat",font=FONT_VALUE,justify="center",
                 highlightbackground=GOLD_DIM,highlightthickness=1).pack(side="left",padx=3)
        tk.Button(fr,text="▶",command=gn,bg=GOLD_DIM,fg=TEXT_BRIGHT,activebackground=GOLD,activeforeground=BG_DARK,
                  font=("Georgia",8,"bold"),relief="flat",bd=0,padx=6,pady=2,cursor="hand2").pack(side="left")
        tk.Label(fr,text="px",font=FONT_SMALL,bg=BG_PANEL,fg=TEXT_DIM).pack(side="left",padx=(4,0))
        res_var.trace_add("write",sync)

    def _xml_section(self,title,keys):
        keys=[k for k in keys if k in self.xml_raw]
        if not keys: return
        wrap=tk.Frame(self.body,bg=BG_MID,highlightbackground=GOLD_DIM,highlightthickness=1)
        wrap.pack(fill="x",pady=(0,10))
        hdr=tk.Frame(wrap,bg=BG_MID,pady=6); hdr.pack(fill="x",padx=12)
        tk.Label(hdr,text=title,font=FONT_SECTION,bg=BG_MID,fg=GOLD_LIGHT).pack(side="left")
        tk.Frame(hdr,bg=GOLD_DIM,height=1).pack(side="left",fill="x",expand=True,padx=(10,0),pady=6)
        inner=tk.Frame(wrap,bg=BG_PANEL,padx=14,pady=10)
        inner.pack(fill="x",padx=8,pady=(0,8)); inner.columnconfigure(1,weight=1)
        XML_OPTS={
            "TextureQuality":["LOW","MEDIUM","HIGH","MAX"],"Antialiasing":["LOW","MEDIUM","HIGH"],
            "SSAO":["LOW","MEDIUM","HIGH","MAX"],"DepthOfField":["LOW","MEDIUM","HIGH","MAX"],
            "MotionBlur":["DISABLE","LOW","MEDIUM","HIGH"],"ShadowQuality":["LOW","MEDIUM","HIGH","MAX"],
            "LightingQuality":["LOW","MEDIUM","HIGH","MAX"],"EffectsQuality":["LOW","MEDIUM","HIGH","MAX"],
            "ReflectionQuality":["LOW","MEDIUM","HIGH","MAX"],"WaterSurfaceQuality":["LOW","MEDIUM","HIGH"],
            "ShadeQuality":["LOW","MEDIUM","HIGH"],"VolumetricEffectQuality":["LOW","MEDIUM","HIGH","MAX"],
            "RaytracingQuality":["LOW","MEDIUM","HIGH","MAX"],"GIDataQuality":["LOW","MEDIUM","HIGH"],
            "GrassQuality":["LOW","MEDIUM","HIGH","MAX"],"Auto-detectBestRenderingSettings":["ON","OFF"],
        }
        for row,key in enumerate(keys):
            val=self.xml_raw[key]
            tk.Label(inner,text=friendly(key),font=FONT_LABEL,bg=BG_PANEL,fg=TEXT_MAIN,
                     anchor="w",width=24).grid(row=row,column=0,sticky="w",pady=3,padx=(0,12))
            if key in XML_OPTS:
                if key not in self.xml_vars: self.xml_vars[key]=tk.StringVar(value=val)
                cb=ttk.Combobox(inner,textvariable=self.xml_vars[key],values=XML_OPTS[key],
                                state="readonly",width=20,font=FONT_VALUE)
                cb.grid(row=row,column=1,sticky="w",pady=3)
                cb.bind("<<ComboboxSelected>>",lambda e:self._mark())
            elif val.lstrip('-').isdigit():
                if key not in self.xml_vars: self.xml_vars[key]=tk.StringVar(value=val)
                tk.Entry(inner,textvariable=self.xml_vars[key],width=12,bg=BG_DARK,fg=TEXT_BRIGHT,
                         insertbackground=GOLD,relief="flat",font=FONT_VALUE,
                         highlightbackground=GOLD_DIM,highlightthickness=1).grid(row=row,column=1,sticky="w",pady=3)
                self.xml_vars[key].trace_add("write",lambda *a:self._mark())
            else:
                if key not in self.xml_vars: self.xml_vars[key]=tk.StringVar(value=val)
                tk.Label(inner,textvariable=self.xml_vars[key],font=FONT_VALUE,
                         bg=BG_PANEL,fg=TEXT_DIM,anchor="w").grid(row=row,column=1,sticky="w",pady=3)

    # ── Characters Tab ────────────────────────────────────────────────────
    def _render_chars(self):
        saves=find_save_files()
        if not saves:
            tk.Label(self.body,text="No Elden Ring save files found.",
                     font=FONT_LABEL,bg=BG_DARK,fg=RED_ACCENT,pady=20).pack(); return
        os.makedirs(USER_SAVES,exist_ok=True)
        for save_path,save_label,ext in saves:
            fw=tk.Frame(self.body,bg=BG_MID,highlightbackground=GOLD_DIM,highlightthickness=1)
            fw.pack(fill="x",pady=(0,12))
            fh=tk.Frame(fw,bg=BG_MID,pady=8); fh.pack(fill="x",padx=12)
            icon="🟡" if ext=="co2" else "⚪"
            # Show save label only — no filename
            tk.Label(fh,text=f"{icon}  {save_label}",font=FONT_SECTION,bg=BG_MID,fg=GOLD_LIGHT).pack(side="left")
            tk.Frame(fw,bg=GOLD_DIM,height=1).pack(fill="x",padx=12,pady=(0,4))
            try: chars=scan_save_file(save_path)
            except Exception as e:
                tk.Label(fw,text=f"Error reading save: {e}",font=FONT_LABEL,bg=BG_PANEL,fg=RED_ACCENT,pady=8).pack(padx=12); continue
            if not chars:
                tk.Label(fw,text="No characters found.",font=FONT_LABEL,bg=BG_PANEL,fg=TEXT_DIM,pady=8).pack(padx=12); continue
            for ch in chars:
                self._char_card(fw,ch,save_path,save_label,ext)

    def _char_card(self,parent,ch,save_path,save_label,ext):
        card=tk.Frame(parent,bg=BG_PANEL,highlightbackground=GOLD_DIM,highlightthickness=1)
        card.pack(fill="x",padx=8,pady=(0,6))
        port=tk.Frame(card,bg=BG_MID,width=72,height=72,highlightbackground=GOLD_DIM,highlightthickness=1)
        port.pack(side="left",padx=(10,12),pady=10); port.pack_propagate(False)
        tk.Label(port,text="⚔",font=("Georgia",28),bg=BG_MID,fg=GOLD_DIM).place(relx=.5,rely=.5,anchor="center")
        mid=tk.Frame(card,bg=BG_PANEL); mid.pack(side="left",fill="both",expand=True,pady=10)
        tk.Label(mid,text=ch["name"],font=FONT_CHAR,bg=BG_PANEL,fg=TEXT_BRIGHT,anchor="w").pack(anchor="w")
        tk.Frame(mid,bg=GOLD_DIM,height=1).pack(fill="x",pady=(3,4))
        tk.Label(mid,text=f"Level  {ch['level']}",font=FONT_CHAR_SUB,bg=BG_PANEL,fg=TEXT_MAIN,anchor="w").pack(anchor="w")
        tk.Label(mid,text=ch["location"],font=FONT_CHAR_SUB,bg=BG_PANEL,fg=TEXT_DIM,anchor="w").pack(anchor="w")
        right=tk.Frame(card,bg=BG_PANEL); right.pack(side="right",padx=(0,10),pady=10)
        tk.Label(right,text=ch["playtime_fmt"],font=("Consolas",12),bg=BG_PANEL,fg=GOLD,anchor="e").pack(anchor="e")
        tk.Label(right,text=save_label,font=FONT_SMALL,bg=BG_PANEL,fg=TEXT_DIM,anchor="e").pack(anchor="e",pady=(0,6))
        btns=tk.Frame(right,bg=BG_PANEL); btns.pack(anchor="e")
        safe=re.sub(r'[^\w]','_',ch["name"]); slot=os.path.join(USER_SAVES,safe)

        def make_save():
            os.makedirs(slot,exist_ok=True); ts=datetime.now().strftime("%Y%m%d_%H%M%S")
            dst=os.path.join(slot,f"{safe}_{ts}.{ext}"); shutil.copy2(save_path,dst)
            self.status.set(f"✦  Save created: {os.path.basename(dst)}")
            messagebox.showinfo("Save Created",f"Save point created:\n{dst}")

        def load_save():
            avail=sorted(Path(slot).glob(f"*.{ext}"),reverse=True) if os.path.isdir(slot) else []
            if not avail:
                messagebox.showwarning("No Saves",f"No save points for {ch['name']}.\nCreate one first."); return
            self._load_window(ch,save_path,avail,ext)

        def do_export():
            dst=filedialog.asksaveasfilename(title=f"Export — {ch['name']}",
                initialfile=f"{safe}_export.{ext}",defaultextension=f".{ext}",
                filetypes=[("Elden Ring Save","*.sl2 *.co2"),("All files","*.*")])
            if dst: shutil.copy2(save_path,dst); self.status.set(f"✦  Exported to {os.path.basename(dst)}")

        def do_import():
            src=filedialog.askopenfilename(title="Import save file",
                filetypes=[("Elden Ring Save","*.sl2 *.co2"),("All files","*.*")])
            if not src: return
            if not messagebox.askyesno("Confirm Import","This replaces your current save.\nGame must be closed!\nBackup created automatically."): return
            bak=save_path+f".import_bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(save_path,bak); shutil.copy2(src,save_path)
            self.status.set(f"✦  Imported {os.path.basename(src)}")
            messagebox.showinfo("Imported",f"Save imported.\nBackup: {os.path.basename(bak)}")
            self._switch("chars")

        for txt,cmd,bg,hv in [
            ("💾 Save",make_save,GOLD_DIM,GOLD),("📂 Load",load_save,"#2a4a2a",GREEN_OK),
            ("⬆ Export",do_export,"#1a2a3a","#4a7a9b"),("⬇ Import",do_import,"#3a1a3a","#7a4a7a"),
        ]:
            tk.Button(btns,text=txt,command=cmd,bg=bg,fg=TEXT_BRIGHT,activebackground=hv,
                      activeforeground=TEXT_BRIGHT,font=FONT_SMALL,relief="flat",bd=0,
                      padx=8,pady=4,cursor="hand2").pack(side="left",padx=(0,4))

    def _load_window(self,ch,save_path,avail,ext):
        win=tk.Toplevel(self); win.title(f"Load Save — {ch['name']}")
        win.configure(bg=BG_DARK); win.resizable(False,False)
        win.transient(self); win.grab_set()
        W,H=520,360
        def repos(*_):
            mx=self.winfo_x(); my=self.winfo_y()
            mw=self.winfo_width(); mh=self.winfo_height()
            win.geometry(f"{W}x{H}+{mx+(mw-W)//2}+{my+(mh-H)//2}")
        repos(); self.bind("<Configure>",repos)
        win.protocol("WM_DELETE_WINDOW",lambda:(self.unbind("<Configure>"),win.destroy()))
        try:
            dwm=ctypes.WinDLL("dwmapi"); v=ctypes.c_int(1)
            dwm.DwmSetWindowAttribute(win.winfo_id(),20,ctypes.byref(v),ctypes.sizeof(v))
        except: pass
        tk.Label(win,text=f"Select save point for  {ch['name']}",
                 font=FONT_SECTION,bg=BG_DARK,fg=GOLD,pady=10).pack()
        tk.Frame(win,bg=GOLD_DIM,height=1).pack(fill="x",padx=16)
        lbf=tk.Frame(win,bg=BG_DARK); lbf.pack(fill="both",expand=True,padx=16,pady=8)
        lb=tk.Listbox(lbf,bg=BG_PANEL,fg=TEXT_BRIGHT,font=FONT_VALUE,selectbackground=GOLD_DIM,
                      selectforeground=TEXT_BRIGHT,relief="flat",bd=0,activestyle="none")
        lb.pack(fill="both",expand=True)
        fmap={}
        for sf in avail:
            mt=datetime.fromtimestamp(sf.stat().st_mtime).strftime("%Y-%m-%d  %H:%M:%S")
            lbl=f"{sf.stem}   [{mt}]"; lb.insert(tk.END,lbl); fmap[lbl]=sf
        lb.selection_set(0)
        def close(): self.unbind("<Configure>"); win.destroy()
        def do_load():
            sel=lb.curselection()
            if not sel: return
            chosen=list(fmap.values())[sel[0]]
            if not messagebox.askyesno("Confirm Load",f"Replace save with:\n{chosen.name}\n\nGame must be closed!",parent=win): return
            bak=save_path+".editor_bak"; shutil.copy2(save_path,bak); shutil.copy2(str(chosen),save_path)
            self.status.set(f"✦  Loaded: {chosen.name}")
            messagebox.showinfo("Loaded",f"Save loaded.\nBackup: {os.path.basename(bak)}",parent=win); close()
        def do_delete():
            sel=lb.curselection()
            if not sel: return
            chosen=list(fmap.values())[sel[0]]
            if messagebox.askyesno("Delete?",f"Delete:\n{chosen.name}?",parent=win):
                chosen.unlink(); close(); self.status.set("✦  Save point deleted.")
        foot=tk.Frame(win,bg=BG_DARK,pady=8); foot.pack(fill="x",padx=16)
        tk.Button(foot,text="✗  Delete",command=do_delete,bg=RED_ACCENT,fg=TEXT_BRIGHT,
                  activebackground="#b02222",activeforeground=TEXT_BRIGHT,font=FONT_BUTTON,
                  relief="flat",bd=0,padx=12,pady=5,cursor="hand2").pack(side="left")
        tk.Button(foot,text="Cancel",command=close,bg=BG_MID,fg=TEXT_DIM,
                  activebackground=BG_PANEL,activeforeground=TEXT_MAIN,font=FONT_BUTTON,
                  relief="flat",bd=0,padx=12,pady=5,cursor="hand2").pack(side="right",padx=(0,8))
        tk.Button(foot,text="↩  Load Selected",command=do_load,bg=GOLD_DIM,fg=TEXT_BRIGHT,
                  activebackground=GOLD,activeforeground=BG_DARK,font=FONT_BUTTON,
                  relief="flat",bd=0,padx=14,pady=5,cursor="hand2").pack(side="right")

    # ── Option maps ───────────────────────────────────────────────────────
    def _opts(self,s,k):
        m={
            ("Renderer","LatencyReductionMode"):{0:"Off",1:"Enabled",2:"Boost"},
            ("Renderer","GammaLevel"):{0:"0",1:"1",2:"2",3:"3",4:"4",5:"5",6:"6"},
            ("DLSS","DLSSMode"):{0:"Off",1:"Max Performance",2:"Performance",3:"Balanced",4:"Quality",5:"Ultra Quality",6:"DLAA"},
            ("DLSS","DLSSPreset"):{0:"Default",1:"A",2:"B",3:"C",4:"D",5:"E",6:"F",7:"G"},
            ("DLSS","SharpenMode"):{0:"Off",1:"Sharpening"},
            ("DLSS-G","NumGenFrames"):{1:"1",2:"2",3:"3",4:"4"},
            ("FrameGeneration","FrameGenMode"):{0:"Off",1:"DLSS-G",2:"Auto"},
            ("FrameGeneration","GIGlitchMitigation"):{0:"Off",1:"On"},
            ("FSR3U","QualityMode"):{0:"Native AA",1:"Quality",2:"Balanced",3:"Performance",4:"Ultra Performance"},
            ("XESS","QualityMode"):{100:"Ultra Performance",101:"Performance",102:"Balanced",103:"Quality",104:"Ultra Quality",105:"Ultra Quality+",106:"Native AA"},
            ("XESS","SharpenMode"):{0:"Off",1:"Sharpening"},
            ("NIS","ScalingMode"):{0:"Off",1:"NIS"},
            ("Reflex","ReflexMode"):{0:"Off",1:"Enabled",2:"Boost"},
        }
        d=m.get((s,k)); return (d,d) if d else None

    def _range(self,s,k):
        # Fallback range for any floats not covered by ARROW_INT_KEYS
        return (0.0,1.0,0.01)

    def _str_opts(self,s,k):
        return {("Renderer","ScalingMode"):["Native","DLSS","FSR3","XESS","NIS"]}.get((s,k),[])

    def _mark(self):
        if not self._changed:
            self._changed=True; self.status.set("⚠  Unsaved changes — click Save Settings to apply.")

    # ── Save ──────────────────────────────────────────────────────────────
    def _save(self):
        errs=[]
        # ERSS toml
        if self.vars and self.erss_path:
            dm={}
            for lk,v in self.vars.items():
                if isinstance(v,tuple) and len(v)==3 and v[0]=="arrow_float":
                    _,sv,is_frac=v
                    raw=float(sv.get())/100.0 if is_frac else float(sv.get())
                    # Preserve original type: if original was int, save as int
                    orig=self.erss_raw
                    sec_raw=orig if lk[0] is None else orig.get(lk[0],{})
                    orig_val=sec_raw.get(lk[1],raw) if isinstance(sec_raw,dict) else raw
                    dm[lk]=py_to_toml(int(raw) if isinstance(orig_val,int) else raw)
                elif isinstance(v,tuple):
                    sv,od,ld=v; rev={vv:kk for kk,vv in ld.items()}
                    dm[lk]=py_to_toml(rev.get(sv.get(),sv.get()))
                elif isinstance(v,tk.BooleanVar): dm[lk]=py_to_toml(v.get())
                elif isinstance(v,tk.DoubleVar):  dm[lk]=py_to_toml(round(v.get(),4))
                elif isinstance(v,tk.IntVar):     dm[lk]=py_to_toml(v.get())
                elif isinstance(v,tk.StringVar):  dm[lk]=py_to_toml(v.get())
            try: save_toml(self.erss_path,dm)
            except Exception as e: errs.append(f"ERSS: {e}")
        # Game XML
        if self.xml_vars and self.xml_path:
            try: save_xml(self.xml_path,{k:v.get() for k,v in self.xml_vars.items()})
            except Exception as e: errs.append(f"Game XML: {e}")
        # Co-op INI
        if self.coop_vars and self.coop_path and self.coop_cfg:
            for vk,(v,kind,sec,key,*rest) in self.coop_vars.items():
                if kind=="bool":
                    self.coop_cfg.set(sec,key,"1" if v.get() else "0")
                elif kind=="choice":
                    lbl_map=rest[0]; raw=lbl_map.get(v.get(),v.get())
                    self.coop_cfg.set(sec,key,raw)
                elif kind in ("int","text"):
                    self.coop_cfg.set(sec,key,v.get())
            try: save_ini(self.coop_path,self.coop_cfg)
            except Exception as e: errs.append(f"Co-op: {e}")
        if errs:
            messagebox.showerror("Save failed","\n".join(errs)); self.status.set("✘  Save failed.")
        else:
            self._changed=False; self.status.set(f"✦  Saved at {datetime.now().strftime('%H:%M:%S')}")

    def _reload(self):
        self._discover(); self._auto_fps_warn(); self._changed=False
        self._switch(self.active_tab.get()); self.status.set("⟳  Reloaded from disk.")

if __name__=="__main__":
    app=EldenEditor(); app.mainloop()
