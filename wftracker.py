import warnings; warnings.filterwarnings("ignore", message="Pick support for Wedge is missing.")
import os
import re
import sys
import json
import math
import time
import sqlite3
import tempfile
import threading
import webbrowser
from datetime import datetime, timezone
from io import BytesIO
from urllib.parse import quote
import requests
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import sv_ttk
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import mplcursors  # pip install mplcursors
from matplotlib.animation import FuncAnimation
from PIL import Image, ImageTk


# --- KONFIGURATION ---
DB_FILE = "warframe_data.db"
IMAGE_CACHE_DIR = "image_cache" # --- NEU: Ordner für den Bild-Cache
CATEGORIES = ["Gesamtübersicht", "Warframe", "Primary", "Secondary", "Melee", "Amp", "Arch-Gun", "Arch-Melee", "Companion", "Vehicle", "Necramechs", "Star Chart"]
STATUS_OPTIONS = ["Mastered", "Building", "Built", "Leveling", "Missing"]
STATUS_COLORS = {'Mastered': '#a3e6a3', 'Building': '#e6d1a3', 'Built': '#a3d1e6', 'Leveling': '#cda3e6', 'Missing': '#e6a3a3'}
MASTERY_POINTS = {"Warframe": 6000, "Companion": 6000, "Archwing": 6000, "Vehicle": 6000, "Primary": 3000, "Secondary": 3000, "Melee": 3000, "Amp": 3000, "Arch-Gun": 3000, "Arch-Melee": 3000, "Default": 3000}
API_BASE_URL = "https://raw.githubusercontent.com/WFCD/warframe-items/refs/heads/master/data/json"
STATUS_TEXT_COLORS = {
    'Mastered': '#28a745',  # Ein kräftiges Grün
    'Building': '#fd7e14',  # Ein klares Orange
    'Built': '#007bff',     # Ein helles Blau
    'Leveling': '#6f42c1',  # Ein sattes Lila
    'Missing': '#dc3545'   # Ein deutliches Rot
}
NODE_STATUS_TEXT = {0: "Incomplete", 1: "Completed", 2: "Steel Path"}
STATUS_NODE_COLORS = {
    "Completed": "#2a95f5",      # Blau für normalen Abschluss
    "Steel Path": "#e6a3a3",     # Rot für Steel Path
    "Incomplete": "#6c757d"   # Grau
}
# --- Mapping für Mission Types (MT_*) ---
MISSION_TYPE_MAP = {
    "MT_EXTERMINATION": "Extermination",
    "MT_DEFENSE": "Defense",
    "MT_MOBILE_DEFENSE": "Mobile Defense",
    "MT_TERRITORY": "Interception",
    "MT_ASSASSINATION": "Assassination",
    "MT_SURVIVAL": "Survival",
    "MT_RESCUE": "Rescue",
    "MT_SABOTAGE": "Sabotage",
    "MT_CAPTURE": "Capture",
    "MT_SPY": "Spy",
    "MT_HIVE": "Hive",
    "MT_EXCAVATE": "Excavation",
    "MT_ARENA": "Arena",
    "MT_PURSUIT": "Pursuit",
    "MT_INTEL": "Data Retrieval",
    "MT_RACE": "K-Drive Race",
    "MT_ASSAULT": "Assault",
    "MT_DISRUPTION": "Disruption",
    "MT_VOLATILE": "Railjack Volatile",
    "MT_ORPHIX": "Orphix",
    "MT_DEFENSE_ARTIFACT": "Artifact Defense",
}

# --- Mapping für Sortie Modifiers (SORTIE_MODIFIER_*) ---
SORTIE_MODIFIER_MAP = {
    "SORTIE_MODIFIER_ARMOR": "Enhanced Armor",
    "SORTIE_MODIFIER_SHIELDS": "Enhanced Shields",
    "SORTIE_MODIFIER_ENERGY_DRAIN": "Energy Reduction",
    "SORTIE_MODIFIER_LOW_ENERGY": "Low Energy",
    "SORTIE_MODIFIER_EXIMUS": "Eximus Stronghold",
    "SORTIE_MODIFIER_SECONDARY_ONLY": "Secondary Only",
    "SORTIE_MODIFIER_MELEE_ONLY": "Melee Only",
    "SORTIE_MODIFIER_RIFLE_ONLY": "Primary Only",
    "SORTIE_MODIFIER_SHOTGUN_ONLY": "Shotgun Only",
    "SORTIE_MODIFIER_SNIPER_ONLY": "Sniper Only",
    "SORTIE_MODIFIER_HAZARD_FOG": "Fog Hazard",
    "SORTIE_MODIFIER_HAZARD_FIRE": "Fire Hazard",
    "SORTIE_MODIFIER_HAZARD_ICE": "Ice Hazard",
    "SORTIE_MODIFIER_HAZARD_MAGNETIC": "Magnetic Hazard",
    "SORTIE_MODIFIER_HAZARD_TOXIN": "Toxin Hazard",
    "SORTIE_MODIFIER_HAZARD_RADIATION": "Radiation Hazard",
}

# --- VOLLSTÄNDIGE DATEN FÜR DIE PLANETEN-DETAILANSICHT ---
PLANET_DATA = {
    "Mercury": "Der sonnennächste Planet. Die Grineer haben die alten orokinischen Bergbauanlagen übernommen und nutzen sie nun für ihre eigenen Zwecke.",
    "Venus": "Eine gefrorene Welt, auf der die Corpus versuchen, orokinische Technologie aus dem Schnee zu bergen. Die Solaris-Bevölkerung arbeitet unter ihrer Herrschaft in Fortuna.",
    "Earth": "Die Wiege der Menschheit. Die Erde ist jetzt ein üppiger, wilder Dschungel, der von den Grineer patrouilliert wird und die Ebenen von Eidolon beheimatet.",
    "Lua": "Der Mond der Erde, für Jahrhunderte im Void verborgen. Er ist ein zentrales Relikt des Orokin-Reiches und birgt die tiefsten Geheimnisse der Tenno.",
    "Mars": "Eine Wüstenwelt, die als eine der Hauptbasen der Grineer dient. Hier befindet sich auch der Basar von Maroo, ein Treffpunkt für Händler und Tenno.",
    "Phobos": "Der kleinere Mond des Mars, der von den Grineer zu einer stark industrialisierten Werft und einem militärischen Außenposten umfunktioniert wurde.",
    "Deimos": "Der befallene Mond des Mars, ein pulsierender, lebender Organismus. Heimat der Entrati-Familie und des Necralisks.",
    "Ceres": "Ein Zwergplanet, der von den Grineer vollständig in eine gigantische, verschmutzte Schiffswerft und Klonfabrik umgewandelt wurde.",
    "Jupiter": "Ein Gasriese, umgeben von schwebenden Corpus-Gasstädten in der Atmosphäre. Hier führt Alad V seine finsteren Experimente durch.",
    "Europa": "Ein eisiger Mond des Jupiter. Die Corpus unterhalten hier Forschungseinrichtungen, die oft um Orokin-Ruinen herum gebaut sind, die tief im Eis verborgen liegen.",
    "Saturn": "Ein Gasriese, dessen Ringe von Grineer-Galeonen und Asteroidenbasen übersät sind. Das Hauptoperationsgebiet von Councilor Vay Hek.",
    "Uranus": "Ein Ozeanplanet. Tief unter den stürmischen Wellen hat der Grineer-Wissenschaftler Tyl Regor seine Sealabs errichtet, um seine perfekten Grineer-Klone zu züchten.",
    "Neptune": "Ein gefrorener Gasriese, der von den Corpus als wichtiger Knotenpunkt für ihre interplanetaren Handelsrouten genutzt wird. Hier findet auch 'The Index' statt.",
    "Pluto": "Ein Zwergplanet, der als 'Outer Terminus' des Sonnensystems dient. Die Corpus haben hier eine riesige interstellare Relaisstation errichtet.",
    "Eris": "Ein Zwergplanet am Rande des Systems, der nach fehlgeschlagenen Grineer-Kolonisierungsversuchen vollständig von der Infestation überrannt wurde.",
    "Sedna": "Ein Zwergplanet unter der Kontrolle der Grineer. Kela De Thaym veranstaltet hier ihre brutalen Gladiatorenkämpfe in einer riesigen Arena.",
    "Void": "Eine mysteriöse Dimension außerhalb des normalen Raums. Die Orokin-Türme hier bergen die wertvollsten Belohnungen und werden von korrumpierten Einheiten bewacht.",
    "Kuva Fortress": "Das Herz der Macht der Grineer-Königinnen. Eine schwer befestigte Asteroidenfestung, von der aus sie ihr Reich befehligen und den Fluss von Kuva kontrollieren.",
    "Zariman Ten Zero": "Das legendäre Orokin-Kolonieschiff, das im Void verloren ging und nun auf mysteriöse Weise zurückgekehrt ist. Es ist der Ursprungsort der Tenno.",
    "Junctions": "Spektrale Wächter, die den Weg zu neuen Planeten bewachen. Besiege den Wächter, um die nächste Region des Sonnensystems freizuschalten."
}

# --- Textfarben für Item-Seltenheiten im Relic Finder ---
RARITY_TEXT_COLORS = {
    'Common': '#a9a9a9',    # Ein helles Grau (Dimgray) für unauffällige Items
    'Uncommon': '#a3d1e6',  # Dasselbe Blau wie für 'Built' für Konsistenz
    'Rare': '#e6d1a3',      # Dasselbe Gold/Orange wie für 'Building'
    'Legendary': '#e6a3a3' # Dasselbe Rot wie für 'Missing' für sehr seltene Items
}
RESOURCE_TRACKER_CONTAINS_KEYWORDS = {
    'ornament', 'holster', 'stars', 'chain', 'partcore', 'blueprint'
}

# Keywords, die am Ende eines Namens eine Komponente bezeichnen.
# Ein `endswith`-Check ist hier sicherer, um keine echten Ressourcen zu filtern.
RESOURCE_TRACKER_ENDSWITH_KEYWORDS = {
    'barrel', 'receiver', 'stock', 'link', 'handle', 'blade', 'limb', 'disc', 'rivet',
    'guard', 'carapace', 'cerebrum', 'string', 'head', 'motor', 'systems', 'chassis',
    'neuroptics', 'pouch', 'harness', 'wings', 'fuselage', 'engine', 'avionics', 'grip',
    'gauntlet', 'aegis', 'heatsink', 'hilt', 'body', 'bridge', 'fret', 'boot'
}

# Die Whitelist bleibt unverändert.
RESOURCE_TRACKER_EXCLUSION_EXCEPTIONS = {
    'gyromag systems', 'atmos systems', 'repeller systems'
}

def pretty_mission_type(s: str) -> str:
    """Konvertiert 'MT_PVP' zu 'PVP' und macht es hübscher."""
    return s.replace("MT_", "").replace("_", " ").title() if s else "N/A"

def pretty_modifier(s: str) -> str:
    """Entfernt 'MODIFIER_' und macht es hübscher."""
    return s.replace("MODIFIER_", "").replace("_", " ").title() if s else "N/A"
    
def resolve_node_name(conn, node_key: str) -> str:
    """Sucht den Klartextnamen für einen Node-Key wie 'SolNode123' in der DB."""
    if not node_key: return "N/A"
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM nodes WHERE uniqueName = ?", (node_key,))
        res = cur.fetchone()
        return res[0] if res else node_key.replace("SolNode", "Node ")
    except Exception:
        return node_key

def get_planet_image_url(planet_name: str) -> str:
        special_cases = {
            "Kuva Fortress": "Kuva_Fortress",
            "Zariman Ten Zero": "Zariman_Ten_Zero",
            "Junctions": "Junction"
        }
        safe_name = special_cases.get(planet_name, planet_name)
        safe_name = safe_name.replace(" ", "_")  # Leerzeichen durch _
        return f"https://wiki.warframe.com/images/{safe_name}.png"

# --- API DATENIMPORT (ERWEITERT) ---

def determine_app_category(item):
    """
    Bestimmt die korrekte App-Kategorie für ein Item, indem die zuverlässigsten
    Schlüssel wie 'productCategory' und 'uniqueName' priorisiert werden.
    """
    unique_name = item.get('uniqueName', '')
    api_category = item.get('category', '')
    product_category = item.get('productCategory', '') # Der neue, wichtige Schlüssel

    # --- Priorität 1: Eindeutige Erkennung via productCategory ---
    # Dies ist der sicherste Weg, um Amps zu identifizieren.
    if product_category == "OperatorAmps":
        return "Amp"

    # --- Priorität 2: Behandele den Sonderfall "Necramech getarnt als Warframe" ---
    if api_category == "Warframes":
        if "mech" in unique_name.lower():
            return "Necramechs"
        else:
            return "Warframe"
            
    # --- Priorität 3: Prüfe auf andere Fahrzeuge via uniqueName ---
    elif "/hoverboard/" in unique_name.lower():
        return "Vehicle"
        
    # --- Priorität 4: Allgemeines Mapping für alle anderen, eindeutigen Kategorien ---
    else:
        mapping = {
            "Primary": "Primary", "Secondary": "Secondary", "Melee": "Melee",
            "Arch-Gun": "Arch-Gun", "Arch-Melee": "Arch-Melee", "Archwing": "Vehicle",
            "Sentinels": "Companion", "Kubrows": "Companion", "Kavats": "Companion",
            "Moas": "Companion", "Vulpaphyla": "Companion", "Predasites": "Companion",
            "Hounds": "Companion", "Pets": "Companion",
            "K-Drives": "Vehicle",
            "Necramechs": "Necramechs"
            # 'Amp' wird nicht mehr benötigt, da es oben bereits sicher behandelt wird.
        }
        return mapping.get(api_category, None)



# --- NEU: Funktion für den Massen-Download ---
def download_all_images(conn, status_callback):
    cur = conn.cursor()
    cur.execute("SELECT image_name FROM items WHERE image_name != ''")
    image_names = [row[0] for row in cur.fetchall()]
    total = len(image_names)

    for i, name in enumerate(image_names, start=1):
        local_path = os.path.join(IMAGE_CACHE_DIR, name)
        if os.path.exists(local_path):
            continue
        status_callback(f"Lade Bild {i}/{total}: {name}")
        url = f"https://wiki.warframe.com/images/{name}"
        if not download_image_if_missing(url, local_path):
            # Best-effort fallback to CDN naming (if your item images sometimes live here)
            cdn_url = f"https://cdn.warframestat.us/img/{name}"
            download_image_if_missing(cdn_url, local_path)

    status_callback("Download aller Bilder abgeschlossen.")

def download_planet_images(status_callback=None):
    planets = [
        "Mercury","Venus","Earth","Lua","Mars","Phobos","Deimos",
        "Ceres","Jupiter","Europa","Saturn","Uranus","Neptune",
        "Pluto","Eris","Sedna","Void","Kuva Fortress","Zariman Ten Zero","Junctions"
    ]
    special = {"Kuva Fortress":"Kuva_Fortress","Zariman Ten Zero":"Zariman_Ten_Zero","Junctions":"Junction"}

    if status_callback: status_callback("Downloading planet images...")
    total = len(planets)
    for i, planet in enumerate(planets, start=1):
        safe = special.get(planet, planet).replace(" ", "_")
        url = f"https://wiki.warframe.com/images/{safe}.png"
        local_path = os.path.join(IMAGE_CACHE_DIR, f"{safe}.png")
        if os.path.exists(local_path):
            continue
        ok = download_image_if_missing(url, local_path)
        if status_callback:
            if ok: status_callback(f"[{i}/{total}] {planet} downloaded")
            else:  status_callback(f"Failed to download {planet}")
    if status_callback: status_callback("Planet image download complete.")

