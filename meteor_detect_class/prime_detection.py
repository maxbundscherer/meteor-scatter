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
#import twitchhandler.py

# Einstellungen
FORMAT = pyaudio.paInt16  # Audioformat (16-bit)
CHANNELS = 1              # Stereo-Kanaele
RATE = 44100              # Abtastrate (Hz)
CHUNK = 1024 * 4               # Groesse der Datenbloecke
DURATION = 30             # Aufnahmedauer in Sekunden
FILENAME = "loopback_recording.wav"  # Datei, in der die Aufnahme gespeichert wird
DISPLAY = False

audio_grabber = twitchrealtimehandler.TwitchAudioGrabber(
    twitch_url="https://www.twitch.tv/astronomiemuseum",
    blocking=True,  # wait until a segment is available
    segment_length=30,  # segment length in seconds
    rate=5000,  # sampling rate of the audio
    channels=1,  # number of channels
    dtype=np.int16  # quality of the audio could be [np.int16, np.int32, np.float32, np.float64]
    )


def load_wav(filename):
    with wave.open(filename, 'r') as wav_file:
        params = wav_file.getparams()
        num_channels = params.nchannels
        sample_width = params.sampwidth
        frame_rate = params.framerate
        num_frames = params.nframes
        
        raw_data = wav_file.readframes(num_frames)
        total_samples = num_frames * num_channels
        
        if sample_width == 2:
            fmt = f"{total_samples}h"
        else:
            raise ValueError("Unsupported sample width")
        
        integer_data = struct.unpack(fmt, raw_data)
        audio_data = np.array(integer_data).reshape(-1, num_channels)
        
        return audio_data, frame_rate
    
def plot_spectrogram(iq_segment, fs, display = True, vmin=10, vmax=30):
    #Um Rauschgrund zu entfernen wird die Rauschleistung berechnet:
    NFFT = 2048
    delta_f = fs / NFFT #Frequenzaufloesung im Spectrogramm und fuer die Rauschberechnung

    Pxx, freqs, bins, im = plt.specgram(iq_segment[:, 0], Fs=fs, NFFT=NFFT, noverlap=NFFT//2) #29 40,vmin=29, vmax=40
    #Frequenzbereich in dem nur Rauschen vorkommt und keine Bursts
    lower_freq = 250 
    upper_freq = 800 
    noise_band = (freqs >= lower_freq) & (freqs <= upper_freq)
    #Bandbreite fuer das Frequenzband
    bandwidth = np.sum(noise_band) * delta_f #Bandbreite in Hz

    #Gesamte Leistung in diesem Frequenzband
    band_power = np.sum(Pxx[noise_band]) # Summe der Leistung im Frequenzband
    power_density_db_hz = 10*np.log10(band_power/bandwidth)
    factor = 40/23


    #db-Werte in Pxx umrechnen
    Pxx_db = 10*np.log10(Pxx) # in dB
    Pxx_db[np.isinf(Pxx_db)] = -np.inf

    
    plt.imshow(Pxx_db, aspect='auto', origin='lower', extent=[bins[0], bins[-1], freqs[0], freqs[-1]], vmin = power_density_db_hz/factor+3, vmax=40)
    #plt.xlabel('Time [s]')
    #plt.ylabel('Frequency [Hz]')
    #plt.title('Spectrogram 25 Seconds')
    plt.ylim(800, 1200)  # Frequenzbereich von 0 bis 2000 Hz
    #plt.colorbar(label='Leistung/Frequenz (dB/Hz)')
    fig = plt.axis('off')
    #plt.tight_layout()
    plt.savefig('spectrogram2.jpg', format='jpg', bbox_inches='tight', pad_inches=0)
    if display:
        plt.show()
    #plt.show(block=False)
    del Pxx, Pxx_db, band_power
    plt.close()

def list_audio_devices():
    #Liste alle verfuegbaren Audioeingabegeraete auf.
    audio = pyaudio.PyAudio()
    print('Verfuegbare Audiogeraete:')
    for i in range(audio.get_device_count()):
        device = audio.get_device_info_by_index(i)
        print(f"Index {i}: {device['name']} - {device['maxInputChannels']} Eingaenge, {device['maxOutputChannels']} Ausgaenge")
    audio.terminate()

def record_loopback(device_index):
    """Zeichnet Audio vom angegebenen Geraet auf."""
    audio = pyaudio.PyAudio()

    # Oeffne den Stream
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        input_device_index=device_index,
                        frames_per_buffer=CHUNK)

    # Oeffne die WAV-Datei zum Schreiben
    wf = wave.open(FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)

    print("Aufnahme gestartet...")
    for _ in range(0, int(RATE / CHUNK * DURATION)):
        data = stream.read(CHUNK, exception_on_overflow=False)
        wf.writeframes(data)  # Schreibe Frames direkt in die Datei
    print("Aufnahme beendet.")

    # Schliesse den Stream und die Datei
    stream.stop_stream()
    stream.close()
    audio.terminate()
    wf.close()

    print(f"Audio erfolgreich gespeichert in {FILENAME}")

