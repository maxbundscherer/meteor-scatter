import io
import os
import base64
from venv import create
import matplotlib

matplotlib.use('Agg')  # Sicherstellen, dass Agg-Backend verwendet wird
import time
import threading
from threading import Lock
from threading import Thread
import configparser
import matplotlib.pyplot as plt
import logging
from matplotlib.dates import DateFormatter
import pandas as pd
from flask import Flask, render_template, jsonify
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.io as pio
import asyncio
from flask_apscheduler import APScheduler

###############################################################################################
# configparser für config.ini laden mit fallback Werten versehen
config = configparser.ConfigParser()


############################ konfigdatei laden    ######################################

class Config:
    # Fallback-Werte setzen
    DEFAULT_SECTION = "DEFAULT"

    # Dynamisch ermitteln, wo der Hauptordner liegt
    # BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DEFAULT_CSV_FOLDER = "/home/meteor/Documents/meteor-detection/csv-out/"  # TODO Change this
    DEFAULT_CSV_STORAGE_PATH = "final_dataframe.csv"

    DEFAULT_DEBUG = False
    DEFAULT_UNDERE_GRENZE = 0
    DEFAULT_OBERE_GRENZE = 300
    DEFAULT_TITLE_FONT_SIZE = 55
    DEFAULT_FONT_COLOR = "black"
    DEFAULT_FONT_WEIGHT = "normal"
    DEFAULT_FONT_STYLE = "normal"
    DEFAULT_ANZAHL_INTERVALLE = 55
    DEFAULT_AKTUALISIERUNGSZEIT = 5
    DEFAULT_RELOAD_INTERVAL = 1200
    DEFAULT_TITLE_PADDING = 21
    DEFAULT_SCHEDULE_INTERVAL = 60

    PLOT_SETTINGS_SECTION = "PlotSettings"

    PLOT_SETTINGS_FONT_SIZE = 16
    PLOT_SETTINGS_TITLE_FONT_SIZE = 20

    SCHEDULER_API_ENABLE = True


CURRENT_DF = None

###################################################################

# Logging-Einstellungen
logging.basicConfig(
    level=logging.INFO,  # Standardmäßiges Log-Level (kann `DEBUG` für detaillierte Logs sein)
    format="%(asctime)s - %(levelname)s - %(message)s",  # Format der Logs
    filename="app.log",  # Logs werden in einer Datei gespeichert
    filemode="w"  # "a" für Anhängen, "w" für Überschreiben der Datei bei jedem Start
)

# Logs in der Konsole ausgeben, StreamHandler hinzufügen:
console = logging.StreamHandler()
console.setLevel(logging.INFO)  # Konsole für nur `INFO`-Level oder höher aktivieren
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console.setFormatter(formatter)
logging.getLogger("").addHandler(console)


###################################################################


def calculate_last_month():
    # Berechnung des aktuellen Zeitraums: 30 Tage bis gestern
    today = datetime.now().date()  # Nur das aktuelle Datum (ohne Uhrzeit) verwenden
    end_date = today - timedelta(days=1)  # Gestern (kalenderbezogen, 0 Uhr)
    start_date = end_date - timedelta(days=30)  # 30 Tage vor gestern (ebenfalls kalenderbezogen)
    return start_date, end_date


def config_get(section, key, fallback=None):
    """
    Liest und konvertiert einen Wert aus der Konfigurationsdatei.
    Gibt den Standardwert (fallback) zurück, wenn der Eintrag fehlt oder ungültig ist.
    """
    try:
        value = config.get(section, key)
        # Konvertiere den Wert in den Typ des Rückfallwertes
        if isinstance(fallback, int):
            return int(value)
        elif isinstance(fallback, float):
            return float(value)
        elif isinstance(fallback, bool):
            return value.lower() in ("true", "1", "yes", "on")  # Boolean-Konvertierung
        else:
            return value  # Standardmäßig als String übernehmen

    except configparser.NoSectionError:
        logging.warning(f"Sektion '{section}' fehlt. Fallback-Wert '{fallback}' wird verwendet.")
        return fallback
    except configparser.NoOptionError:
        logging.warning(f"Schlüssel '{key}' in Sektion '{section}' fehlt. Fallback-Wert '{fallback}' wird verwendet.")
        return fallback
    except ValueError as e:
        logging.error(f"Konvertierungsfehler '{key}': {e}. Fallback-Wert: {fallback}")
        return fallback


def load_config():
    try:
        config.read('config.ini')
        logging.info("Konfigurationsdatei erfolgreich geladen.")  # Erfolgreiche Info-Log-Nachricht
    except Exception as e:
        logging.error(f"Fehler beim Laden der Konfiguration: {e}")  # Fehlerhafte Log-Nachricht
