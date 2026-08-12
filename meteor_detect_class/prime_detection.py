import pyaudio
import wave
import time
import csv
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
import struct
import twitchrealtimehandler
import detector_and_classification as detection
import os
import shutil

# TODO ALERTS

C_FILE_PATH_OUT = "/home/meteor/Documents/meteor-detection/csv-out/"  # TODO CSV OUT PATH
C_FILE_PATH_OUT_SPEC = "/home/meteor/Documents/meteor-detection/spec-out/"  # TODO SPEC OUT PATH

# C_MS_SPEC_CUT_FACTOR = 8  # TODO Noise Filter
C_MS_SPEC_CUT_FACTOR = 12  # TODO Noise Filter

C_MS_CLUSTER_MIN_SAMPLES = 5  # TODO Cluster Filter
C_MS_CLUSTER_EPSILON = 30  # TODO Cluster Filter

C_FILE_PATH_SPEC = "/tmp/spectrogram2.jpg"
C_FILE_PATH_SPEC_DEBUG_NO_VMIN = "/tmp/spectrogram2-no-vmin.jpg"
C_FILE_PATH_SPEC_DETECTED = "/tmp/spectrogram2-detected.jpg"
C_DISPLAY = False
C_SAMPLE_RATE = 5000
C_SEG_LEN = 30

# Assert Env
assert os.path.exists(C_FILE_PATH_OUT), f"Path not found: {C_FILE_PATH_OUT}"
assert os.path.exists(C_FILE_PATH_OUT_SPEC), f"Path not found: {C_FILE_PATH_OUT_SPEC}"

# Time Measurement
time_meas_dict = {}


def start_time_meas(idk: str):
    time_meas_dict[idk] = datetime.now()


def end_time_meas(idk: str):
    # and print in seconds
    time = datetime.now() - time_meas_dict[idk]
    print(f"Time for {idk}: {time.total_seconds()} seconds")


# Augio Grabber
audio_grabber = twitchrealtimehandler.TwitchAudioGrabber(
    twitch_url="https://www.twitch.tv/astronomiemuseum",
    # twitch_url="https://www.twitch.tv/noway4u_sir",
    blocking=True,  # wait until a segment is available
    segment_length=C_SEG_LEN,  # segment length in seconds
    rate=C_SAMPLE_RATE,  # sampling rate of the audio
    channels=1,  # number of channels
    dtype=np.int16  # quality of the audio could be [np.int16, np.int32, np.float32, np.float64]
)