#audio_segment = audio_grabber.grab()

# Liste alle verfuegbaren Geraete
#list_audio_devices()

# Waehle den Index des Loopback-Geraets aus
#device_index = int(input("Gib den Index des Loopback-Geraets ein: "))
#record_loopback(device_index)

#iq_data, fs = load_wav(FILENAME)
#print(type(iq_data))
#print(iq_data.shape)
#print(iq_data[:10])
#raise Exception("Stop")
#iq_segment = iq_data
fs = 5000
n_critical = 0
n_non_critical = 0


start_time= datetime.now()   # Startzeit
start_time1 = datetime.now()
save_interval = timedelta(minutes=59.8)  # Intervall von 1h
save_interval2 = timedelta(hours=24) #Intervall von 24 h

previous_date = datetime.now().strftime('%Y-%m-%d')
#output_file = "values_sum.txt"  # Datei zum Speichern der Summe
# Aktuelles Datum im Format YYYYMMDD
date_string = datetime.now().strftime("%Y%m%d")
separator = ";"
# Dateiname basierend auf dem aktuellen Datum
file_name = f"C:/Users/sebik/Desktop/Meteor-Projekt/WebsiteProjekt/pythonProject/pythonProject/csv_files/{date_string}.csv"
columns = ["Timestamp", "Anzahl", "Kritisch"]
df = pd.DataFrame(columns=columns)
df.to_csv(file_name,sep=separator, index=False)
print(f"Die CSV-Datei '{file_name}' wurde erfolgreich erstellt.")


while True:
    current_date = datetime.now().strftime('%Y-%m-%d')
    print(f"Startzeit: {start_time}\n")

    # Schritt 1: Audiosegment erfassen
    try:
        print("Starte Audioaufnahme...")
        audio_segment = audio_grabber.grab()
        print("Audioaufnahme abgeschlossen.")
    except Exception as e:
        print(f"Fehler bei der Audioaufnahme: {e}")
        time.sleep(5)  # Wartezeit bei Fehlern
        continue
    print(f"Audiosegment Größe: {audio_segment.shape}")
    if audio_segment.shape[0] !=  150000:
        print("Fehler: Das Audiosegment ist leer.")
        audio_grabber.terminate()
        audio_grabber = twitchrealtimehandler.TwitchAudioGrabber(
            twitch_url="https://www.twitch.tv/astronomiemuseum",
            blocking=True,  # wait until a segment is available
            segment_length=30,  # segment length in seconds
            rate=5000,  # sampling rate of the audio
            channels=1,  # number of channels
            dtype=np.int16  # quality of the audio could be [np.int16, np.int32, np.float32, np.float64]
            )
        continue
    # Schritt 2: Spektrogramm plotten
    print("Erstelle Spektrogramm...")
    plot_spectrogram(audio_segment, fs, DISPLAY)
    print("Spektrogramm wurde erstellt.")

    # Audioaufnahme-Objekt beenden
    #audio_grabber.terminate()
    print("Audioaufnahme beendet.\n")
    del audio_segment


    # Schritt 3: Burst-Erkennung und Clusterbildung
    image_path1 = "spectrogram2.jpg"
    print("Starte Burst-Erkennung und Clusterbildung...")
    bursts, unique_labels, burst_positions, critical_bursts, non_critical_bursts = detection.detect_and_cluster_bursts(image_path1, display=DISPLAY)
    print("Burst-Erkennung und Clusterbildung abgeschlossen.")

    # Schritt 4: Ergebnisse aktualisieren
    n_critical += len(critical_bursts)
    n_non_critical += len(non_critical_bursts)
    print(f"Anzahl kritischer Bursts in dieser Stunde: {n_critical}")
    print(f"Anzahl nicht kritischer Bursts in dieser Stunde: {n_non_critical}\n")

    # Schritt 5: Ueberpruefen, ob 1 Stunden vergangen ist
    if datetime.now()  - start_time >= save_interval:
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
        df2.to_csv(file_name,sep=separator, index=False)
        
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
        file_name = f"C:/Users/sebik/Desktop/Meteor-Projekt/WebsiteProjekt/pythonProject/pythonProject/csv_files/{date_string}.csv"
        columns = ["Timestamp", "Anzahl", "Kritisch"]
        df = pd.DataFrame(columns=columns)
        df.to_csv(file_name,sep=separator, index=False)
        print(f"Die CSV-Datei '{file_name}' wurde erfolgreich erstellt.")
        # Zurücksetzen der Summen und Aktualisieren der Startzeit
        n_critical = 0
        n_non_critical = 0
        start_time1 = datetime.now()
        print("Summen zurückgesetzt und Startzeit aktualisiert.\n")