# Die Signatur wird geändert, um die 'app'-Instanz zu akzeptieren
def populate_database_from_api(app, conn, status_callback):
    API_URL = "https://raw.githubusercontent.com/WFCD/warframe-items/refs/heads/master/data/json/All.json"
    status_callback("Downloading item data from API... (This may take a moment)")
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        all_items = response.json()

        # --- KORREKTUR: Fülle die Namens-Karte in der übergebenen App-Instanz ---
        status_callback("Building complete item name map...")
        # Leere die Karte zuerst, um sicherzustellen, dass sie sauber ist
        app.full_item_name_map.clear() 
        for item in all_items:
            if 'uniqueName' in item and 'name' in item:
                app.full_item_name_map[item['uniqueName']] = item['name']
        
        status_callback("Download complete. Processing and saving to database...")
        
        cursor = conn.cursor()
        items_to_insert = []
        
        for item in all_items:
            # (Der Rest der Funktion bleibt unverändert)
            app_category = determine_app_category(item)
            if not app_category: 
                continue
            if item.get('masterable') is False:
                continue
            if item.get('excludeFromCodex') is True:
                continue

            name = item.get('name')
            unique_name = item.get('uniqueName')
            if not name or not unique_name: 
                continue

            mr = item.get('masteryReq', 0)
            desc = item.get('description', '')
            image_name = item.get('imageName', '')
            build_price = item.get('buildPrice', 0)
            mastery_points = MASTERY_POINTS.get(app_category, MASTERY_POINTS["Default"])
            components_json = json.dumps(item.get('components', []))
            
            items_to_insert.append((name, unique_name, app_category, mr, mastery_points, desc, image_name, components_json, build_price))
        
        cursor.executemany("""
            INSERT OR IGNORE INTO items (name, uniqueName, category, mastery_rank, mastery_points, description, image_name, components, build_price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, items_to_insert)
        
        conn.commit()
        status_callback(f"Database populated with {len(items_to_insert)} items.")
        
    except Exception as e:
        status_callback(f"An unexpected error occurred during import: {e}")
    
def populate_nodes_from_api(conn, status_callback):
    NODE_URL = "https://raw.githubusercontent.com/WFCD/warframe-items/master/data/json/Node.json"
    JUNCTION_MASTERY = 1000
    NODE_MASTERY = 52

    status_callback("Downloading Star Chart data...")
    try:
        response = requests.get(NODE_URL)
        response.raise_for_status()
        all_nodes = response.json()
        status_callback("Download complete. Processing Star Chart...")

        cursor = conn.cursor()
        nodes_to_insert = []

        # nodeType-Werte können je nach Build variieren; diese Kandidaten decken die „Junction“-Fälle ab
        JUNCTION_NODETYPE_CANDIDATES = {7, 8, 9}

        for node in all_nodes:
            # KEIN startswith-Filter mehr – wir kommen ja sowieso aus Node.json
            unique_name = node.get('uniqueName', '')
            name = node.get('name', '')
            system_name = node.get('systemName', '')
            node_type = node.get('nodeType', None)

            # robustes Junction-Matching:
            is_junction = (node_type in JUNCTION_NODETYPE_CANDIDATES) or ('junction' in name.lower())

            mastery = JUNCTION_MASTERY if is_junction else NODE_MASTERY
            steel_path_mastery = mastery

            # Junctions in eine eigene „Planet“-Gruppe legen
            if is_junction:
                system_name = "Junctions"

            if unique_name and name and system_name and node_type is not None:
                nodes_to_insert.append(
                    (unique_name, name, system_name, node_type, mastery, steel_path_mastery)
                )

        cursor.executemany("""
            INSERT OR IGNORE INTO nodes (uniqueName, name, systemName, nodeType, mastery_points, steel_path_mastery_points)
            VALUES (?, ?, ?, ?, ?, ?)
        """, nodes_to_insert)

        conn.commit()
        status_callback(f"Database populated with {len(nodes_to_insert)} Star Chart nodes.")

    except Exception as e:
        status_callback(f"An unexpected error occurred during node import: {e}")

# --- NEUE HILFSFUNKTION FÜR DEN RELIC FINDER ---
def fetch_relic_data_from_official_source(status_callback):
    """
    Holt und verarbeitet Relikt-Daten. Kombiniert die offizielle Drop-Tabelle (für aktive Relikte)
    mit der offiziellen Wiki-Seite (für gevaultete Relikte), um einen 100% korrekten
    Vaulted-Status und eine saubere, duplikatfreie Liste zu garantieren.
    """

def _norm_key(planet: str, node_name: str) -> str:
    """Bildet einen robusten Vergleichsschlüssel (planet::node), alles kleingeschrieben & alphanumerisch."""
    def n(s): 
        return re.sub(r'\W+', '', (s or '').lower())
    return f"{n(planet)}::{n(node_name)}"

def _looks_like_junction(name: str) -> bool:
    return 'junction' in (name or '').lower()

def populate_nodes_mastery_from_public_export(conn, status_callback):
    URL = "https://raw.githubusercontent.com/calamity-inc/warframe-public-export/senpai/ExportRegions_en.json"
    status_callback("Downloading ExportRegions_en.json (mastery values)...")
    try:
        resp = requests.get(URL, headers={'User-Agent': 'WarframeMasteryTrackerApp/1.0'}); resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        status_callback(f"Failed to fetch ExportRegions_en.json: {e}")
        return

    def norm(s): return re.sub(r'\W+', '', (s or '').lower())
    def key_for(planet, node): return f"{norm(planet)}::{norm(node)}"

    cur = conn.cursor()
    # cache existing by our synthetic key
    cur.execute("SELECT uniqueName, systemName, name FROM nodes")
    existing = {}
    for u, sysname, name in cur.fetchall():
        existing[key_for(sysname, name)] = u

    updates, inserts = [], []
    regions = (data or {}).get("Regions", {})
    for planet, robj in regions.items():
        for n in robj.get("nodes", []):
            node_name = n.get("name")
            mv = int(n.get("masteryValue") or 0)
            if not node_name or mv <= 0: 
                continue
            if "junction" in node_name.lower():  # Junctions NICHT hier
                continue

            k = key_for(planet, node_name)
            uid = existing.get(k, f"NODE_EXPORT_{k}")
            if k in existing:
                updates.append((mv, mv, uid))  # normal & steel-path gleich
            else:
                inserts.append((uid, node_name, planet, 0, mv, mv, 0))  # nodeType=0, status=0

    try:
        if inserts:
            cur.executemany(
                "INSERT INTO nodes (uniqueName, name, systemName, nodeType, mastery_points, steel_path_mastery_points, status) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)"
                " ON CONFLICT(uniqueName) DO NOTHING",
                inserts
            )
        if updates:
            cur.executemany(
                "UPDATE nodes SET mastery_points=?, steel_path_mastery_points=? WHERE uniqueName=?",
                updates
            )
        conn.commit()
    except Exception as e:
        status_callback(f"Failed updating node mastery from export: {e}")
        return

    status_callback(f"Mastery synced: {len(updates)} updated, {len(inserts)} inserted.")

# --- UTILS (new) ---
ROTATION_RE = re.compile(r',\s*(Rot(?:ation)?\s+[A-D])\b', re.IGNORECASE)

def run_bg(fn, *args, daemon=True, **kwargs):
    """Run a function in a background thread."""
    t = threading.Thread(target=fn, args=args, kwargs=kwargs, daemon=daemon)
    t.start()
    return t

def clear_tree(tree: ttk.Treeview):
    """Fast clear all rows from a treeview."""
    children = tree.get_children('')
    if children:
        tree.delete(*children)

def set_text(text_widget: tk.Text, value: str):
    """Safely set full text in a disabled Text widget."""
    text_widget.config(state=tk.NORMAL)
    text_widget.delete(1.0, tk.END)
    text_widget.insert(tk.END, value)
    text_widget.config(state=tk.DISABLED)

def safe_get_json(url: str, headers=None, timeout=30):
    """HTTP GET -> JSON with consistent headers and errors handled upstream."""
    headers = headers or {'User-Agent': 'WarframeMasteryTrackerApp/1.0'}
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.json()

def download_image_if_missing(url: str, local_path: str, headers=None, timeout=30):
    """Download image if local file missing; return True if (now) exists."""
    try:
        if os.path.exists(local_path):
            return True
        headers = headers or {'User-Agent': 'WarframeMasteryTrackerApp/1.0'}
        r = requests.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
        os.makedirs(os.path.dirname(local_path) or ".", exist_ok=True)
        with open(local_path, "wb") as f:
            f.write(r.content)
        return True
    except requests.RequestException:
        return False


class ChartImage(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._label = ttk.Label(self)
        self._label.pack(fill=tk.BOTH, expand=True)
        self._photo = None  # keep reference

    def set_png_bytes(self, png_bytes: bytes):
        try:
            img = Image.open(BytesIO(png_bytes))
            # Optional: fit to current size; skip if you want native resolution
            w = max(200, self.winfo_width() or 800)
            h = max(150, self.winfo_height() or 450)
            img.thumbnail((w, h))
            self._photo = ImageTk.PhotoImage(img)
            self._label.config(image=self._photo, text="")
        except Exception as e:
            self._label.config(text=f"Error loading chart image: {e}", image="")

    def set_message(self, text: str):
        self._label.config(text=text, image="")
        self._photo = None


# --- Pie and Bar Chart ---
class ChartMPL(ttk.Frame):
    def __init__(self, parent, with_toolbar=True, **kwargs):
        super().__init__(parent, **kwargs)
        self.fig = Figure(figsize=(5, 3), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.toolbar = None
        if with_toolbar:
            self.toolbar = NavigationToolbar2Tk(self.canvas, self)
            self.toolbar.update()
        self._anim = None
        self._cursor = None

    def clear(self):
        self.ax.clear()
        if self._cursor:
            try:
                self._cursor.remove()  # mplcursors >= 0.5
            except Exception:
                pass
            self._cursor = None

    def draw_pie(self, labels, sizes, theme_dark=False):
        """Donut chart with a styled legend, tooltips, and consistent theme colors."""
        self.clear()
        bg_color = "#2D2D2D" if theme_dark else "white"
        text_color = "white" if theme_dark else "black"
        grid_color = "#555555" if theme_dark else "#cccccc" # For legend border

        colors = [
            '#6c757d' if lbl == 'Missing' else
            '#2a95f5' if lbl == 'Mastered' else
            STATUS_TEXT_COLORS.get(lbl, "#999999")
            for lbl in labels
        ]        
        # We pass labels to the legend, not directly to the pie, for a cleaner look
        wedges, texts, autotexts = self.ax.pie(
            sizes,
            colors=colors,
            wedgeprops=dict(width=0.35, edgecolor=bg_color),
            autopct=lambda p: f"{p:.1f}%" if p >= 5 else "",
            startangle=90,
            pctdistance=0.85,
            textprops={'color': 'white', 'weight': 'bold'} # White text is readable on all colors
        )
        
        self.ax.axis("equal")
        self.fig.patch.set_facecolor(bg_color)
        self.ax.set_facecolor(bg_color)
        
        # --- ADD A STYLED TITLE ---
        self.ax.set_title("Item Status Breakdown", color=text_color, pad=20)

        # --- ADD A STYLED LEGEND (like the bar chart) ---
        legend = self.ax.legend(wedges, labels,
                                title="Status",
                                loc="center left",
                                bbox_to_anchor=(0.95, 0, 0.5, 1)) # Position legend outside
        legend.get_frame().set_facecolor(bg_color)
        legend.get_frame().set_edgecolor(grid_color)
        legend.get_title().set_color(text_color)
        for text in legend.get_texts():
            text.set_color(text_color)
            
        # --- Tooltip code is unchanged, it's already great ---
        if self._cursor:
            self._cursor.remove()
        self._cursor = mplcursors.cursor(wedges, hover=True)
        
        @self._cursor.connect("add")
        def _(sel):
            i = sel.index
            sel.annotation.set_text(f"{labels[i]}: {sizes[i]}")
            sel.annotation.get_bbox_patch().set(facecolor=colors[i], alpha=0.95)
            sel.annotation.arrow_patch.set(arrowstyle="->", facecolor=text_color, ec="none")
            sel.annotation.set_color("white" if theme_dark else 'black')

        self.fig.tight_layout() # Ensure legend and title fit
        self.canvas.draw_idle()


    def draw_bar_animated(self, cats, mastered, remaining, theme_dark=False):
        """Stacked horizontal bar chart with a simple grow animation and improved styling."""
        self.clear()
        bg_color = "#2D2D2D" if theme_dark else "white"
        text_color = "white" if theme_dark else "black"
        grid_color = "#555555" if theme_dark else "#cccccc"
        mastered_color = "#2a95f5" if theme_dark else "#2a95f5"
        remaining_color = '#6c757d'  # A neutral dark gray

        y = list(range(len(cats)))
        
        # Use explicit colors for the bars
        mastered_bars = self.ax.barh(y, [0]*len(cats), color=mastered_color, label="Mastered XP")
        remaining_bars = self.ax.barh(y, [0]*len(cats), left=[0]*len(cats), color=remaining_color, label="Remaining XP")

        # --- Style Axes, Ticks, and Spines ---
        self.ax.set_yticks(y, labels=cats)
        self.ax.invert_yaxis()
        self.ax.tick_params(axis='y', colors=text_color, length=0) # No tick lines on y-axis
        self.ax.tick_params(axis='x', colors=text_color)
        
        # Hide top and right borders for a cleaner look
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['left'].set_color(grid_color)
        self.ax.spines['bottom'].set_color(grid_color)

        # --- Style Figure and Background ---
        self.fig.patch.set_facecolor(bg_color)
        self.ax.set_facecolor(bg_color)

        # --- Add a subtle grid ---
        self.ax.xaxis.grid(True, linestyle='--', alpha=0.6, color=grid_color)
        self.ax.set_axisbelow(True) # Ensure grid is behind the bars

        # --- Style the Legend ---
        legend = self.ax.legend(loc="lower right")
        legend.get_frame().set_facecolor(bg_color)
        legend.get_frame().set_edgecolor(grid_color)
        for text in legend.get_texts():
            text.set_color(text_color)

        max_x = max((m+r) for m, r in zip(mastered, remaining)) or 1
        self.ax.set_xlim(0, max_x * 1.05)

        # --- IMPROVED Hover Tooltips ---
        if self._cursor:
            self._cursor.remove()
        all_rects = list(mastered_bars) + list(remaining_bars)
        self._cursor = mplcursors.cursor(all_rects, hover=True)
        
        @self._cursor.connect("add")
        def _(sel):
            rect = sel.artist
            width = rect.get_width()
            
            is_mastered = (rect in mastered_bars)
            lbl = "Mastered XP" if is_mastered else "Remaining XP"
            bar_color = mastered_color if is_mastered else remaining_color

            sel.annotation.set_text(f"{lbl}: {int(width):,}")
            
            # Style the annotation box like we did for the pie chart
            sel.annotation.get_bbox_patch().set(facecolor=bar_color, alpha=0.95)
            sel.annotation.arrow_patch.set(arrowstyle="->", facecolor=text_color, ec="none")
            sel.annotation.set_color("white" if theme_dark else "black")


        # --- Animation (Unchanged) ---
        steps = 30
        def interp(step, target):
            return [t * step/steps for t in target]

        def update(frame):
            cur_mastered = interp(frame, mastered)
            cur_remaining = interp(frame, remaining)
            for i, w in enumerate(cur_mastered):
                mastered_bars[i].set_width(w)
            for i, w in enumerate(cur_remaining):
                remaining_bars[i].set_x(cur_mastered[i])
                remaining_bars[i].set_width(w)
            return (*mastered_bars, *remaining_bars)

        self.fig.tight_layout() # Adjust layout to prevent labels from being cut off
        self._anim = FuncAnimation(self.fig, update, frames=steps, interval=16, blit=False, repeat=False)
        self.canvas.draw_idle()


# DetailPanel-KLASSE
class DetailPanel(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding="10")
        self.app = app
        self.image_cache = {}
        self.current_drops = []
        self.drops_sort_column = 'chance'
        self.drops_sort_reverse = True

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.name_label = ttk.Label(
            self, text="Item Details",
            font=self.app.font_header, anchor="center"
        )
        self.name_label.grid(row=0, column=0, pady=(0, 10), sticky="ew")

        # Notebook (tabs)
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=1, column=0, sticky="nsew")

        # --- Tab 1: Overview ---
        overview_tab = ttk.Frame(self.notebook, padding="5")
        overview_tab.columnconfigure(0, weight=1)

        self.image_label = ttk.Label(overview_tab)
        self.image_label.grid(row=0, column=0, pady=10)

        self.description_text = tk.Text(
            overview_tab, wrap=tk.WORD, height=8
        )
        self.description_text.grid(row=1, column=0, sticky="nsew")

        self.notebook.add(overview_tab, text="Overview")

        # --- Tab 2: Crafting & Locations ---
        self.crafting_tab = ttk.Frame(self.notebook, padding="5")
        self.crafting_tab.columnconfigure(0, weight=1)
        self.crafting_tab.rowconfigure(3, weight=1)

        # Components
        self.components_frame = ttk.LabelFrame(
            self.crafting_tab, text="Required Components", padding="5"
        )
        self.components_frame.grid(row=0, column=0, sticky="ew")

        self.components_tree = ttk.Treeview(
            self.components_frame,
            columns=('name', 'count'),
            show='headings', height=4
        )
        self.components_tree.heading('name', text='Component')
        self.components_tree.heading('count', text='Count')
        self.components_tree.column('name', width=200)
        self.components_tree.column('count', width=50, anchor=tk.CENTER)
        self.components_tree.pack(fill=tk.BOTH, expand=True)

        self.components_tree.bind("<<TreeviewSelect>>", self.on_component_select)
        self._setup_components_context_menu()
        self.components_tree.bind("<Button-3>", self._show_components_context_menu)

        # Drops filters
        drops_filter_frame = ttk.LabelFrame(
            self.crafting_tab, text="Filter & Sort Drop Locations", padding=5
        )
        drops_filter_frame.grid(row=1, column=0, sticky="ew", pady=(10, 5))

        filter_row1 = ttk.Frame(drops_filter_frame); filter_row1.pack(fill=tk.X, expand=True)
        filter_row2 = ttk.Frame(drops_filter_frame); filter_row2.pack(fill=tk.X, expand=True, pady=(5,0))

        self.drop_place_filter_var = tk.StringVar()
        self.drop_type_filter_var = tk.StringVar()
        self.drop_rarity_filter_var = tk.StringVar()

        ttk.Label(filter_row1, text="Location:").pack(side=tk.LEFT, padx=(0,5))
        ttk.Entry(filter_row1, textvariable=self.drop_place_filter_var).pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Label(filter_row2, text="Type:").pack(side=tk.LEFT, padx=(0,5))
        self.type_combo = ttk.Combobox(
            filter_row2, textvariable=self.drop_type_filter_var,
            values=["All", "Relic", "Bounty", "Mission Reward", "Container Drop", "Enemy Drop"],
            state="readonly"
        )
        self.type_combo.pack(side=tk.LEFT, padx=(0,10), fill=tk.X, expand=True)

        ttk.Label(filter_row2, text="Rarity:").pack(side=tk.LEFT, padx=5)
        self.rarity_combo = ttk.Combobox(
            filter_row2, textvariable=self.drop_rarity_filter_var,
            values=["All", "Common", "Uncommon", "Rare", "Legendary"],
            state="readonly"
        )
        self.rarity_combo.pack(side=tk.LEFT, padx=0, fill=tk.X, expand=True)

        self.type_combo.set("All")
        self.rarity_combo.set("All")

        self.drop_place_filter_var.trace_add("write", self._apply_drop_filters)
        self.drop_type_filter_var.trace_add("write", self._apply_drop_filters)
        self.drop_rarity_filter_var.trace_add("write", self._apply_drop_filters)

        # Drops list
        self.drops_frame = ttk.LabelFrame(
            self.crafting_tab, text="Drop Locations", padding="5"
        )
        self.drops_frame.grid(row=2, column=0, sticky="nsew")

        self.drops_tree = ttk.Treeview(
            self.drops_frame,
            columns=('place', 'type', 'rotation', 'chance'),
            show='headings', height=8
        )
        self.drops_tree.heading('place', text='Location', command=lambda: self.sort_drops_column('place'))
        self.drops_tree.heading('type', text='Type', command=lambda: self.sort_drops_column('type'))
        self.drops_tree.heading('rotation', text='Rotation', command=lambda: self.sort_drops_column('rotation'))
        self.drops_tree.heading('chance', text='Chance', command=lambda: self.sort_drops_column('chance'))
        self.drops_tree.column('place', width=220)
        self.drops_tree.column('type', width=120, anchor=tk.CENTER)
        self.drops_tree.column('rotation', width=80, anchor=tk.CENTER)
        self.drops_tree.column('chance', width=70, anchor=tk.E)
        self.drops_tree.pack(fill=tk.BOTH, expand=True)

        self._setup_drops_context_menu()
        self.drops_tree.bind("<Button-3>", self._show_drops_context_menu)

        # Add Crafting tab initially
        self.notebook.add(self.crafting_tab, text="Crafting & Locations")

        self.clear_panel()

    # -------------------------------
    # Tab visibility helpers
    # -------------------------------
    def hide_crafting_tab(self):
        """Hides the 'Crafting & Locations' tab from the notebook."""
        try:
            for tab_id in self.notebook.tabs():
                if self.nametowidget(tab_id) is self.crafting_tab:
                    self.notebook.forget(tab_id)
                    break
        except Exception:
            pass

    def show_crafting_tab(self):
        """Shows the 'Crafting & Locations' tab again if hidden."""
        try:
            existing_tabs = [self.nametowidget(t) for t in self.notebook.tabs()]
            if self.crafting_tab not in existing_tabs:
                self.notebook.add(self.crafting_tab, text="Crafting & Locations")
        except Exception:
            pass

    # -------------------------------
    # Updating panel
    # -------------------------------

    def update_with_item(self, data):
        # --- Star Chart node selected ---
        if isinstance(data, (list, tuple)):
            # (This part is already correct and remains unchanged)
            planet_name, node_name, status = data
            self.name_label.config(text=f"{node_name} ({planet_name})")
            # ... etc.
            return

        # --- Normal item selected ---
        
        # --- KORREKTUR TEIL 1: Name bereinigen und korrekt verwenden ---
        display_name = str(data)              # Originalname für die Anzeige, z.B. "Lex *"
        clean_name = display_name.strip(" *") # Bereinigter Name für Datenabfragen, z.B. "Lex"
        
        cursor = self.app.conn.cursor()
        # Verwende den bereinigten Namen für die Datenbankabfrage
        cursor.execute("SELECT description, image_name, components FROM items WHERE name = ?", (clean_name,))
        result = cursor.fetchone()
        
        if not result: 
            self.clear_panel()
            return
            
        description, image_name, components_json = result
        
        # Verwende den Originalnamen für die Anzeige im Titel
        self.name_label.config(text=display_name)
        
        set_text(self.description_text, description)
        
        # Der Rest der Funktion (Komponenten laden, etc.) funktioniert jetzt,
        # weil die DB-Abfrage erfolgreich war.
        self.show_crafting_tab()
        clear_tree(self.components_tree)
        components = json.loads(components_json or "[]")
        for comp in components:
            self.components_tree.insert('', tk.END, values=(comp.get('name', '—'), comp.get('itemCount', 0)))
            
        clear_tree(self.drops_tree)
        self.drops_tree.insert('', tk.END, values=("Select a component above", "", "", ""))
        
        self.load_image(image_name)
        self.notebook.select(0)
        self.clear_filters()


    def _setup_components_context_menu(self):
        self.components_context_menu = tk.Menu(self, tearoff=0)
        self.components_context_menu.add_command(
            label="Open in Wiki",
            command=self._open_wiki_for_component
        )
        self.components_context_menu.add_command(
            label="Show in Resource Tracker",
            command=self._show_in_resource_tracker
        )

    
    def _on_find_component_drops(self):
        """Manually trigger drop search for the selected component (from context menu)."""
        selected_item_id = self.components_tree.focus()
        if not selected_item_id:
            return
        # Reuse the same logic as when double-clicking/selection
        self.on_component_select(None)

    def _show_in_resource_tracker(self):
        """Open selected resource directly in Resource Tracker tab."""
        selected = self.components_tree.selection()
        if not selected:
            return
        comp_name = self.components_tree.item(selected[0], "values")[0]
        if not comp_name or comp_name == "Not applicable":
            return

        # switch to Resource Tracker tab
        self.app.notebook.select(self.app.resource_tracker_tab)

        # set search filter
        self.app.resource_tracker_tab.search_var.set(comp_name)


    def _show_components_context_menu(self, event):
        item_id = self.components_tree.identify_row(event.y)
        if item_id:
            self.components_tree.selection_set(item_id)
            self.components_tree.focus(item_id)
            self.components_context_menu.post(event.x_root, event.y_root)

    def _open_wiki_for_component(self):
        selected_item_id = self.components_tree.focus()
        if not selected_item_id: return
        component_name = self.components_tree.item(selected_item_id, 'values')[0]
        formatted_name = quote(component_name.replace(' ', '_'))
        url = f"https://wiki.warframe.com/w/{formatted_name}"
        webbrowser.open_new_tab(url)
        self.app.update_status_bar(f"Opening wiki for {component_name}...")

    def on_component_select(self, event):
        selected_item_id = self.components_tree.focus()
        if not selected_item_id: return
        
        # --- KORREKTUR TEIL 2: Bereinige den Namen aus dem Titel-Label ---
        display_name = self.name_label.cget("text")
        main_item_name = display_name.strip(" *") # Bereinige das Sternchen
        
        component_name = self.components_tree.item(selected_item_id, 'values')[0]
        specific_keywords = ["Blueprint", "Chassis", "Neuroptics", "Systems", "Barrel", "Receiver", "Stock", "Handle", "Heatsink", "Guard", "Blade", "Link", "Pouch", "Head", "Carapace", "Cerebrum"]
        is_specific_part = any(keyword in component_name for keyword in specific_keywords)
        
        # Verwende den bereinigten Namen, um den Suchbegriff zu erstellen
        search_term = f"{main_item_name} {component_name}" if is_specific_part else component_name
        
        self.load_drop_locations(search_term)


    def load_drop_locations(self, search_term):
        self.clear_filters()
        clear_tree(self.drops_tree)
        self.drops_tree.insert('', tk.END, values=(f"Searching for '{search_term}'...", "", "", ""))
        self.notebook.select(1)

        def _fetch_drops():
            try:
                url = f"https://api.warframestat.us/drops/search/{search_term.replace(' ', '%20')}"
                self.current_drops = safe_get_json(url)
                self.app.root.after(0, self._apply_drop_filters)
            except Exception:
                self.app.root.after(0, lambda: self._populate_drops_tree([]))

        run_bg(_fetch_drops)


    def _apply_drop_filters(self, *args):
        place_filter = self.drop_place_filter_var.get().lower()
        type_filter = self.drop_type_filter_var.get()
        rarity_filter = self.drop_rarity_filter_var.get()

        filtered = self.current_drops
        if place_filter:
            filtered = [d for d in filtered if place_filter in d.get('place', '').lower()]
        if type_filter != "All":
            filtered = [d for d in filtered if self._get_drop_type(d.get('place', '')) == type_filter]
        if rarity_filter != "All":
            filtered = [d for d in filtered if d.get('rarity') == rarity_filter]

        self._populate_drops_tree(filtered)


    def sort_drops_column(self, col):
        items = [(self.drops_tree.set(k, col), k) for k in self.drops_tree.get_children('')]
        if col == self.drops_sort_column:
            self.drops_sort_reverse = not self.drops_sort_reverse
        else:
            self.drops_sort_column, self.drops_sort_reverse = col, False

        if col == 'chance':
            def key(x):
                try:
                    return float(str(x[0]).replace('%', '') or 0)
                except Exception:
                    return 0.0
        else:
            key = lambda x: str(x[0]).lower()

        items.sort(key=key, reverse=self.drops_sort_reverse)
        for idx, (_, iid) in enumerate(items):
            self.drops_tree.move(iid, '', idx)


    def _get_drop_type(self, place_string):
        place_lower = place_string.lower()
        
        # --- FINALE LOGIK: Priorisierte Erkennung aller Drop-Typen ---
        
        # 1. Relikte sind immer eindeutig.
        if "relic" in place_lower: 
            return "Relic"

        # 2. NEU: Wenn "bounty" im Ort steht, ist es eine Kopfgeld-Belohnung.
        if "bounty" in place_lower:
            return "Bounty"
            
        # 3. Wenn "caches" erwähnt wird, ist es ein Container Drop.
        if "caches" in place_lower:
            return "Container Drop"
            
        # 4. Bisherige Prüfung für klassische Mission Rewards (Rotationen, Tiers, etc.)
        if "rotation" in place_lower or "rot " in place_lower or "tier " in place_lower: 
            return "Mission Reward"
            
        # 5. Fallback: Wenn nichts anderes zutrifft, ist es ein Enemy Drop.
        return "Enemy Drop"

    def _populate_drops_tree(self, drop_data):
        clear_tree(self.drops_tree)
        if not drop_data:
            self.drops_tree.insert('', tk.END, values=("No results for filter.", "", "", ""))
            return

        added = 0
        for drop in drop_data:
            place = drop.get('place', '')
            if any(tag in place for tag in ("(Exceptional)", "(Flawless)", "(Radiant)")):
                continue

            display_location = place.replace(" (Intact)", "")
            rotation_text = "-"
            m = ROTATION_RE.search(display_location)
            if m:
                rotation_text = m.group(1)
                display_location = display_location[:m.start()].strip()

            drop_type = self._get_drop_type(place)
            chance_percent = f"{float(drop.get('chance', 0)):.2f}%"
            self.drops_tree.insert('', tk.END, values=(display_location, drop_type, rotation_text, chance_percent))
            added += 1

        if added == 0:
            self.drops_tree.insert('', tk.END, values=("No Intact relics found.", "", "", ""))

    def load_image(self, image_name):
        if not image_name:
            self.image_label.config(image=None)
            return

        if image_name in self.image_cache:
            self.image_label.config(image=self.image_cache[image_name])
            return

        local_path = os.path.join(IMAGE_CACHE_DIR, image_name)

        def _finish_load(path):
            try:
                img = Image.open(path)
                img.thumbnail((256, 256))
                photo = ImageTk.PhotoImage(img)
                self.image_cache[image_name] = photo
                self.image_label.config(image=photo)
            except Exception:
                pass

        if os.path.exists(local_path):
            _finish_load(local_path)
            return

        def _fetch_and_save():
            # try CDN first, fallback to wiki
            cdn_url = f"https://cdn.warframestat.us/img/{image_name}"
            wiki_url = f"https://wiki.warframe.com/images/{image_name}"
            if not download_image_if_missing(cdn_url, local_path):
                download_image_if_missing(wiki_url, local_path)
            self.app.root.after(0, lambda: _finish_load(local_path) if os.path.exists(local_path) else None)

        run_bg(_fetch_and_save)
        
    def clear_filters(self):
        self.drop_place_filter_var.set(""); self.type_combo.set("All"); self.rarity_combo.set("All")

    def _set_description(self, text: str):
        set_text(self.description_text, text)

    def clear_panel(self):
        self.name_label.config(text="Select an item from the list")
        self._set_description("Details about the selected item will be shown here.")
        clear_tree(self.components_tree)
        clear_tree(self.drops_tree)
        self.image_label.config(image=None)
        self.clear_filters()

    
    def _setup_drops_context_menu(self):
            self.drops_context_menu = tk.Menu(self, tearoff=0)
            self.drops_context_menu.add_command(label="Show in Relic Finder", command=self._show_relic_in_finder)
            self.drops_context_menu.add_separator()
            self.drops_context_menu.add_command(label="Open Source in Wiki", command=self._open_wiki_for_drop)

    def _show_drops_context_menu(self, event):
        item_id = self.drops_tree.identify_row(event.y)
        if item_id:
            item_values = self.drops_tree.item(item_id, 'values')
            self.drops_tree.selection_set(item_id)
            self.drops_tree.focus(item_id)
            is_relic = "Relic" in item_values[1]  
            if is_relic:
                self.drops_context_menu.entryconfig("Show in Relic Finder", state="normal")
            else:
                self.drops_context_menu.entryconfig("Show in Relic Finder", state="disabled")
            self.drops_context_menu.post(event.x_root, event.y_root)

    def _open_wiki_for_drop(self):
        selected_item_id = self.drops_tree.focus()
        if not selected_item_id: return
        item_values = self.drops_tree.item(selected_item_id, 'values')
        place_string = item_values[0]
        drop_type = item_values[1]
        name_for_wiki = place_string
        if "Relic" in drop_type:  
            match = re.search(r'(Axi|Lith|Meso|Neo|Requiem)\s[A-Z0-9]+', place_string)
            if match:
                name_for_wiki = match.group(0)
        formatted_name = quote(name_for_wiki.replace(' ', '_'))
        url = f"https://wiki.warframe.com/w/{formatted_name}"
        webbrowser.open_new_tab(url)
        self.app.update_status_bar(f"Opening wiki for drop source: {name_for_wiki}...")

    def _show_relic_in_finder(self):
        selected_item_id = self.drops_tree.focus()
        if not selected_item_id: return
        item_values = self.drops_tree.item(selected_item_id, 'values')
        place_string = item_values[0]
        match = re.search(r'(Axi|Lith|Meso|Neo|Requiem)\s[A-Z0-9]+', place_string)
        if not match: return
        relic_name = match.group(0)
        self.app.notebook.select(self.app.relic_finder_tab)
        self.app.relic_finder_tab.search_and_select_relic(relic_name)


 # DASHBOARD 
class DashboardTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding="10")
        self.app = app
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # --- Top frame for Mastery and controls ---
        top_frame = ttk.Frame(self)
        top_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # --- Mastery Rank Display ---
        mastery_frame = ttk.LabelFrame(top_frame, text="Mastery Rank", padding="15")
        mastery_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        mastery_frame.columnconfigure(0, weight=1)
        self.mr_label = ttk.Label(mastery_frame, text="Calculating...", font=("Segoe UI Semibold", 28), anchor="center")
        self.mr_label.grid(row=0, column=0, sticky="ew")
        self.xp_progress = ttk.Progressbar(mastery_frame, orient="horizontal", mode="determinate")
        self.xp_progress.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        self.xp_label = ttk.Label(mastery_frame, text="XP: 0 / 2,500", anchor="center")
        self.xp_label.grid(row=2, column=0, sticky="ew")

        # --- Controls Frame ---
        controls_frame = ttk.LabelFrame(top_frame, text="Controls", padding="15")
        controls_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(5, 0))
        self.refresh_button = ttk.Button(controls_frame, text="Refresh Charts", command=self.update_charts)
        self.refresh_button.pack(expand=True, fill=tk.BOTH)

        # --- Chart area using a PanedWindow ---
        chart_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        chart_pane.grid(row=1, column=0, sticky="nsew")

        # Pie Chart
        pie_frame = ttk.LabelFrame(chart_pane, text="Overall Item Status", padding=5)
        self.pie_chart_view = ChartMPL(pie_frame, with_toolbar=False) # <-- ADD THIS
        self.pie_chart_view.pack(fill=tk.BOTH, expand=True)
        chart_pane.add(pie_frame, weight=1)

        # Bar Chart
        bar_frame = ttk.LabelFrame(chart_pane, text="Mastery Progress by Category", padding=5)
        self.bar_chart_view = ChartMPL(bar_frame, with_toolbar=False) # <-- AND ADD THIS
        self.bar_chart_view.pack(fill=tk.BOTH, expand=True)
        chart_pane.add(bar_frame, weight=2)

    def get_plotly_theme(self):
        return "plotly_dark" if sv_ttk.get_theme() == "dark" else "plotly_white"

    def update_display(self):
        self.update_mastery_rank()
        self.update_charts()

    def update_mastery_rank(self):
            total_xp = self.app.calculate_total_xp() or 0

            # Korrekte und robuste Logik zur MR-Berechnung
            mr = int(math.sqrt(total_xp / 2500)) if total_xp < 2250000 else 30 + int((total_xp - 2250000) / 147500)
            xp_for_current_mr = (2500 * mr**2) if mr <= 30 else (2250000 + (mr - 30) * 147500)
            xp_for_next_mr = (2500 * (mr + 1)**2) if mr < 30 else (xp_for_current_mr + 147500)
            
            # Diese Zeilen verhindern negative Werte und Division durch Null
            xp_in_current_rank = max(0, total_xp - xp_for_current_mr)
            xp_needed_for_next_rank = max(1, xp_for_next_mr - xp_for_current_mr)

            self.mr_label.config(text=f"Mastery Rank {mr}")
            # Verbessertes Label, das sowohl Gesamt-XP als auch den Fortschritt anzeigt
            self.xp_label.config(text=f"Total XP: {int(total_xp):,}   |   Rank Progress: {int(xp_in_current_rank):,} / {int(xp_needed_for_next_rank):,}")
            
            self.xp_progress['maximum'] = xp_needed_for_next_rank
            self.xp_progress['value'] = xp_in_current_rank



    def update_charts(self):
        self.refresh_button.config(state="disabled")
        self.app.update_status_bar("Generating dashboard charts...")

        # MAIN THREAD: safe to query Tk/SV-TTK here
        theme_dark = (sv_ttk.get_theme() == "dark")

        # Start worker with only plain data (no Tk calls inside)
        threading.Thread(target=self._worker_collect_chart_data, args=(theme_dark,), daemon=True).start()

    def _worker_collect_chart_data(self, theme_dark: bool):
            # compute DB aggregates only; NO Tk calls here
            status_counts = self.app.get_status_counts("Gesamtübersicht") or {}
            labels, sizes = [], []
            for key in STATUS_OPTIONS:
                v = status_counts.get(key, 0) or 0
                if v > 0:
                    labels.append(key); sizes.append(v)

            # Die Kategorienliste wird nun dynamisch erstellt
            categories = [c for c in CATEGORIES if c not in ["Gesamtübersicht"]]
            cats, mastered_vals, remaining_vals = [], [], []
            cursor = self.app.conn.cursor()
            
            for cat in categories:
                total = 0
                mastered = 0
                
                if cat == "Star Chart":
                    # --- LOGIK FÜR STAR CHART ---
                    # "Mastered" XP ist die Summe aus Normal + Steel Path
                    cursor.execute("SELECT SUM(mastery_points) FROM nodes WHERE status >= 1")
                    normal_xp = cursor.fetchone()[0] or 0
                    cursor.execute("SELECT SUM(steel_path_mastery_points) FROM nodes WHERE status >= 2")
                    steel_path_xp = cursor.fetchone()[0] or 0
                    mastered = normal_xp + steel_path_xp

                    # "Total" XP ist die Summe aller möglichen Punkte
                    cursor.execute("SELECT COALESCE(SUM(mastery_points),0) + COALESCE(SUM(steel_path_mastery_points),0) FROM nodes")
                    total = cursor.fetchone()[0] or 0
                else:
                    # --- LOGIK FÜR ITEMS (wie bisher) ---
                    cursor.execute("SELECT SUM(mastery_points) FROM items WHERE category = ?", (cat,))
                    total = cursor.fetchone()[0] or 0
                    cursor.execute("SELECT SUM(mastery_points) FROM items WHERE category = ? AND status = 'Mastered'", (cat,))
                    mastered = cursor.fetchone()[0] or 0

                if total > 0:
                    cats.append(cat)
                    mastered_vals.append(mastered)
                    remaining_vals.append(max(0, total - mastered))

            # hop back to UI thread to render
            self.app.root.after(
                0,
                self._finalize_chart_update,
                labels, sizes, cats, mastered_vals, remaining_vals, theme_dark
            )

    def _finalize_chart_update(self, labels, sizes, cats, mastered, remaining, theme_dark):
        if labels and sizes:
            self.pie_chart_view.draw_pie(labels, sizes, theme_dark)
        else:
            self.pie_chart_view.clear()
            self.pie_chart_view.ax.text(0.5, 0.5, "No status data.", ha="center", va="center")
            self.pie_chart_view.canvas.draw_idle()

        if cats and (any(mastered) or any(remaining)):
            self.bar_chart_view.draw_bar_animated(cats, mastered, remaining, theme_dark)
        else:
            self.bar_chart_view.clear()
            self.bar_chart_view.ax.text(0.5, 0.5, "No progress data.", ha="center", va="center")
            self.bar_chart_view.canvas.draw_idle()

        self.refresh_button.config(state="normal")
        self.app.update_status_bar("Dashboard updated.")


class ChartWebView(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.view = WebView2(self, width=300, height=200)
        self.view.pack(fill=tk.BOTH, expand=True)
        self._initialized = False
        self.view.bind("<<WebView2Ready>>", self._on_ready)

    def _on_ready(self, _=None):
        self._initialized = True

    def load_html(self, html: str):
        if not self._initialized:
            self.after(50, lambda: self.load_html(html))
            return
        path = os.path.join(tempfile.gettempdir(), f"chart_{id(self)}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        self.view.Navigate(f"file:///{path.replace('\\','/')}")


# "MasteryTrackerTab"-KLASSE
class MasteryTrackerTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.current_category = "Gesamtübersicht"
        self.status_counts = {}

        # Sorting and filter variables
        self.sort_column = "name"
        self.sort_reverse = False
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.apply_filters)
        self.hide_mastered_var = tk.BooleanVar(value=False)
        self.hide_primes_var = tk.BooleanVar(value=False)

        # Layout
        self.paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left_frame = ttk.Frame(self.paned_window, width=650)
        left_frame.columnconfigure(1, weight=1)
        left_frame.rowconfigure(1, weight=1)
        self.paned_window.add(left_frame)

        self.detail_panel = DetailPanel(self.paned_window, self.app)
        self.paned_window.add(self.detail_panel)

        self.category_frame = ttk.LabelFrame(left_frame, text="Categories", padding="10")
        self.category_frame.grid(row=0, column=0, rowspan=3, sticky="ns", pady=(5,0))


        # 1. Create Frame
        filter_frame = ttk.LabelFrame(left_frame, text="Filter & Search", padding=10)
        filter_frame.grid(row=0, column=1, sticky="ew", pady=(5,0), padx=(10,0))

        # 2. Add Search
        ttk.Label(filter_frame, text="Search:").pack(side=tk.LEFT, padx=(0,5))
        ttk.Entry(filter_frame, textvariable=self.search_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # 3. Create Checkbuttons
        self.hide_mastered_checkbutton = ttk.Checkbutton(filter_frame, text="Hide Mastered", variable=self.hide_mastered_var, command=self.apply_filters)
        self.hide_mastered_checkbutton.pack(side=tk.LEFT, padx=5)

        self.hide_primes_checkbutton = ttk.Checkbutton(filter_frame, text="Hide Primes", variable=self.hide_primes_var, command=self.apply_filters)
        self.hide_primes_checkbutton.pack(side=tk.LEFT, padx=5)

        self.item_frame = ttk.LabelFrame(left_frame, text="Items")
        self.item_frame.grid(row=1, column=1, sticky="nsew", pady=(5,0), padx=(10,0))
        
        self.summary_frame = ttk.LabelFrame(left_frame, text="Progress", padding="10")
        self.summary_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10,0))
        
        # Initialize widgets
        self.create_category_buttons()
        self.create_item_treeview()
        self.create_summary_display()
        self.setup_context_menu()
        self.handle_category_click("Gesamtübersicht") # Set initial view

    # -------------------------------
    # Category switching
    # -------------------------------
    def handle_category_click(self, category):
        self.current_category = category

        if category == "Star Chart":
            # Hide Crafting tab + irrelevant checkboxes
            self.detail_panel.hide_crafting_tab()
            self.hide_mastered_checkbutton.pack_forget()
            self.hide_primes_checkbutton.pack_forget()
        else:
            # Show Crafting tab + filters
            self.detail_panel.show_crafting_tab()
            self.hide_mastered_checkbutton.pack(side=tk.LEFT, padx=5)
            self.hide_primes_checkbutton.pack(side=tk.LEFT, padx=5)

        self.display_items(self.current_category)
        self.update_summary_display()
        self.detail_panel.clear_panel()

    # -------------------------------
    # Treeview helpers
    # -------------------------------
    def _select_all(self, event=None):
        all_item_ids = self.tree.get_children('')
        if all_item_ids:
            self.tree.selection_set(all_item_ids)
        return "break"

    def _copy_selection(self, event=None):
        selected_ids = self.tree.selection()
        if not selected_ids:
            return "break"

        if self.current_category == "Star Chart":
            names_to_copy = [self.tree.item(item_id, 'values')[1] for item_id in selected_ids]
        else:
            names_to_copy = [self.tree.item(item_id, 'values')[0] for item_id in selected_ids]

        copy_text = "\n".join(names_to_copy)
        self.app.root.clipboard_clear()
        self.app.root.clipboard_append(copy_text)

        count = len(names_to_copy)
        item_text = "Item" if count == 1 else "Items"
        self.app.update_status_bar(f"Copied {count} {item_text} to clipboard.")  
        
        return "break"

    def _treeview_sort_column(self, tree, col, reverse):
        self.sort_column = col
        self.sort_reverse = reverse
        l = [(tree.set(k, col), k) for k in tree.get_children("")]
        try:
            l.sort(key=lambda t: int(str(t[0]).replace(",", "")), reverse=reverse)
        except ValueError:
            l.sort(key=lambda t: str(t[0]).lower(), reverse=reverse)
        for index, (val, k) in enumerate(l):
            tree.move(k, "", index)
        tree.heading(col, command=lambda: self._treeview_sort_column(tree, col, not reverse))

    
    # -------------------------------
    # Filtering / Display
    # -------------------------------
    def apply_filters(self, *args):
        self.display_items(self.current_category)

    def display_items(self, category):
        clear_tree(self.tree)
        self.detail_panel.clear_panel()
        cursor = self.app.conn.cursor()
        
        if category == "Star Chart":
            cols = ('system', 'name', 'status')
            self.tree.config(columns=cols)
            for col in cols:
                self.tree.heading(col, text=col.title(),
                                  command=lambda _col=col: self._treeview_sort_column(self.tree, _col, False))
            self.tree.column('system', width=100, anchor=tk.W)
            self.tree.column('name', width=200, anchor=tk.W)
            self.tree.column('status', width=100, anchor=tk.CENTER)
            
            base_query = "SELECT systemName, name, status FROM nodes"
            params = []
            search_term = self.search_var.get()
            if search_term:
                base_query += " WHERE systemName LIKE ? OR name LIKE ?"
                params.extend([f"%{search_term}%", f"%{search_term}%"])
            
            base_query += " ORDER BY systemName, name"
            cursor.execute(base_query, params)
            
            for system, name, status_int in cursor.fetchall():
                status_text = NODE_STATUS_TEXT.get(status_int, "Unknown")
                self.tree.insert('', tk.END, values=(system, name, status_text), tags=(status_text,))
        else:
            cols = ('name', 'mr', 'status')
            self.tree.config(columns=cols)
            for col in cols:
                self.tree.heading(col, text=col.title(), command=lambda _col=col: self._treeview_sort_column(self.tree, _col, False))
            self.tree.column('name', width=250)
            self.tree.column('mr', width=50, anchor=tk.CENTER)
            self.tree.column('status', width=100, anchor=tk.CENTER)
            
            # --- KORREKTUR: Füge uniqueName zur Abfrage hinzu ---
            base_query = "SELECT name, mastery_rank, status, uniqueName FROM items"
            where_clauses, params = [], []
            if category not in ("Gesamtübersicht", "All Items"):
                 where_clauses.append("category = ?")
                 params.append(category)
            search_term = self.search_var.get()
            if search_term:
                where_clauses.append("name LIKE ?")
                params.append(f"%{search_term}%")
            if self.hide_mastered_var.get():
                where_clauses.append("status != 'Mastered'")
            if self.hide_primes_var.get():
                where_clauses.append("name NOT LIKE '% Prime'")
            query = base_query
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            query += " ORDER BY name"
            cursor.execute(query, params)
            
            # --- KORREKTUR: Prüfe jedes Item und füge ggf. ein '*' hinzu ---
            for row in cursor.fetchall():
                name, mr, status, unique_name = row
                
                display_name = name
                # Prüfe, ob das Item im Set der Komponenten ist
                if unique_name in self.app.component_item_uniquenames:
                    display_name = f"{name} *"
                
                # Füge die Zeile mit dem möglicherweise modifizierten Namen ein
                self.tree.insert('', tk.END, values=(display_name, mr, status), tags=(status,))
        
        display_category = "All Items" if category == "Gesamtübersicht" else category
        self.item_frame.config(text=f"Items: {display_category}")
        self._treeview_sort_column(self.tree, self.sort_column, self.sort_reverse)

    # -------------------------------
    # Tree setup
    # -------------------------------
    def create_item_treeview(self):
        cols = ('name', 'mr', 'status')
        self.tree = ttk.Treeview(self.item_frame, columns=cols, show='headings')
        for col in cols:
            self.tree.heading(col, text=col.title(),
                              command=lambda _col=col: self._treeview_sort_column(self.tree, _col, False))
        self.tree.column('name', width=250)
        self.tree.column('mr', width=50, anchor=tk.CENTER)
        self.tree.column('status', width=100, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True)
        for status, color in STATUS_TEXT_COLORS.items():
            self.tree.tag_configure(status, foreground=color)
        for status, color in STATUS_NODE_COLORS.items():
            self.tree.tag_configure(status, foreground=color)
        self.tree.bind("<<TreeviewSelect>>", self.on_item_select)
        self.tree.bind("<Double-1>", self.handle_double_click)
        self.tree.bind("<KeyPress>", self.handle_key_press)
        self.tree.bind("<Control-a>", self._select_all)
        self.tree.bind("<Control-c>", self._copy_selection)

    def update_multiple_statuses(self, item_names, new_status):
        selected_ids = self.tree.selection()
        
        # --- KORREKTUR TEIL 1: Bereinige die Namen, bevor sie in der DB verwendet werden ---
        clean_item_names = [name.strip(" *") for name in item_names]
        selected_item_names = [self.tree.item(item_id, 'values')[0].strip(" *") for item_id in selected_ids]

        cursor = self.app.conn.cursor()
        # Verwende die bereinigten Namen für die DB-Abfrage
        updates = [(new_status, name) for name in clean_item_names]
        cursor.executemany("UPDATE items SET status = ? WHERE name = ?", updates)
        self.app.conn.commit()
        
        self.display_items(self.current_category)
        self.app.update_all_summaries()
        
        # --- KORREKTUR TEIL 2: Verwende die bereinigten Namen auch für die Wiederherstellung der Auswahl ---
        ids_to_reselect = []
        for item_id in self.tree.get_children():
            # Vergleiche bereinigten Namen mit bereinigten Namen
            if self.tree.item(item_id, 'values')[0].strip(" *") in selected_item_names:
                ids_to_reselect.append(item_id)
                
        if ids_to_reselect:
            self.tree.selection_set(ids_to_reselect)
            self.tree.focus(ids_to_reselect[0])
            self.tree.see(ids_to_reselect[0])
            
        self.app.update_status_bar(f"{len(clean_item_names)} Item(s) set to '{new_status}'.")

    def handle_double_click(self, event):
        item_id = self.tree.focus()
        if not item_id: return
        
        if self.current_category == "Star Chart":
            # (This part is fine and needs no changes)
            node_name = self.tree.item(item_id, 'values')[1]
            # ...
            self.update_node_status([node_name], new_status)
        else: # Item-Logik
            current_status = self.tree.item(item_id, 'values')[2]
            new_status = "Missing" if current_status == "Mastered" else "Mastered"
            
            # --- KORREKTUR: Bereinige den Namen, bevor er an die Update-Funktion übergeben wird ---
            display_name = self.tree.item(item_id, 'values')[0]
            item_name = display_name.strip(" *")
            
            self.update_multiple_statuses([item_name], new_status)

    def update_node_status(self, node_names, new_status_int):
        selected_ids = self.tree.selection()
        selected_node_names = [self.tree.item(item_id, 'values')[1] for item_id in selected_ids]
        cursor = self.app.conn.cursor()
        updates = [(new_status_int, name) for name in node_names]
        cursor.executemany("UPDATE nodes SET status = ? WHERE name = ?", updates)
        self.app.conn.commit()
        self.display_items(self.current_category)
        self.app.update_all_summaries()
        ids_to_reselect = []
        for item_id in self.tree.get_children():
            if self.tree.item(item_id, 'values')[1] in selected_node_names:
                ids_to_reselect.append(item_id)
        if ids_to_reselect:
            self.tree.selection_set(ids_to_reselect)
            self.tree.focus(ids_to_reselect[0])
            self.tree.see(ids_to_reselect[0])
        status_text = NODE_STATUS_TEXT.get(new_status_int)
        self.app.update_status_bar(f"{len(node_names)} Node(s) set to '{status_text}'.")  

    def handle_key_press(self, event):
        key_map = {'m': "Mastered", 's': "Missing", 'b': "Building", 'u': "Built", 'l': "Leveling"}
        pressed_key = event.keysym.lower()
        if pressed_key in key_map:
            new_status = key_map[pressed_key]
            selected_ids = self.tree.selection()
            if not selected_ids: return
            if self.current_category == "Star Chart": return
            item_names = [self.tree.item(item_id, 'values')[0] for item_id in selected_ids]
            self.update_multiple_statuses(item_names, new_status)

    def setup_context_menu(self):
        self.context_menu = tk.Menu(self.app.root, tearoff=0)
        self.tree.bind("<Button-3>", self._show_context_menu)

    def _show_context_menu(self, event):
        clicked_item_id = self.tree.identify_row(event.y)
        if not clicked_item_id: return
        current_selection = self.tree.selection()
        if clicked_item_id not in current_selection:
            self.tree.selection_set(clicked_item_id)
            self.tree.focus(clicked_item_id)
        final_selection_ids = self.tree.selection()
        if not final_selection_ids: return
        self.context_menu.delete(0, tk.END)
        if self.current_category == "Star Chart":
            node_names = [self.tree.item(sid, 'values')[1] for sid in final_selection_ids]
            self.context_menu.add_command(label=f"Set to '{NODE_STATUS_TEXT[1]}' ({len(node_names)} Nodes)", command=lambda: self.update_node_status(node_names, 1))  
            self.context_menu.add_command(label=f"Set to '{NODE_STATUS_TEXT[2]}' ({len(node_names)} Nodes)", command=lambda: self.update_node_status(node_names, 2))  
            self.context_menu.add_command(label=f"Set to '{NODE_STATUS_TEXT[0]}' ({len(node_names)} Nodes)", command=lambda: self.update_node_status(node_names, 0))  
            self.context_menu.add_separator()
            self.context_menu.add_command(label="Open in Wiki", command=self._open_wiki_for_node)
        else:
            item_names = [self.tree.item(sid, 'values')[0] for sid in final_selection_ids]
            for status in STATUS_OPTIONS:
                self.context_menu.add_command(label=f"Set to '{status}' ({len(item_names)} Items)", command=lambda s=status: self.update_multiple_statuses(item_names, s))  
            self.context_menu.add_separator()
            self.context_menu.add_command(label="Open in Wiki", command=self._open_wiki_for_item)
        self.context_menu.post(event.x_root, event.y_root)

    def _open_wiki_for_node(self):
        selected_item_id = self.tree.focus()
        if not selected_item_id: return
        values = self.tree.item(selected_item_id, 'values')
        node_name = values[1]
        formatted_name = quote(node_name.replace(' ', '_'))
        url = f"https://wiki.warframe.com/w/{formatted_name}"
        webbrowser.open_new_tab(url)
        self.app.update_status_bar(f"Opening wiki for {node_name}...")  
    

    def _open_wiki_for_item(self):
        selected_item_id = self.tree.focus()
        if not selected_item_id: return
        
        # Get the display name from the treeview
        display_name = self.tree.item(selected_item_id, 'values')[0]
        
        # --- KORREKTUR: Entferne das '*' Suffix, falls vorhanden ---
        # .strip() entfernt Leerzeichen und das Sternchen am Ende des Namens
        item_name = display_name.strip(" *")
        
        # Der Rest der Funktion funktioniert jetzt mit dem sauberen Namen
        formatted_name = quote(item_name.replace(' ', '_'))
        url = f"https://wiki.warframe.com/w/{formatted_name}"
        webbrowser.open_new_tab(url)
        self.app.update_status_bar(f"Opening wiki for {item_name}...")


    def on_item_select(self, event):
        selected_item_id = self.tree.focus()
        if selected_item_id:
            values = self.tree.item(selected_item_id)['values']
            
            if self.current_category == "Star Chart":
                # This part is fine, as Star Chart names don't have a '*'
                self.detail_panel.update_with_item(values)
            else:
                # --- KORREKTUR: Bereinige den Namen, bevor er an das DetailPanel gesendet wird ---
                display_name = values[0]
                clean_name = display_name.strip(" *")
                
                # Übergebe den sauberen Namen an das DetailPanel
                self.detail_panel.update_with_item(clean_name)
        else:
            self.detail_panel.clear_panel()

    def create_category_buttons(self):
        # Translate category names for display
        display_names = {
            "Gesamtübersicht": "All Items",
            "Warframe": "Warframes", # Plural for button
        }
        for category in CATEGORIES:
            btn_text = display_names.get(category, category)
            ttk.Button(self.category_frame, text=btn_text, command=lambda c=category: self.handle_category_click(c)).pack(fill=tk.X, pady=2)

    def create_summary_display(self):
        self.stats_frame = ttk.Frame(self.summary_frame)
        self.stats_frame.pack(fill=tk.X, pady=5, padx=5)
        self.diagram_canvas = tk.Canvas(self.summary_frame, height=25, bg="white", highlightthickness=0)
        self.diagram_canvas.pack(fill=tk.X, pady=5, padx=5)
        self.diagram_canvas.bind("<Configure>", self.update_diagram)




    def update_summary_display(self):
        self.status_counts = self.app.get_status_counts(self.current_category)
        for widget in self.stats_frame.winfo_children(): widget.destroy()
        if self.current_category == "Star Chart":
            node_status_order = ["Completed", "Steel Path", "Incomplete"]
            for status in node_status_order:
                count = self.status_counts.get(status, 0)
                ttk.Label(self.stats_frame, text=f"{status}: {count}").pack(side=tk.LEFT, padx=10, expand=True)
        else:
            for status in STATUS_OPTIONS:
                count = self.status_counts.get(status, 0)
                ttk.Label(self.stats_frame, text=f"{status}: {count}").pack(side=tk.LEFT, padx=10, expand=True)
        self.update_diagram()

    def update_diagram(self, event=None):
        counts = self.status_counts
        self.diagram_canvas.delete("all")
        if self.current_category == "Star Chart":
            total = sum(v for v in counts.values() if v is not None)
            if total == 0: return
            canvas_width = self.diagram_canvas.winfo_width()
            current_x = 0
            node_status_order = ["Completed", "Steel Path", "Incomplete"]
            for status in node_status_order:
                count = counts.get(status, 0)
                if count and count > 0:
                    bar_width = (count / total) * canvas_width
                    color = STATUS_NODE_COLORS.get(status, "#FFFFFF") 
                    self.diagram_canvas.create_rectangle(current_x, 0, current_x + bar_width, self.diagram_canvas.winfo_height(), fill=color, outline="")
                    current_x += bar_width
        else:
            total_items = sum(v for v in counts.values() if v is not None)
            if total_items == 0: return
            canvas_width = self.diagram_canvas.winfo_width()
            current_x = 0
            for status in STATUS_OPTIONS:
                count = counts.get(status, 0)
                if count and count > 0:
                    bar_width = (count / total_items) * canvas_width
                    self.diagram_canvas.create_rectangle(current_x, 0, current_x + bar_width, self.diagram_canvas.winfo_height(), fill=STATUS_COLORS.get(status, "#FFFFFF"), outline="")
                    current_x += bar_width
    
    # Diese neue Methode gehört in die MasteryTrackerTab-Klasse
    def show_drop_locations_for_item(self, item_name):
        """
        Wird von anderen Tabs aufgerufen, um direkt die Fundorte für ein Item/Ressource
        im DetailPanel anzuzeigen.
        """
        # Leere die Haupt-Item-Liste, da wir kein spezifisches Item aus der Liste anzeigen
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.item_frame.config(text=f"Showing Drop Locations for: {item_name}")

        # Rufe direkt die Drop-Location-Logik des DetailPanels auf
        self.detail_panel.load_drop_locations(item_name)
        
        # Aktualisiere den Titel und die Beschreibung im DetailPanel
        self.detail_panel.name_label.config(text=f"Drop Locations for {item_name}")
        self.detail_panel.description_text.config(state=tk.NORMAL)
        self.detail_panel.description_text.delete(1.0, tk.END)
        self.detail_panel.description_text.insert(tk.END, f"Showing all known drop locations for the resource '{item_name}'.\n\nComponent list is not applicable.")
        self.detail_panel.description_text.config(state=tk.DISABLED)
        self.detail_panel.image_label.config(image=None) # Ressourcen haben oft kein gutes Einzelbild
        
        # Leere die Komponentenliste
        for i in self.detail_panel.components_tree.get_children(): 
            self.detail_panel.components_tree.delete(i)
        self.detail_panel.components_tree.insert('', tk.END, values=("Not applicable", ""))


class ChartBrowser(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.browser = None
        self.bind("<Map>", self._embed)          # create when the widget is shown
        self.bind("<Configure>", self._on_configure)
        self._last_html_path = None

    def _embed(self, event=None):
        if self.browser:
            return
        # Create a real child window for CEF
        window_info = cef.WindowInfo()
        window_info.SetAsChild(self.winfo_id(), [0, 0, self.winfo_width(), self.winfo_height()])
        self.browser = cef.CreateBrowserSync(window_info, url="about:blank")

    def _on_configure(self, event):
        if self.browser:
            try:
                self.browser.SetBounds(0, 0, event.width, event.height)
            except Exception:
                pass

    def load_html(self, html: str):
        # Ensure browser exists (widget might not be mapped yet)
        if not self.browser:
            self.after(50, lambda: self.load_html(html))
            return
        # Write to a temp file and navigate (most reliable for assets/CDN)
        path = os.path.join(tempfile.gettempdir(), f"chart_{id(self)}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        self._last_html_path = path
        self.browser.LoadUrl("file:///" + path.replace("\\", "/"))

    def destroy(self):
        if self.browser:
            try:
                self.browser.CloseBrowser(True)
            except Exception:
                pass
            self.browser = None
        super().destroy()


# --- LiveTickerTAb KLASSE ---
class LiveTickerTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=10)
        self.app = app

        # Speichert pro Treeview die aktuelle Sortierung
        self.sort_states = {}

        # --- GRID KONFIGURATION ---
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)  # Missions/Nightwave soll sich vertikal ausdehnen

        # === BLOCK 1: ENVIRONMENTS (Obere Zeile) ===
        env_frame = ttk.LabelFrame(self, text="Environments", padding=10)
        env_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        env_frame.columnconfigure((0, 1, 2), weight=1)

        self.cetus_lbl = ttk.Label(env_frame, text="Cetus: loading...", justify="left")
        self.vallis_lbl = ttk.Label(env_frame, text="Orb Vallis: loading...", justify="left")
        self.cambion_lbl = ttk.Label(env_frame, text="Cambion Drift: loading...", justify="left")

        self.cetus_lbl.grid(row=0, column=0, sticky="w")
        self.vallis_lbl.grid(row=0, column=1, sticky="w")
        self.cambion_lbl.grid(row=0, column=2, sticky="w")

        # === BLOCK 2: MISSIONS (Linke Spalte) ===
        missions_frame = ttk.LabelFrame(self, text="Missions", padding=10)
        missions_frame.grid(row=1, column=0, sticky="nsew", pady=5, padx=(0, 5))

        # Sortie
        self.sortie_title_lbl = ttk.Label(missions_frame, text="Sortie", font=self.app.font_bold)
        self.sortie_title_lbl.pack(fill="x")
        self.sortie_lbl = ttk.Label(missions_frame, text="loading...", justify="left", anchor="nw")
        self.sortie_lbl.pack(fill="x", pady=(0, 10), padx=(5, 0))

        ttk.Separator(missions_frame, orient="horizontal").pack(fill="x", pady=5)

        # Archon Hunt
        self.archon_title_lbl = ttk.Label(missions_frame, text="Archon Hunt", font=self.app.font_bold)
        self.archon_title_lbl.pack(fill="x")
        self.archon_lbl = ttk.Label(missions_frame, text="loading...", justify="left", anchor="nw")
        self.archon_lbl.pack(fill="x", padx=(5, 0))

        # === BLOCK 3: NIGHTWAVE (Rechte Spalte) ===
        nightwave_frame = ttk.LabelFrame(self, text="Nightwave", padding=10)
        nightwave_frame.grid(row=1, column=1, sticky="nsew", pady=5, padx=(5, 0))
        nightwave_frame.rowconfigure(1, weight=1)
        nightwave_frame.columnconfigure(0, weight=1)

        self.nightwave_info_lbl = ttk.Label(nightwave_frame, text="Loading season info...")
        self.nightwave_info_lbl.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))

        cols = ("mission", "xp")
        self.nightwave_tree = ttk.Treeview(nightwave_frame, columns=cols, show="headings", height=8)
        self.nightwave_tree.heading("mission", text="Mission",
            command=lambda: self._treeview_sort_column(self.nightwave_tree, "mission", False))
        self.nightwave_tree.heading("xp", text="XP",
            command=lambda: self._treeview_sort_column(self.nightwave_tree, "xp", False))
        self.nightwave_tree.column("mission", width=300, stretch=True)
        self.nightwave_tree.column("xp", width=80, anchor="e", stretch=False)
        self.nightwave_tree.grid(row=1, column=0, sticky="nsew")

        nw_scroll = ttk.Scrollbar(nightwave_frame, orient="vertical", command=self.nightwave_tree.yview)
        self.nightwave_tree.configure(yscrollcommand=nw_scroll.set)
        nw_scroll.grid(row=1, column=1, sticky="ns")

        # === BLOCK 4: VOID TRADER (Untere Zeile) ===
        trader_frame = ttk.LabelFrame(self, text="Void Trader", padding=10)
        trader_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        trader_frame.columnconfigure(0, weight=1)
        trader_frame.rowconfigure(1, weight=1)

        self.trader_lbl = ttk.Label(trader_frame, text="Loading trader info...")
        self.trader_lbl.grid(row=0, column=0, sticky="w", pady=(0, 5))

        tcols = ("item", "ducats", "credits")
        self.trader_tree = ttk.Treeview(trader_frame, columns=tcols, show="headings", height=6)
        self.trader_tree.heading("item", text="Item",
            command=lambda: self._treeview_sort_column(self.trader_tree, "item", False))
        self.trader_tree.heading("ducats", text="Ducats",
            command=lambda: self._treeview_sort_column(self.trader_tree, "ducats", False))
        self.trader_tree.heading("credits", text="Credits",
            command=lambda: self._treeview_sort_column(self.trader_tree, "credits", False))
        self.trader_tree.column("item", width=400, stretch=True)
        self.trader_tree.column("ducats", width=100, anchor="center", stretch=False)
        self.trader_tree.column("credits", width=120, anchor="e", stretch=False)
        self.trader_tree.grid(row=1, column=0, sticky="nsew")

        trader_scroll = ttk.Scrollbar(trader_frame, orient="vertical", command=self.trader_tree.yview)
        self.trader_tree.configure(yscrollcommand=trader_scroll.set)
        trader_scroll.grid(row=1, column=1, sticky="ns")

    # --- Sortierfunktion ---
    def _treeview_sort_column(self, tree, col, reverse):
        """Sortiert eine Treeview-Spalte und merkt sich die Sortierung pro Tree."""
        self.sort_states[tree] = (col, reverse)

        items = [(tree.set(k, col), k) for k in tree.get_children("")]
        try:
            items.sort(key=lambda t: int(str(t[0]).replace(",", "")), reverse=reverse)
        except ValueError:
            items.sort(key=lambda t: str(t[0]).lower(), reverse=reverse)

        for index, (val, k) in enumerate(items):
            tree.move(k, "", index)

        tree.heading(col, command=lambda: self._treeview_sort_column(tree, col, not reverse))

    def resort_tree(self, tree):
        """Wendet die gespeicherte Sortierung für einen Tree an, falls gültig."""
        if tree not in self.sort_states:
            return
        col, reverse = self.sort_states[tree]

        current_cols = tree.cget("columns")
        if col not in current_cols:
            return  # Spalte existiert nicht mehr

        self._treeview_sort_column(tree, col, reverse)

    # --- Hilfsfunktion für Zeit ---
    def format_time(self, seconds_str):
        seconds = int(seconds_str)
        if seconds < 0: return "Expired"
        days, rem = divmod(seconds, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, _ = divmod(rem, 60)
        if days > 0: return f"{days}d {hours}h {minutes}m"
        if hours > 0: return f"{hours}h {minutes}m"
        return f"{minutes}m"

    # --- Update der Inhalte ---
    def update_worldstate(self, worldstate_data):
        # Environments
        cetus_data = worldstate_data.get('cetusCycle')
        if cetus_data:
            self.cetus_lbl.config(text=f"Cetus: {'Day' if cetus_data['isDay'] else 'Night'} (Ends in: {cetus_data['shortString']})")

        vallis_data = worldstate_data.get('vallisCycle')
        if vallis_data:
            self.vallis_lbl.config(text=f"Orb Vallis: {'Warm' if vallis_data['isWarm'] else 'Cold'} (Ends in: {vallis_data['shortString']})")

        cambion_data = worldstate_data.get('cambionCycle')
        if cambion_data:
            self.cambion_lbl.config(text=f"Cambion: {cambion_data['active'].upper()} (Ends in: {cambion_data['timeLeft']})")

        # Trader
        trader_list = worldstate_data.get("VoidTraders")
        if trader_list:
            data = trader_list[0]
            activation_ms = int(data['Activation']['$date']['$numberLong'])
            expiry_ms = int(data['Expiry']['$date']['$numberLong'])
            activation = datetime.fromtimestamp(activation_ms / 1000, tz=timezone.utc)
            expiry = datetime.fromtimestamp(expiry_ms / 1000, tz=timezone.utc)
            now = datetime.now(timezone.utc)

            if now < activation:
                self.trader_lbl.config(text=f"Baro Ki'Teer arrives at {data['Node']} in: {self.format_time((activation - now).total_seconds())}")
            else:
                self.trader_lbl.config(text=f"Baro Ki'Teer is at {data['Node']} and leaves in: {self.format_time((expiry - now).total_seconds())}")

            for row in self.trader_tree.get_children():
                self.trader_tree.delete(row)
            for item in data.get("Manifest", []):
                name_parts = item.get("ItemType", "Unknown").split("/")
                name = name_parts[-1] if name_parts else "Unknown"
                self.trader_tree.insert("", "end", values=(name, item.get("PrimePrice", 0), f"{item.get('RegularPrice', 0):,}"))

        # Sortie
        sortie_list = worldstate_data.get("Sorties")
        if sortie_list:
            data = sortie_list[0]
            expiry_ms = int(data['Expiry']['$date']['$numberLong'])
            expiry = datetime.fromtimestamp(expiry_ms / 1000, tz=timezone.utc)
            remaining = expiry - datetime.now(timezone.utc)
            boss_name = data.get('Boss', 'N/A').replace('SORTIE_BOSS_', '').replace('_', ' ').title()
            missions = "\n".join([f"- {pretty_mission_type(m.get('missionType'))} ({pretty_modifier(m.get('modifierType'))})" for m in data.get('Variants', [])])
            self.sortie_title_lbl.config(text=f"Sortie: {boss_name}")
            self.sortie_lbl.config(text=f"Time Remaining: {self.format_time(remaining.total_seconds())}\nMissions:\n{missions}")

        # Archon Hunt
        archon_list = worldstate_data.get("LiteSorties")
        if archon_list:
            data = archon_list[0]
            expiry_ms = int(data['Expiry']['$date']['$numberLong'])
            expiry = datetime.fromtimestamp(expiry_ms / 1000, tz=timezone.utc)
            remaining = expiry - datetime.now(timezone.utc)
            boss_name = data.get('Boss', 'N/A').replace('SORTIE_BOSS_', '').replace('_', ' ').title()
            missions = "\n".join([f"- {pretty_mission_type(m.get('missionType'))} ({resolve_node_name(self.app.conn, m.get('node'))})" for m in data.get('Missions', [])])
            self.archon_title_lbl.config(text=f"Archon Hunt: {boss_name}")
            self.archon_lbl.config(text=f"Time Remaining: {self.format_time(remaining.total_seconds())}\nMissions:\n{missions}")

        # Nightwave
        # --- KORREKTUR: Nutzt jetzt die neuen, besseren Daten von 'api.warframestat.us' ---
        nw_data = worldstate_data.get('nightwave') # <-- Greift auf den neuen 'nightwave'-Schlüssel zu
        if nw_data and nw_data.get('active'):
            # Info-Label
            season = nw_data.get("season", "?")
            tag = nw_data.get("tag", "Nora's Mix")
            expiry_str = nw_data.get('expiry', '')
            
            try:
                # Zeit bis zum Ablauf berechnen
                expiry_dt = datetime.fromisoformat(expiry_str.replace('Z', '+00:00'))
                remaining = expiry_dt - datetime.now(timezone.utc)
                self.nightwave_info_lbl.config(text=f"{tag} (Season {season}) - Ends in: {self.format_time(remaining.total_seconds())}")
            except (ValueError, TypeError):
                self.nightwave_info_lbl.config(text=f"{tag} (Season {season})")

            # Treeview füllen
            for row in self.nightwave_tree.get_children():
                self.nightwave_tree.delete(row)
            
            # Die neue API verwendet 'activeChallenges' (camelCase)
            for ch in nw_data.get('activeChallenges', []):
                # 'desc' ist hier immer vorhanden und korrekt
                description = ch.get("desc", "Unknown Challenge")
                reputation = f"{ch.get('reputation', 0):,}"
                self.nightwave_tree.insert("", "end", values=(description, reputation))
        else:
            self.nightwave_info_lbl.config(text="No active Nightwave season.")
            for row in self.nightwave_tree.get_children():
                self.nightwave_tree.delete(row)

        # --- Sortierung nach dem Refresh wieder anwenden ---
        self.resort_tree(self.nightwave_tree)
        self.resort_tree(self.trader_tree)


# --- NEUE RELIC FINDER KLASSE ---
class RelicFinderTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding="10")
        self.app = app
        self.processed_relics = []

        # Speichert Sortierung pro Tree
        self.sort_states = {}

        # Layout
        self.paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # Left Frame (Relic List & Filters)
        left_frame = ttk.Frame(self.paned_window)
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(1, weight=1)
        self.paned_window.add(left_frame, weight=1)

        # Right container
        right_container = ttk.Frame(self.paned_window)
        self.paned_window.add(right_container, weight=2)

        # Filter widgets
        filter_frame = ttk.LabelFrame(left_frame, text="Filter & Search", padding=10)
        filter_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.apply_filters)
        ttk.Label(filter_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(filter_frame, textvariable=self.search_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.vaulted_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            filter_frame, text="Hide Vaulted", variable=self.vaulted_var, command=self.apply_filters
        ).pack(side=tk.LEFT, padx=5)

        # Relic Treeview
        relic_tree_frame = ttk.Frame(left_frame)
        relic_tree_frame.grid(row=1, column=0, sticky="nsew")
        self.relic_tree = ttk.Treeview(
            relic_tree_frame, columns=("tier", "name", "state"), show="headings"
        )
        for col in ("tier", "name", "state"):
            self.relic_tree.heading(
                col,
                text=col.title(),
                command=lambda _col=col: self._treeview_sort_column(self.relic_tree, _col, False),
            )
        self.relic_tree.column("tier", width=60, anchor=tk.CENTER)
        self.relic_tree.column("name", width=150)
        self.relic_tree.column("state", width=100, anchor=tk.CENTER)
        self.relic_tree.pack(side="left", fill="both", expand=True)

        relic_scrollbar = ttk.Scrollbar(
            relic_tree_frame, orient="vertical", command=self.relic_tree.yview
        )
        relic_scrollbar.pack(side="right", fill="y")
        self.relic_tree.configure(yscrollcommand=relic_scrollbar.set)

        self.relic_tree.bind("<<TreeviewSelect>>", self.on_relic_select)
        self._setup_relic_context_menu()
        self.relic_tree.bind("<Button-3>", self._show_relic_context_menu)

        # Rewards Treeview
        rewards_frame = ttk.LabelFrame(
            right_container, text="Rewards for Selected Relic (Intact)", padding="5"
        )
        rewards_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        self.drops_tree = ttk.Treeview(
            rewards_frame, columns=("rarity", "name", "chance"), show="headings"
        )
        for col in ("rarity", "name", "chance"):
            self.drops_tree.heading(
                col,
                text=col.title(),
                command=lambda _col=col: self._treeview_sort_column(self.drops_tree, _col, False),
            )
        self.drops_tree.column("rarity", width=80)
        self.drops_tree.column("name", width=250)
        self.drops_tree.column("chance", width=120, anchor=tk.E)
        self.drops_tree.pack(fill=tk.BOTH, expand=True)
        # Konfiguriere die Textfarben für die Seltenheiten
        for rarity, color in RARITY_TEXT_COLORS.items():
            self.drops_tree.tag_configure(rarity, foreground=color)


        # Drop Locations Treeview
        locations_frame = ttk.LabelFrame(right_container, text="Drop Locations", padding="5")
        locations_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(5, 0))
        self.locations_tree = ttk.Treeview(
            locations_frame, columns=("location", "type", "rotation", "chance"), show="headings"
        )
        for col in ("location", "type", "rotation", "chance"):
            self.locations_tree.heading(
                col,
                text=col.title(),
                command=lambda _col=col: self._treeview_sort_column(self.locations_tree, _col, False),
            )
        self.locations_tree.column("location", width=220)
        self.locations_tree.column("type", width=120)
        self.locations_tree.column("rotation", width=80, anchor=tk.CENTER)
        self.locations_tree.column("chance", width=80, anchor=tk.E)
        self.locations_tree.pack(fill=tk.BOTH, expand=True)

    # --- Sortierlogik ---
    def _treeview_sort_column(self, tree, col, reverse):
        self.sort_states[tree] = (col, reverse)

        items = [(tree.set(k, col), k) for k in tree.get_children("")]
        try:
            items.sort(key=lambda t: int(str(t[0]).replace(",", "")), reverse=reverse)
        except ValueError:
            items.sort(key=lambda t: str(t[0]).lower(), reverse=reverse)

        for index, (val, k) in enumerate(items):
            tree.move(k, "", index)

        tree.heading(
            col, command=lambda: self._treeview_sort_column(tree, col, not reverse)
        )

    def resort_tree(self, tree):
        if tree not in self.sort_states:
            return
        col, reverse = self.sort_states[tree]
        current_cols = tree.cget("columns")
        if col not in current_cols:
            return
        self._treeview_sort_column(tree, col, reverse)

    # --- Apply Filters ---
    def apply_filters(self, *args):
        search_term = self.search_var.get().lower()
        hide_vaulted = self.vaulted_var.get()

        for i in self.relic_tree.get_children():
            self.relic_tree.delete(i)

        filtered_relics = self.processed_relics
        if hide_vaulted:
            filtered_relics = [r for r in filtered_relics if not r["vaulted"]]
        if search_term:
            filtered_relics = [
                r
                for r in filtered_relics
                if search_term in r["name"].lower()
                or any(search_term in reward["item"]["name"].lower() for reward in r["rewards"])
            ]

        for relic in sorted(filtered_relics, key=lambda r: (r["tier"], r["name"])):
            status_str = "Vaulted" if relic["vaulted"] else "Available"
            self.relic_tree.insert(
                "", tk.END, values=(relic["tier"], relic["name"], status_str), iid=relic["name"]
            )

        self.resort_tree(self.relic_tree)

    # --- Relic Auswahl ---
    def on_relic_select(self, event):
        selected_item_id = self.relic_tree.focus()

        for i in self.drops_tree.get_children():
            self.drops_tree.delete(i)
        for i in self.locations_tree.get_children():
            self.locations_tree.delete(i)

        if not selected_item_id:
            return

        selected_relic_name = self.relic_tree.item(selected_item_id, "values")[1]
        selected_relic_data = next(
            (r for r in self.processed_relics if r["name"] == selected_relic_name), None
        )

        if selected_relic_data:
            # Rewards Tree
            rewards = sorted(
                selected_relic_data.get("rewards", []),
                key=lambda x: (x["rarity"] != "Common", x["rarity"] != "Uncommon", x["rarity"] != "Rare"),
            )
            for reward in rewards:
                chance_str = f"{reward.get('chance', 0):.2f}%"
                item_name = reward.get("item", {}).get("name", "Unknown Item")
                self.drops_tree.insert(
                    "", tk.END, values=(reward["rarity"], item_name, chance_str), tags=(reward["rarity"],)
                )
            self.resort_tree(self.drops_tree)

            # Locations Tree
            drop_locations = selected_relic_data.get("drops", [])
            if drop_locations:
                for drop in sorted(drop_locations, key=lambda x: x.get("chance", 0), reverse=True):
                    full_location = drop.get("location", "N/A")
                    chance = f"{drop.get('chance', 0):.2f}%"

                    parsed_mission_type = "N/A"
                    rotation = "-"
                    clean_location_display = full_location

                    type_match = re.search(r"\((.*?)\)", full_location)
                    if type_match:
                        parsed_mission_type = type_match.group(1)
                        clean_location_display = clean_location_display.replace(
                            f"({parsed_mission_type})", ""
                        ).strip()

                    if ", Rotation " in clean_location_display:
                        parts = clean_location_display.split(", Rotation ")
                        clean_location_display = parts[0]
                        rotation = parts[1]

                    self.locations_tree.insert(
                        "",
                        tk.END,
                        values=(clean_location_display, parsed_mission_type, rotation, chance),
                    )
            else:
                self.locations_tree.insert("", tk.END, values=("This relic is vaulted.", "", "", ""))

            self.resort_tree(self.locations_tree)

    # --- Context Menü ---
    def _setup_relic_context_menu(self):
        self.relic_context_menu = tk.Menu(self, tearoff=0)
        self.relic_context_menu.add_command(label="Open in Wiki", command=self._open_wiki_for_relic)

    def _show_relic_context_menu(self, event):
        item_id = self.relic_tree.identify_row(event.y)
        if item_id:
            self.relic_tree.selection_set(item_id)
            self.relic_tree.focus(item_id)
            self.relic_context_menu.post(event.x_root, event.y_root)

    def _open_wiki_for_relic(self):
        selected_item_id = self.relic_tree.focus()
        if not selected_item_id:
            return

        relic_name = selected_item_id
        formatted_name = quote(relic_name.replace(" ", "_"))
        url = f"https://wiki.warframe.com/w/{formatted_name}"

        webbrowser.open_new_tab(url)
        self.app.update_status_bar(f"Opening wiki for {relic_name} Relic...")
    
    # --- Public: initial load + progress row + thread ---
    def load_all_relics_threaded(self):
        """Startet den Download/Parse der Relic-Daten in einem Thread."""
        self.app.update_status_bar("Fetching relic data...")
        # Tree leeren und 'Loading...' anzeigen
        for i in self.relic_tree.get_children():
            self.relic_tree.delete(i)
        self.relic_tree.insert('', tk.END, values=("", "Loading, please wait...", ""))

        threading.Thread(target=self._fetch_and_process_relics, daemon=True).start()

    # --- Optional: von außen gezielt ein Relikt fokussieren (wird von DetailPanel genutzt) ---
    def search_and_select_relic(self, relic_name: str):
        """Sucht ein Relikt in der Liste, wählt es an und scrollt hin (ohne Vaulted-Filter)."""
        self.vaulted_var.set(False)           # sicherstellen, dass es nicht ausgeblendet ist
        self.search_var.set(relic_name)       # triggert apply_filters()

        def _select_item():
            if self.relic_tree.exists(relic_name):
                self.relic_tree.selection_set(relic_name)
                self.relic_tree.focus(relic_name)
                self.relic_tree.see(relic_name)
        self.app.root.after(120, _select_item)

    # --- Worker: lädt & verarbeitet Relics; UI-Updates via .after ---
    def _fetch_and_process_relics(self):
        url = "https://raw.githubusercontent.com/WFCD/warframe-items/refs/heads/master/data/json/Relics.json"
        try:
            resp = requests.get(url, headers={'User-Agent': 'WarframeMasteryTrackerApp/1.0'})
            resp.raise_for_status()
            raw_relics = resp.json()

            relic_dict = {}
            for relic in raw_relics:
                # Nur die "Intact"-Variante bestimmt, ob ein Relikt aktuell dropt
                name = relic.get('name', '')
                if "Intact" in name:
                    base_name_parts = name.split(' ')
                    base_name = " ".join(base_name_parts[:2]) if len(base_name_parts) >= 2 else name

                    # 'vaulted' ist unzuverlässig → Verfügbarkeit anhand non-empty 'drops'
                    drops = relic.get('drops', []) or []
                    rewards = relic.get('rewards', []) or []
                    is_vaulted = not bool(drops)

                    relic_dict[base_name] = {
                        'name': base_name,
                        'tier': base_name_parts[0] if base_name_parts else '',
                        'vaulted': is_vaulted,
                        'rewards': rewards,
                        'drops': drops
                    }

            self.processed_relics = list(relic_dict.values())

            # UI aktualisieren
            self.app.root.after(0, self.apply_filters)
            self.app.root.after(0, self.app.update_status_bar, "Relic data loaded successfully.")
        except requests.exceptions.RequestException as e:
            # Fehler im UI anzeigen
            def _show_error():
                for i in self.relic_tree.get_children():
                    self.relic_tree.delete(i)
                self.relic_tree.insert('', tk.END, values=("", "Error fetching relics.", ""))
                self.app.update_status_bar(f"Failed to load relic data: {e}")
            self.app.root.after(0, _show_error)


from contextlib import closing

# --- RESOURCE TRACKER CLASS ---
class ResourceTrackerTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding="10")
        self.app = app
        self.sort_states = {}
        self.needed_data = {}
        self.spent_data = {}
        self.all_masterable_item_uniquenames = set()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Search bar
        search_frame = ttk.LabelFrame(self, text="Search Resources", padding="5")
        search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._populate_results)
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(search_frame, textvariable=self.search_var).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Paned window
        paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned_window.grid(row=1, column=0, sticky="nsew")

        needed_frame = ttk.LabelFrame(paned_window, text="Needed (for 'Missing' items)", padding="5")
        spent_frame = ttk.LabelFrame(paned_window, text="Spent (for 'Mastered' items)", padding="5")
        paned_window.add(needed_frame, weight=1)
        paned_window.add(spent_frame, weight=1)

        self.needed_tree = self._create_results_tree(needed_frame)
        self.spent_tree = self._create_results_tree(spent_frame)
        self._setup_context_menu()
        self.needed_tree.bind("<Button-3>", self._show_context_menu)
        self.spent_tree.bind("<Button-3>", self._show_context_menu)

    # -------------------------------
    # Context menu
    # -------------------------------
    def _setup_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Find Drop Locations", command=self._find_drop_locations)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Open in Wiki", command=self._open_wiki_for_resource)

    def _show_context_menu(self, event):
        tree = event.widget
        item_id = tree.identify_row(event.y)
        if item_id:
            tree.selection_set(item_id)
            tree.focus(item_id)
            self.context_menu.post(event.x_root, event.y_root)

    def _find_drop_locations(self):
        focused_tree = self.focus_get()
        if focused_tree not in [self.needed_tree, self.spent_tree]:
            return
        selected_item_id = focused_tree.focus()
        if not selected_item_id:
            return
        resource_name = focused_tree.item(selected_item_id, 'values')[0]
        self.app.notebook.select(self.app.mastery_tracker_tab)
        self.app.mastery_tracker_tab.show_drop_locations_for_item(resource_name)

    def _open_wiki_for_resource(self):
        focused_tree = self.focus_get()
        if focused_tree not in [self.needed_tree, self.spent_tree]:
            return
        selected_item_id = focused_tree.focus()
        if not selected_item_id:
            return
        resource_name = focused_tree.item(selected_item_id, 'values')[0]
        formatted_name = quote(resource_name.replace(' ', '_'))
        url = f"https://wiki.warframe.com/w/{formatted_name}"
        webbrowser.open_new_tab(url)
        self.app.update_status_bar(f"Opening wiki for {resource_name}...")

    # -------------------------------
    # Tree setup & sorting
    # -------------------------------
    def _create_results_tree(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True)
        tree = ttk.Treeview(frame, columns=('resource', 'quantity'), show='headings')
        for col in ('resource', 'quantity'):
            tree.heading(col, text=col.title(),
                         command=lambda _col=col, _tree=tree: self._treeview_sort_column(_tree, _col, False))
        tree.column('resource', width=300)
        tree.column('quantity', width=150, anchor=tk.E)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        return tree

    def _treeview_sort_column(self, tree, col, reverse):
        self.sort_states[tree] = (col, reverse)
        items = [(tree.set(k, col), k) for k in tree.get_children("")]
        try:
            items.sort(key=lambda t: int(str(t[0]).replace(",", "")), reverse=reverse)
        except ValueError:
            items.sort(key=lambda t: str(t[0]).lower(), reverse=reverse)
        for index, (val, k) in enumerate(items):
            tree.move(k, "", index)
        tree.heading(col, command=lambda: self._treeview_sort_column(tree, col, not reverse))

    def resort_tree(self, tree):
        if tree not in self.sort_states:
            if "quantity" in tree.cget("columns"):
                self._treeview_sort_column(tree, "quantity", True)
            return
        col, reverse = self.sort_states[tree]
        current_cols = tree.cget("columns")
        if col not in current_cols:
            return
        self._treeview_sort_column(tree, col, reverse)

    # -------------------------------
    # Calculation
    # -------------------------------
    def start_calculation(self):
        for tree in [self.needed_tree, self.spent_tree]:
            for i in tree.get_children():
                tree.delete(i)
            tree.insert('', tk.END, values=("Calculating...", ""))
        self.app.update_status_bar("Aggregating resource requirements...")
        threading.Thread(target=self._perform_calculation, daemon=True).start()

    def _perform_calculation(self):
        with closing(self.app.conn.cursor()) as cursor:
            cursor.execute("SELECT uniqueName FROM items")
            self.all_masterable_item_uniquenames = {row[0] for row in cursor.fetchall()}

            cursor.execute("SELECT uniqueName FROM items WHERE status = 'Missing'")
            missing_names = [row[0] for row in cursor.fetchall() if row[0]]
            cursor.execute("SELECT uniqueName FROM items WHERE status = 'Mastered'")
            mastered_names = [row[0] for row in cursor.fetchall() if row[0]]

        self.needed_data = self._get_all_requirements(missing_names)
        self.spent_data = self._get_all_requirements(mastered_names)
        self.app.root.after(0, self._populate_results)

    def _get_all_requirements(self, unique_names):
        total_requirements = {}
        item_component_cache = {}
        for u_name in unique_names:
            self._get_recursive_components(u_name, 1, total_requirements, item_component_cache)
        return total_requirements

    def _get_recursive_components(self, unique_name, quantity, total_reqs, cache):
        if unique_name in cache:
            for sub_name, sub_count in cache[unique_name].items():
                total_reqs[sub_name] = total_reqs.get(sub_name, 0) + (sub_count * quantity)
            return

        recipe = self.app.recipes_data.get(unique_name)

        if not recipe:
            if unique_name in self.all_masterable_item_uniquenames:
                cache[unique_name] = {}
                return
            else:
                total_reqs[unique_name] = total_reqs.get(unique_name, 0) + quantity
                cache[unique_name] = {unique_name: 1}
                return

        this_item_base_components = {}
        build_price = recipe.get('buildPrice', 0)
        if build_price > 0:
            this_item_base_components['/Lotus/Types/Items/MiscItems/Credits'] = build_price
        for ingredient in recipe.get('ingredients', []):
            self._get_recursive_components(ingredient['ItemType'], ingredient['ItemCount'],
                                           this_item_base_components, cache)
        cache[unique_name] = this_item_base_components
        for base_name, count in this_item_base_components.items():
            total_reqs[base_name] = total_reqs.get(base_name, 0) + (count * quantity)

    # -------------------------------
    # Results display
    # -------------------------------
    def _populate_results(self, *args):
        for tree in [self.needed_tree, self.spent_tree]:
            for i in tree.get_children(): tree.delete(i)
        name_map = self.app.full_item_name_map

        def should_exclude(item_name):
            name_lower = item_name.lower()
            if name_lower in RESOURCE_TRACKER_EXCLUSION_EXCEPTIONS:
                return False
            for keyword in RESOURCE_TRACKER_CONTAINS_KEYWORDS:
                if keyword in name_lower:
                    return True
            for keyword in RESOURCE_TRACKER_ENDSWITH_KEYWORDS:
                if name_lower.endswith(keyword):
                    return True
            return False

        filtered_needed_data = {
            key: value for key, value in self.needed_data.items()
            if not should_exclude(name_map.get(key, key))
        }
        filtered_spent_data = {
            key: value for key, value in self.spent_data.items()
            if not should_exclude(name_map.get(key, key))
        }

        search_term = self.search_var.get().lower()
        needed_to_display = filtered_needed_data
        if search_term:
            needed_to_display = {
                key: value for key, value in filtered_needed_data.items()
                if search_term in name_map.get(key, key).lower()
            }
        spent_to_display = filtered_spent_data
        if search_term:
            spent_to_display = {
                key: value for key, value in filtered_spent_data.items()
                if search_term in name_map.get(key, key).lower()
            }

        sorted_needed = sorted(needed_to_display.items(), key=lambda item: name_map.get(item[0], item[0]))
        for name_key, count in sorted_needed:
            display_name = name_map.get(name_key, name_key.split('/')[-1])
            self.needed_tree.insert('', tk.END, values=(display_name, f"{int(count):,}"))

        sorted_spent = sorted(spent_to_display.items(), key=lambda item: name_map.get(item[0], item[0]))
        for name_key, count in sorted_spent:
            display_name = name_map.get(name_key, name_key.split('/')[-1])
            self.spent_tree.insert('', tk.END, values=(display_name, f"{int(count):,}"))

        self.resort_tree(self.needed_tree)
        self.resort_tree(self.spent_tree)

        if not search_term:
            self.app.update_status_bar("Resource calculation complete.")



# --- HAUPTANWENDUNG ---
class WarframeTrackerApp:
    def __init__(self, root):
            self.component_item_uniquenames = set()
            self.full_item_name_map = {}
            self.recipes_data = {}
            self.unique_name_map = {}
            self.root = root
            self.root.title("Warframe Mastery Dashboard")
            self.root.geometry("1400x900")
            self.conn = None

            self.font_normal = ("Segoe UI", 10)
            self.font_bold = ("Segoe UI Semibold", 10)
            self.font_header = ("Segoe UI Semibold", 16)
            
            style = ttk.Style()
            style.configure("Treeview.Heading", font=self.font_bold)
            style.configure("Treeview", rowheight=25, font=self.font_normal)

            self.setup_database()
            
            self.notebook = ttk.Notebook(self.root)
            self.notebook.pack(expand=True, fill='both', padx=10, pady=10)
            
            # Create the status bar BEFORE creating any tabs that might use it.
            self.status_bar = ttk.Label(self.root, text="Initialisiere...", anchor=tk.W)
            self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 5))

            # --- ROBUST ICON LOADING LOGIC ---
            try:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                icons_dir = os.path.join(script_dir, "icons")

                self.icon_dashboard = tk.PhotoImage(file=os.path.join(icons_dir, "dashboard.png"))
                self.icon_tracker = tk.PhotoImage(file=os.path.join(icons_dir, "tracker.png"))
                self.icon_live = tk.PhotoImage(file=os.path.join(icons_dir, "live.png"))
                self.icon_relic = tk.PhotoImage(file=os.path.join(icons_dir, "relic.png"))
                self.icon_resources = tk.PhotoImage(file=os.path.join(icons_dir, "resources.png"))
            except tk.TclError as e:
                print(f"Could not load icons: {e}")
                self.icon_dashboard = tk.PhotoImage()
                self.icon_tracker = tk.PhotoImage()
                self.icon_live = tk.PhotoImage()
                self.icon_relic = tk.PhotoImage()
                self.icon_resources = tk.PhotoImage()
            
            self.dashboard_tab = DashboardTab(self.notebook, self)
            self.mastery_tracker_tab = MasteryTrackerTab(self.notebook, self)
            self.live_ticker_tab = LiveTickerTab(self.notebook, self)
            self.relic_finder_tab = RelicFinderTab(self.notebook, self)
            self.resource_tracker_tab = ResourceTrackerTab(self.notebook, self)

            self.notebook.add(self.dashboard_tab, text=" Dashboard", image=self.icon_dashboard, compound=tk.LEFT)
            self.notebook.add(self.mastery_tracker_tab, text=" Mastery-Tracker", image=self.icon_tracker, compound=tk.LEFT)
            self.notebook.add(self.live_ticker_tab, text=" Live Ticker", image=self.icon_live, compound=tk.LEFT)
            self.notebook.add(self.relic_finder_tab, text=" Relic Finder", image=self.icon_relic, compound=tk.LEFT)
            self.notebook.add(self.resource_tracker_tab, text=" Resource Tracker", image=self.icon_resources, compound=tk.LEFT)
            
            self.initial_load()
            self.start_live_data_updater()
            self.relic_finder_tab.load_all_relics_threaded()
            self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def upsert_junctions(self):
            """Fügt die Junctions manuell zur Datenbank hinzu, da sie in der API fehlen."""
            JUNCTION_MASTERY = 1000
            JUNCTIONS = [
                "Venus Junction", "Mercury Junction", "Mars Junction", "Phobos Junction",
                "Ceres Junction", "Jupiter Junction", "Europa Junction", "Saturn Junction",
                "Uranus Junction", "Neptune Junction", "Pluto Junction", "Eris Junction",
                "Sedna Junction", "Earth Junction"
            ]
            rows = []
            for name in JUNCTIONS:
                uid = "JUNC_" + name.replace(" ", "_").upper()
                # Junctions haben keine Steel Path Mastery
                rows.append((uid, name, "Junctions", 8, JUNCTION_MASTERY, JUNCTION_MASTERY))


            cur = self.conn.cursor()
            cur.executemany("""
                INSERT INTO nodes (uniqueName, name, systemName, nodeType, mastery_points, steel_path_mastery_points)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(uniqueName) DO NOTHING
            """, rows)
            self.conn.commit()
            print(f"Upserted {len(JUNCTIONS)} junctions.")
            
    def heal_zero_mastery_nodes(self):
            """
            Setzt steel_path_mastery_points = mastery_points für alle Nicht-Junctions,
            wo aktuell steel_path_mastery_points = 0 ist.
            """
            cur = self.conn.cursor()
            cur.execute("""
                UPDATE nodes
                   SET steel_path_mastery_points = mastery_points
                 WHERE steel_path_mastery_points = 0
                   AND mastery_points > 0
                   AND (nodeType != 8 AND LOWER(name) NOT LIKE '%junction%')
            """)
            changed = cur.rowcount or 0
            self.conn.commit()

            if changed > 0:
                self.update_status_bar(f"Healed {changed} nodes with missing Steel Path XP.")
    
    def _on_tab_changed(self, event):
            """Called whenever the user selects a new tab."""
            selected_tab_widget_name = event.widget.select()
            # Check if the newly selected tab is the resource tracker tab
            if selected_tab_widget_name == str(self.resource_tracker_tab):
                self.resource_tracker_tab.start_calculation()

    def _live_data_loop(self):
        WORLDSTATE_URL = "https://oracle.browse.wf/worldState.json"
        CYCLE_API_URL = "https://api.warframestat.us/pc"
        headers = {'Accept-Language': 'en'}

        while True:
            try:
                self.update_status_bar("Fetching live worldstate data...")

                # --- Schritt 1: Lade die Basis-Daten ---
                worldstate_data = safe_get_json(WORLDSTATE_URL, headers=headers)

                # --- Schritt 2: Lade die Zusatz-Daten ---
                endpoints_to_merge = ['cetusCycle', 'vallisCycle', 'cambionCycle', 'nightwave']
                for endpoint in endpoints_to_merge:
                    try:
                        cycle_data = safe_get_json(f"{CYCLE_API_URL}/{endpoint}", headers=headers)
                        worldstate_data[endpoint] = cycle_data
                    except Exception:
                        worldstate_data[endpoint] = None

                # --- Schritt 3: Übergib die Daten an die UI ---
                self.root.after(0, self.live_ticker_tab.update_worldstate, worldstate_data)
                self.update_status_bar("Live data updated. Next update in 5 minutes.")

            except Exception as e:
                self.update_status_bar(f"Error fetching live data: {e}")

            time.sleep(300)  # 5 minutes

    def _load_recipes_data(self):
        RECIPES_URL = "https://browse.wf/warframe-public-export-plus/ExportRecipes.json"
        self.update_status_bar("Downloading recipe data...")
        try:
            raw_recipes = safe_get_json(RECIPES_URL)
            
            # --- NEU: Erstelle ein Set aller uniqueNames, die als Komponenten dienen ---
            self.update_status_bar("Building component reference set...")
            component_unames = set()
            for recipe in raw_recipes.values():
                for ingredient in recipe.get('ingredients', []):
                    # Wir wollen nur echte Items, keine Ressourcen wie Ferrit
                    # Echte Items haben oft diesen Pfad im uniqueName
                    ingredient_uname = ingredient.get('ItemType', '')
                    if '/Lotus/Types/Items/' in ingredient_uname or '/Lotus/Weapons/' in ingredient_uname:
                        component_unames.add(ingredient_uname)
            self.component_item_uniquenames = component_unames
            
            # Re-key the dictionary by the item it PRODUCES for easy lookup
            for bp_name, recipe in raw_recipes.items():
                if 'resultType' in recipe:
                    self.recipes_data[recipe['resultType']] = recipe
                
            self.update_status_bar("Recipe data loaded successfully.")
        except Exception as e:
            self.update_status_bar(f"Failed to load recipe data: {e}")

    def start_live_data_updater(self): threading.Thread(target=self._live_data_loop, daemon=True).start()
    def setup_database(self):
            self.conn = sqlite3.connect(DB_FILE, check_same_thread=False)
            cursor = self.conn.cursor()
            
            # --- Add new columns if they don't exist (for existing users) ---
            try:
                cursor.execute("ALTER TABLE items ADD COLUMN uniqueName TEXT DEFAULT ''")
            except sqlite3.OperationalError:
                pass # Column already exists
            try:
                cursor.execute("ALTER TABLE items ADD COLUMN build_price INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass # Column already exists
            
            # --- Updated CREATE statement for new users ---
            cursor.execute('''CREATE TABLE IF NOT EXISTS items (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                name TEXT NOT NULL UNIQUE,
                                uniqueName TEXT NOT NULL UNIQUE,
                                category TEXT NOT NULL,
                                mastery_rank INTEGER DEFAULT 0,
                                status TEXT DEFAULT 'Missing',
                                mastery_points INTEGER DEFAULT 0,
                                description TEXT,
                                image_name TEXT,
                                components TEXT,
                                build_price INTEGER DEFAULT 0
                            )''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS nodes (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                uniqueName TEXT NOT NULL UNIQUE,
                                name TEXT NOT NULL,
                                systemName TEXT NOT NULL,
                                nodeType INTEGER NOT NULL,
                                mastery_points INTEGER NOT NULL,
                                steel_path_mastery_points INTEGER NOT NULL,
                                status INTEGER DEFAULT 0 NOT NULL 
                            )''') # 0 = Incomplete, 1 = Normal, 2 = Steel Path
            self.conn.commit()
    def initial_load(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(id) FROM items")
        item_count = cursor.fetchone()[0]
        
        if item_count == 0:
            def full_import():
                self.update_status_bar("Starting full database import...")
                # --- KORREKTUR: Übergebe 'self' (die App-Instanz) an die Funktion ---
                populate_database_from_api(self, self.conn, self.update_status_bar)
                
                populate_nodes_from_api(self.conn, self.update_status_bar) 
                self.upsert_junctions() 
                populate_nodes_mastery_from_public_export(self.conn, self.update_status_bar)
                download_all_images(self.conn, self.update_status_bar)
                download_planet_images(self.update_status_bar)
                self.update_status_bar("Full import complete. Finalizing...")

            import_thread = threading.Thread(target=full_import, daemon=True)
            import_thread.start()
            self.root.after(100, self.check_import_thread, import_thread)
        else: 
            # Auch für bestehende DBs müssen wir die Namens-Karte füllen
            threading.Thread(target=populate_database_from_api, 
                             args=(self, self.conn, self.update_status_bar), 
                             daemon=True).start()
            
            self.upsert_junctions()
            populate_nodes_mastery_from_public_export(self.conn, self.update_status_bar)
            self.heal_zero_mastery_nodes()
            threading.Thread(target=download_planet_images, 
                             args=(self.update_status_bar,), 
                             daemon=True).start()
            self.update_status_bar("Database loaded. Ready.")
            self.finalize_load()
        
        recipe_thread = threading.Thread(target=self._load_recipes_data, daemon=True)
        recipe_thread.start()
                
    def check_import_thread(self, thread):
        if thread.is_alive(): self.root.after(100, self.check_import_thread, thread)
        else: self.root.after(500, self.finalize_load)
    
    def finalize_load(self):
        self.update_status_bar("Building name cache...")
        self.full_item_name_map['/Lotus/Types/Items/MiscItems/Credits'] = "Credits"
        self.mastery_tracker_tab.display_items("Gesamtübersicht")
        self.root.after(200, self.update_all_summaries)
        self.update_status_bar("Application loaded successfully.")

    def update_all_summaries(self): 
            self.dashboard_tab.update_display()
            self.mastery_tracker_tab.update_summary_display()
            self.resource_tracker_tab.start_calculation()


    def calculate_total_xp(self):
            cursor = self.conn.cursor()
            
            # 1. XP von Items
            cursor.execute("SELECT SUM(mastery_points) FROM items WHERE status = 'Mastered'")
            item_xp = cursor.fetchone()[0] or 0
            
            # 2. XP von normalen Node-Abschlüssen
            # (Jeder Node mit Status 1 ODER 2 zählt)
            cursor.execute("SELECT SUM(mastery_points) FROM nodes WHERE status >= 1")
            normal_node_xp = cursor.fetchone()[0] or 0
            
            # 3. XP von Steel Path Node-Abschlüssen
            # (Nur Nodes mit Status 2 zählen)
            cursor.execute("SELECT SUM(steel_path_mastery_points) FROM nodes WHERE status >= 2")
            steel_path_node_xp = cursor.fetchone()[0] or 0
            
            return item_xp + normal_node_xp + steel_path_node_xp

    def get_status_counts(self, category):
        cur = self.conn.cursor()

        if category == "Star Chart":
            # Nodes zählen (status: 0=Incomplete, 1=Completed, 2=Steel Path)
            cur.execute("SELECT status, COUNT(*) FROM nodes GROUP BY status")
            rows = cur.fetchall()
            counts = {"Incomplete": 0, "Completed": 0, "Steel Path": 0}
            # Falls du ein globales Mapping hast, kann man das auch nutzen:
            int_to_label = {0: "Incomplete", 1: "Completed", 2: "Steel Path"}
            for s, c in rows:
                label = int_to_label.get(s)
                if label:
                    counts[label] += c or 0
            return counts

        # Standardfall: Items zählen – optional nach Kategorie filtern
        base = "SELECT status, COUNT(*) FROM items"
        params = ()
        if category != "Gesamtübersicht":
            base += " WHERE category = ?"
            params = (category,)
        base += " GROUP BY status"
        cur.execute(base, params)
        rows = cur.fetchall()

        counts = {status: 0 for status in STATUS_OPTIONS}
        for status, cnt in rows:
            counts[status] = cnt or 0
        return counts

    def update_status_bar(self, text): self.status_bar.config(text=text)
    def on_closing(self):
        if self.conn:
            self.conn.close()
        self.root.destroy()


if __name__ == "__main__":
    import sv_ttk

    os.makedirs(IMAGE_CACHE_DIR, exist_ok=True)
    root = tk.Tk()
    
    sv_ttk.set_theme("dark")       # <--- Theme set BEFORE
    
    app = WarframeTrackerApp(root) # <--- App created AFTER
    
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()