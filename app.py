############## general packages ##############################
import io
import os
import base64
from initapp import initialize_app
from venv import create
import matplotlib

matplotlib.use('Agg')  # Sicherstellen, dass Agg-Backend verwendet wird
import time
import threading
from threading import Lock
from threading import Thread
import configparser
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import pandas as pd
from flask import Flask, render_template, jsonify
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.io as pio
import asyncio
from flask_apscheduler import APScheduler
from flask import request

####################  Packages from other .py     #################################
from config import Config, config_get, calculate_last_month
from plot import setup_matplotlib_font, generate_chart, create_zeiger_chart, create_tagesverlauf_chart, \
    create_week_chart, create_month_chart
from database import load_or_create_dataframe, scheduled_csv_update, update_csv_if_needed, check_missing_days, \
    scan_folder
from initapp import initialize_app

#####################################################


# Werte aus der Config-Klasse in Flask-Anwendung laden  -  Abruf über app.config
app = initialize_app()
setup_matplotlib_font()

# Globale Variablen
df = pd.DataFrame()  # Globale DataFrame-Variable

services_started = False
lock = threading.Lock()

app.config.from_object(Config)
scheduler = APScheduler()
scheduler.init_app(app)

# Überprüfen und vorhandene Job-Duplikate entfernen
if scheduler.get_job("csv_update"):  # Prüfen, ob der Job bereits geplant ist
    scheduler.remove_job("csv_update")  # Entfernen, falls er existiert

interval = int(config_get('DEFAULT', 'schedule_interval'))
# Scheduler starten (alle 60 Minuten z. B.)
scheduler.add_job(
    id="csv_update",  # ID des Jobs
    func=scheduled_csv_update,  # Funktion, die ausgeführt werden soll
    trigger="interval",  # Trigger-Typ: Intervall
    minutes=interval,  # Intervall in Minuten
    max_instances=1
)


@app.route('/config/slideshow_interval')
def get_interval():
    slideshow_interval = config_get('DEFAULT', 'slideshow_interval')
    return jsonify({'slideshow_interval': slideshow_interval})  # Liefere den Wert als JSON zurück


@app.route("/update_csv", methods=["POST"])
def update_csv_route():
    """
    API-Endpunkt, der überprüft, ob die Daten aktualisiert und die Merged-Datei neu erstellt werden muss.
    """
    input_folder = Config.DEFAULT_CSV_FOLDER  # Ordner mit Eingangsdaten
    output_file = Config.DEFAULT_CSV_STORAGE_PATH  # Final_dataframe-Ausgabedatei

    try:
        update_csv_if_needed(input_folder, output_file)
        return jsonify({"message": "CSV-Datei wurde überprüft und ggf. aktualisiert."}), 200
    except Exception as e:
        return jsonify({"error": f"Fehler bei der Aktualisierung der CSV-Dateien: {str(e)}"}), 500


@app.route('/')
def index():
    # Berechnung der Zeitspanne (z. B. für den letzten Monat)
    start_date, end_date = calculate_last_month()

    # Scan des Zielordners und Berechnung fehlender Tage
    matching_files = scan_folder(Config.DEFAULT_CSV_FOLDER)
    missing_days = check_missing_days(matching_files)

    # Debug-Ausgaben für die Konsole
    print("Startdatum:", start_date)
    print("Enddatum:", end_date)
    print("Fehlende Tage:", missing_days)

    # Lade das Reload-Intervall aus der Konfigurationsdatei
    reload_interval = config_get('DEFAULT', 'reload_interval', 60000)  # Standard: 1 Minute
    print(f"Geladenes Reload-Intervall: {reload_interval} Millisekunden")

    # Grundseite rendern mit allen erforderlichen Daten
    return render_template(
        'index.html',
        reload_interval=reload_interval,  # Übergabe an das Template
        start_date=start_date,
        end_date=end_date,
        missing_days=missing_days
    )


@app.route('/api/dynamischer_inhalt', methods=['GET'])
def dynamischer_inhalt():
    """API-Route für den Abruf von dynamischen Inhalten"""
    missing_days = check_missing_days(scan_folder(Config.DEFAULT_CSV_FOLDER))
    response = jsonify({'missing_days': missing_days})
    response.headers['Cache-Control'] = 'no-store, must-revalidate'  # Kein Zwischenspeichern
    response.headers['Pragma'] = 'no-cache'  # Ältere Browser
    response.headers['Expires'] = '0'  # Immer abgelaufen
    return response


# Dynamische Chart-Routen
@app.route("/load_chart/<chart_type>", methods=["GET"])
def load_chart(chart_type):
    # Map von Chart-Funktionen und Typen
    chart_functions = {
        "zeiger": create_zeiger_chart,
        "tagesverlauf": create_tagesverlauf_chart,
        "week": create_week_chart,
        "month": create_month_chart,
    }

    # Prüfen, ob der `chart_type` existiert
    if chart_type not in chart_functions:
        return jsonify({"error": f"Ungültiger Chart-Typ: {chart_type}"}), 400

    # Gewählte Chart-Funktion holen
    chart_function = chart_functions[chart_type]

    # Chart generieren
    img_base64 = generate_chart(chart_function, Config.DEFAULT_CSV_STORAGE_PATH)
    if not img_base64:
        return jsonify({"error": f"Fehler beim Erstellen des {chart_type}-Charts."}), 500

    base_url = request.script_root

    if base_url != '':
        if base_url[-1] != '/':
            base_url = base_url + "/"

        if base_url.startswith('/'):
            base_url = base_url[1:]

    # Datei speichern
    output_path = f"static/{chart_type}_chart.png"

    try:
        with open(output_path, "wb") as f:
            f.write(base64.b64decode(img_base64))  # Base64-Dekodierung ins PNG-Format
        print(f"Bild erfolgreich gespeichert: {output_path}")
    except Exception as e:
        print(f"Fehler beim Speichern des Bildes: {e}")
        return jsonify({"error": "Fehler beim Speichern des Bildes."}), 500

    # Rückgabe der URL des Bildes nach Erfolg

    output_path = f"{base_url}static/{chart_type}_chart.png"

    return jsonify({"img_url": f"/{output_path}"})


@app.route('/')
def home():
    # Senden der aktuellen Uhrzeit an die HTML Seite
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return render_template('index.html', time=current_time)


###################################################################################################################

###################################################################################################################

debug_value = config_get('DEFAULT', 'debug').lower() == 'true'

###################################################################################################################
if __name__ == '__main__':
    scheduler.start()  # Startet den Scheduler im Hintergrund

    import sys

    # Check if Parameter --docker is set
    print("Überprüfe, ob Docker-Umgebung erkannt wurde...")

    if '--docker' in sys.argv:
        print("Docker-Umgebung erkannt.")
        os.system("pip freeze > /home/meteor/Documents/meteor-webserver/log-out/requirements-backup.txt")


    class XScriptNameMiddleware:
        def __init__(self, app):
            self.app = app

        def __call__(self, environ, start_response):

            script_name = environ.get('HTTP_X_SCRIPT_NAME', '')

            if script_name != '':

                # script_name = script_name + "fail"
                environ['SCRIPT_NAME'] = script_name
                # print(f"X-Script-Name gesetzt: {script_name}")
            else:
                environ['SCRIPT_NAME'] = ''
                # print("Kein X-Script-Name gesetzt.")

            return self.app(environ, start_response)


    app.wsgi_app = XScriptNameMiddleware(app.wsgi_app)
    app.run(host="0.0.0.0", port=5000, debug=debug_value)