# Proc Spec
def plot_spectrogram(iq_segment, fs, display=True, vmin=10, vmax=30):
    # Um Rauschgrund zu entfernen wird die Rauschleistung berechnet:
    NFFT = 2048
    delta_f = fs / NFFT  # Frequenzaufloesung im Spectrogramm und fuer die Rauschberechnung

    Pxx, freqs, bins, im = plt.specgram(iq_segment[:, 0], Fs=fs, NFFT=NFFT,
                                        noverlap=NFFT // 2)  # 29 40,vmin=29, vmax=40
    # Frequenzbereich in dem nur Rauschen vorkommt und keine Bursts
    lower_freq = 250
    upper_freq = 800
    noise_band = (freqs >= lower_freq) & (freqs <= upper_freq)
    # Bandbreite fuer das Frequenzband
    bandwidth = np.sum(noise_band) * delta_f  # Bandbreite in Hz

    # epsilon = 1e-10
    # Pxx += epsilon

    # Gesamte Leistung in diesem Frequenzband
    band_power = np.sum(Pxx[noise_band])  # Summe der Leistung im Frequenzband
    power_density_db_hz = 10 * np.log10(band_power / bandwidth)
    factor = 40 / 23

    # db-Werte in Pxx umrechnen
    Pxx_db = 10 * np.log10(Pxx)  # in dB
    Pxx_db[np.isinf(Pxx_db)] = -np.inf

    temp_vmin = power_density_db_hz / factor + C_MS_SPEC_CUT_FACTOR
    tmp_vmax = 40

    print("My current vmin is: ", temp_vmin)

    plt.imshow(Pxx_db, aspect='auto', origin='lower', extent=[bins[0], bins[-1], freqs[0], freqs[-1]],
               vmin=temp_vmin, vmax=tmp_vmax)
    # plt.xlabel('Time [s]')
    # plt.ylabel('Frequency [Hz]')
    # plt.title('Spectrogram 25 Seconds')
    plt.ylim(800, 1200)  # Frequenzbereich von 0 bis 2000 Hz
    # plt.colorbar(label='Leistung/Frequenz (dB/Hz)')
    fig = plt.axis('off')
    # plt.tight_layout()
    plt.savefig(C_FILE_PATH_SPEC, format='jpg', bbox_inches='tight', pad_inches=0)

    plt.figure()
    plt.imshow(Pxx_db, aspect='auto', origin='lower', extent=[bins[0], bins[-1], freqs[0], freqs[-1]],
               vmax=tmp_vmax)
    plt.ylim(800, 1200)
    plt.axis('off')
    plt.savefig(C_FILE_PATH_SPEC_DEBUG_NO_VMIN, format='jpg', bbox_inches='tight', pad_inches=0)

    if display:
        plt.show()
    # plt.show(block=False)
    del Pxx, Pxx_db, band_power
    plt.close('all')


# Process Loop

fs = C_SAMPLE_RATE
n_critical = 0
n_non_critical = 0

start_time = datetime.now()  # Startzeit
start_time1 = datetime.now()
save_interval = timedelta(minutes=59.8)  # Intervall von 1h
save_interval2 = timedelta(hours=24)  # Intervall von 24 h

previous_date = datetime.now().strftime('%Y-%m-%d')
# Aktuelles Datum im Format YYYYMMDD
date_string = datetime.now().strftime("%Y%m%d")
separator = ";"
# Dateiname basierend auf dem aktuellen Datum
file_name = f"{C_FILE_PATH_OUT}{date_string}.csv"
columns = ["Timestamp", "Anzahl", "Kritisch"]
df = pd.DataFrame(columns=columns)
# Pruefen, ob die Datei bereits existiert
if not os.path.exists(file_name):
    # Datei existiert nicht, also erstellen
    df.to_csv(file_name, sep=separator, index=False)
    print(f"Datei {file_name} wurde erstellt.")
else:
    print(f"Datei {file_name} existiert bereits.")

while True:
    current_date = datetime.now().strftime('%Y-%m-%d')
    log_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    print()
    print("[INFO] Starte neuen Durchlauf...")
    print(f"Startzeit: {start_time} / Current Date {current_date} / Current Time {log_time_str}\n")

    # time.sleep(2)
    # raise Exception("Test Error")

    # Schritt 1: Audiosegment erfassen
    start_time_meas("grab_audio")
    try:
        print("Starte Audioaufnahme...")
        audio_segment = audio_grabber.grab()
        print("Audioaufnahme abgeschlossen.")
    except Exception as e:
        print(f"Fehler bei der Audioaufnahme: {e}")
        time.sleep(5)  # Wartezeit bei Fehlern
        continue
    print(f"Audiosegment Größe: {audio_segment.shape}")
    if audio_segment.shape[0] != C_SEG_LEN * C_SAMPLE_RATE:
        try:
            print("Fehler: Das Audiosegment ist fehlerhaft. Starte Stream neu...")
            try:
                audio_grabber.terminate()
            except Exception as e:
                print(f"Fehler beim Terminieren des alten Streams: {e}")
            time.sleep(5)
            audio_grabber = twitchrealtimehandler.TwitchAudioGrabber(
                twitch_url="https://www.twitch.tv/astronomiemuseum",
                blocking=True,  # wait until a segment is available
                segment_length=C_SEG_LEN,  # segment length in seconds
                rate=C_SAMPLE_RATE,  # sampling rate of the audio
                channels=1,  # number of channels
                dtype=np.int16  # quality of the audio could be [np.int16, np.int32, np.float32, np.float64]
            )

            print("Neuer Stream wurde gestartet.")
        except Exception as e:
            print(f"Fehler beim Neustart des Streams: {e}")
            # TODO HANDLING - now via watchog
            time.sleep(5)
            raise Exception("Fehler beim Neustart des Streams !!!")
        continue
    end_time_meas("grab_audio")

    # Schritt 2: Spektrogramm plotten
    start_time_meas("plot_spectrogram")
    print("Erstelle Spektrogramm...")
    plot_spectrogram(audio_segment, fs, C_DISPLAY)
    print("Spektrogramm wurde erstellt.")
    del audio_segment
    end_time_meas("plot_spectrogram")

    # Schritt 3: Burst-Erkennung und Clusterbildung
    start_time_meas("detect_and_cluster_bursts")
    image_path1 = C_FILE_PATH_SPEC
    print("Starte Burst-Erkennung und Clusterbildung...")
    bursts, unique_labels, burst_positions, critical_bursts, non_critical_bursts = detection.detect_and_cluster_bursts(
        image_path1, display=C_DISPLAY, eps=C_MS_CLUSTER_EPSILON, min_samples=C_MS_CLUSTER_MIN_SAMPLES,
        output_path=C_FILE_PATH_SPEC_DETECTED)
    print("Burst-Erkennung und Clusterbildung abgeschlossen.")
    end_time_meas("detect_and_cluster_bursts")

    # Schritt 4: Ergebnisse aktualisieren
    n_critical += len(critical_bursts)
    n_non_critical += len(non_critical_bursts)
    print(f"Anzahl kritischer Bursts in dieser Stunde: {n_critical}")
    print(f"Anzahl nicht kritischer Bursts in dieser Stunde: {n_non_critical}")
    if len(critical_bursts) > 0 or len(non_critical_bursts) > 0:
        # Copy spec to out
        print("Kopiere Spektrogramm... (hat etwas detektiert)")
        spec_fp_timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        spec_fp_prefix = f"{C_FILE_PATH_OUT_SPEC}{spec_fp_timestamp}-{len(critical_bursts)}-{len(non_critical_bursts)}"
        shutil.copy(C_FILE_PATH_SPEC, f"{spec_fp_prefix}.jpg")
        shutil.copy(C_FILE_PATH_SPEC_DEBUG_NO_VMIN, f"{spec_fp_prefix}-debug-no-vmin.jpg")
        shutil.copy(C_FILE_PATH_SPEC_DETECTED, f"{spec_fp_prefix}-detected.jpg")

    # Schritt 5: Ueberpruefen, ob 1 Stunden vergangen ist
    if datetime.now() - start_time >= save_interval:
        print("Speichere Ergebnisse...")
        # Zeitstempel für die CSV-Datei ohne Millisekunden formatieren
        formatted_timestamp = start_time.strftime("%Y-%m-%d %H:%M:%S")
        new_row = {"Timestamp": formatted_timestamp, "Anzahl": n_critical + n_non_critical, "Kritisch": n_critical}

        # Bestehende Datei einlesen
        df2 = pd.read_csv(file_name, sep=separator)

        # Neue Zeile als DataFrame erstellen
        new_row_df = pd.DataFrame([new_row])

        # Zusammenfügen des bestehenden DataFrames und der neuen Zeile
        df2 = pd.concat([df2, new_row_df], ignore_index=True)  # Hier wird `pd.concat` verwendet

        # DataFrame speichern
        df2.to_csv(file_name, sep=separator, index=False)

        print(f"Neue Zeile hinzugefügt: {start_time}")

        # Variablen zurücksetzen
        n_critical = 0
        n_non_critical = 0
        start_time = datetime.now()

    # Schritt 6: Ueberpruefen, ob 24 Stunden vergangen sind
    if current_date != previous_date:
        previous_date = current_date
        print("Neuer Tag, lege neues csv-file an...")
        # Aktuelles Datum im Format YYYYMMDD
        date_string = datetime.now().strftime("%Y%m%d")
        # Dateiname basierend auf dem aktuellen Datum
        file_name = f"{C_FILE_PATH_OUT}{date_string}.csv"
        columns = ["Timestamp", "Anzahl", "Kritisch"]
        df = pd.DataFrame(columns=columns)
        df.to_csv(file_name, sep=separator, index=False)
        print(f"Die CSV-Datei '{file_name}' wurde erfolgreich erstellt.")
        # Zurücksetzen der Summen und Aktualisieren der Startzeit
        n_critical = 0
        n_non_critical = 0
        start_time1 = datetime.now()
        print("Summen zurückgesetzt und Startzeit aktualisiert.\n")
