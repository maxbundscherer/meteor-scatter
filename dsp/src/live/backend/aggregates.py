from dataclasses import dataclass


@dataclass
class State:
    pass


@dataclass
class StateInitialization(State):
    history_channel_dB: [float]


@dataclass
class StateDetection(State):
    locked_threshold: float = -1.0
    use_locked_threshold_until_secs: float = -1.0


@dataclass
class StateTracking(State):
    locked_threshold: float
    time_start_detection: float
    history_over_noise_sig_dB: [float]


@dataclass
class Config:
    pass


@dataclass
class ConfigDetection(Config):
    proc_block_sec: float = 0.2  # Blockgröße in Sekunden (0.5 = 500ms)
    n_fft: int = 4096  # Anzahl der FFT-Punkte für PSD, Wasserfall und dB Berechnung
    signal_freq: int = 1000  # Annahme der Frequenz in Hz
    channel_width: int = 100  # Kanalbreite um Frequenz in Hz
    noise_channel_offset: int = 300  # Kanaloffset für Rauschberechnung in Hz
    avg_win_sec: float = 8  # Zeitfenster für Mittelwertbildung in Sekunden
    init_detection_wait_sec: float = 8 * 1.0  # Wartezeit für Initialisierung in Sekunden
    after_tracking_wait_sec: float = 8 * 1.5  # Wartezeit nach Tracking in Sekunden für neue Schwellwertbildung
    threshold_std_factor: float = 4  # Faktor für Standardabweichung für Schwellwertbildung
    detection_db_over_noise_mean_min: float = -1  # Min DB über Rauschen
    detection_dur_min_sec: float = -1  # Mindestzeit für Meteor in Sekunden


@dataclass
class ConfigVisualization(Config):
    enable_ui_plots: bool = True  # UI-Plots aktivieren
    realtime_factor: float = 16  # 1 = Echtzeit, 2 = Doppelte Geschwindigkeit, 0.5 = Halbe Geschwindigkeit (nur UI)
    flag_realtime_animation: bool = True  # Echtzeit-Anzeige (nur UI) verzögert
    max_range_sec: int = 60  # Max. Länge für Länge Wasserfall und dB-Plots in Sekunden (auch für Export relevant, nicht zu klein setzen!)
    limit_freq_offset_wf2_and_export: int = 100  # Frequenzoffset in Hz von Sig Freq für den zweiten Wasserfallplot und Export
    wf_offset_vmin: int = 20  # Offset für vmin im Wasserfallplot dB (Wasserfall und Export)
    wf_offset_vmax: int = 20  # Offset für vmax im Wasserfallplot dB (Wasserfall und Export)
    enable_debug_logs: bool = False  # Debug-Logs aktivieren


@dataclass
class ConfigSpecExport(Config):
    output_dir: str = ""  # Output Directory - set to "" to disable
    time_before_meteor_sec: int = 3  # Zeit vor Meteor in Sekunden
    time_after_meteor_sec: int = 3


@dataclass
class DetectedMeteor:
    time_start: float
    time_stop: float
    duration: float
    db_min: float
    db_max: float
    db_mean: float
    db_std: float
