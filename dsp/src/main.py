import os
from collections import Counter
from dataclasses import dataclass

import numpy as np
import scipy.io.wavfile as wav
import matplotlib.pyplot as plt
from tqdm import tqdm
from scipy.signal import spectrogram
from scipy.signal import welch
import plotly.graph_objects as go
from matplotlib.gridspec import GridSpec

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import spectrogram, welch
import datetime
import matplotlib.ticker as ticker


@dataclass
class Marker:
    color: str
    f_min: float = None
    f_max: float = None
    t_min: float = None
    t_max: float = None


@dataclass
class OutputDetection:
    t_start: float
    t_stop: float
    dur_s: float
    dB: float
    utc_start: datetime.datetime = None
    utc_stop: datetime.datetime = None


def internal_print_spec_and_psd_mod(wav_data, wav_sample_rate, n_fft, eps=1e-10,
                                    freq_min=None, freq_max=None, markers=None,
                                    plt_title=None, plt_filepath=None):
    block_size = n_fft

    # Erstelle GridSpec mit 2 Spalten (70% + 30%)
    fig = plt.figure(figsize=(14, 5))
    gs = GridSpec(1, 2, width_ratios=[7, 3], figure=fig)
    ax_spec = fig.add_subplot(gs[0, 0])
    ax_psd = fig.add_subplot(gs[0, 1])

    # --- Spektrogramm (Wasserfall) ---
    f, t, Sxx = spectrogram(wav_data, fs=wav_sample_rate, window='hann',
                            nperseg=block_size, noverlap=block_size // 2, nfft=n_fft,
                            scaling='density', mode='psd')

    if freq_min is not None and freq_max is not None:
        freq_mask = (f >= freq_min) & (f <= freq_max)
        f = f[freq_mask]
        Sxx = Sxx[freq_mask, :]

    im = ax_spec.pcolormesh(t, f, 10 * np.log10(Sxx + eps), shading='gouraud')
    ax_spec.set_ylabel('Frequenz (Hz)')
    ax_spec.set_xlabel('Zeit (s)')
    ax_spec.set_title('Spektrogramm (Wasserfall)')
    fig.colorbar(im, ax=ax_spec, label='Leistungsdichte [dB/Hz]')

    # Marker für Spektrogramm
    if markers is not None:
        for marker in markers:
            if marker.f_min is not None:
                ax_spec.axhline(y=marker.f_min, color=marker.color, linestyle='--')
            if marker.f_max is not None:
                ax_spec.axhline(y=marker.f_max, color=marker.color, linestyle='--')
            if marker.t_min is not None:
                ax_spec.axvline(x=marker.t_min, color=marker.color, linestyle='--')
            if marker.t_max is not None:
                ax_spec.axvline(x=marker.t_max, color=marker.color, linestyle='--')

    if freq_min is not None and freq_max is not None:
        ax_spec.set_ylim(freq_min, freq_max)
    else:
        ax_spec.set_ylim(0, wav_sample_rate // 2)

    # --- PSD ---
    n_fft = 4096
    block_size = n_fft

    f_psd, Pxx = welch(wav_data, fs=wav_sample_rate, window='hann',
                       nperseg=block_size, noverlap=block_size // 2,
                       nfft=n_fft, scaling='density')

    if freq_min is not None and freq_max is not None:
        psd_mask = (f_psd >= freq_min) & (f_psd <= freq_max)
        f_psd = f_psd[psd_mask]
        Pxx = Pxx[psd_mask]

    Pxx_dB = 10 * np.log10(Pxx + eps)
    ax_psd.plot(f_psd, Pxx_dB)
    ax_psd.set_xlabel('Frequenz (Hz)')
    ax_psd.set_ylabel('PSD [dB]')
    ax_psd.set_title('Power Spectral Density')

    # Marker für PSD
    if markers is not None:
        for marker in markers:
            if marker.f_min is not None:
                ax_psd.axvline(x=marker.f_min, color=marker.color, linestyle='--')
            if marker.f_max is not None:
                ax_psd.axvline(x=marker.f_max, color=marker.color, linestyle='--')

    ax_psd.grid(True)

    if plt_title:
        fig.suptitle(plt_title)
        plt.subplots_adjust(top=0.88)

    plt.tight_layout()

    if plt_filepath is not None:
        plt.savefig(plt_filepath)
    else:
        plt.show()

    plt.close("all")


def internal_print_spec(wav_data, wav_sample_rate, n_fft, eps=1e-10, freq_min=None, freq_max=None, markers=None,
                        plt_title=None, plt_filepath=None):
    block_size = n_fft  # block_size = n_fft
    plt.figure(figsize=(10, 5))

    f, t, Sxx = spectrogram(wav_data, fs=wav_sample_rate, window='hann',
                            nperseg=block_size, noverlap=block_size // 2, nfft=n_fft, scaling='density', mode='psd')

    if markers is not None:
        for marker in markers:
            if marker.f_min is not None:
                plt.axhline(y=marker.f_min, color=marker.color, linestyle='--',
                            label=f'Marker {marker.f_min}-{marker.f_max} Hz')
            if marker.f_max is not None:
                plt.axhline(y=marker.f_max, color=marker.color, linestyle='--')
            if marker.t_min is not None:
                plt.axvline(x=marker.t_min, color=marker.color, linestyle='--',
                            label=f'Marker {marker.t_min}-{marker.t_max} s')
            if marker.t_max is not None:
                plt.axvline(x=marker.t_max, color=marker.color, linestyle='--')

    if freq_min is not None and freq_max is not None:
        freq_mask = (f >= freq_min) & (f <= freq_max)
        f = f[freq_mask]
        Sxx = Sxx[freq_mask, :]

    plt.pcolormesh(t, f, 10 * np.log10(Sxx + eps), shading='gouraud')
    plt.ylabel('Frequenz (Hz)')
    plt.xlabel('Zeit (s)')
    plt.title('Spektrogramm (Wasserfall)')
    if plt_title is not None:
        plt.title(plt_title)
    plt.colorbar(label='Leistungsdichte [dB/Hz]')

    if freq_min is not None and freq_max is not None:
        plt.ylim(freq_min, freq_max)
    else:
        plt.ylim(0, wav_sample_rate // 2)

    plt.tight_layout()
    if plt_filepath is not None:
        plt.savefig(plt_filepath)
    else:
        plt.show()
    plt.close("all")


def internal_print_psd(wav_data, wav_sample_rate, n_fft, eps=1e-10, freq_min=None, freq_max=None, markers=None,
                       plt_title=None):
    block_size = n_fft  # block_size = n_fft
    plt.figure(figsize=(10, 5))

    f_psd, Pxx = welch(wav_data, fs=wav_sample_rate, window='hann',
                       nperseg=block_size, noverlap=block_size // 2, nfft=n_fft, scaling='density')

    if markers is not None:
        for marker in markers:
            if marker.f_min is not None:
                plt.axvline(x=marker.f_min, color=marker.color, linestyle='--',
                            label=f'Marker {marker.f_min}-{marker.f_max} Hz')
            if marker.f_max is not None:
                plt.axvline(x=marker.f_max, color=marker.color, linestyle='--')

    if freq_min is not None and freq_max is not None:
        freq_mask = (f_psd >= freq_min) & (f_psd <= freq_max)
        f_psd = f_psd[freq_mask]
        Pxx = Pxx[freq_mask]

    Pxx_dB = 10 * np.log10(Pxx + eps)
    plt.plot(f_psd, Pxx_dB)
    plt.xlabel('Frequenz (Hz)')
    plt.ylabel('PSD [dB]')
    plt.title('Power Spectral Density (PSD) in dB')
    if plt_title is not None:
        plt.title(plt_title)
    plt.grid(True)
    plt.show()
    plt.close("all")


def proc_wav_file(file_path,
                  block_duration_sec,
                  freq_band,
                  noise_band,
                  n_fft,
                  threshold_std_factor,
                  wav_start_sec=None,
                  wav_end_sec=None,
                  debug_plot_whole=False,
                  debug_plot_config=False,
                  debug_plot_output=False,
                  debug_plot_output_interactive=False,
                  outfile_path=None,
                  out_audacity_lbl_file=None,
                  out_csv_file=None,
                  wav_start_date_time=None,
                  disable_show_and_write=False,
                  flag_adaptive_threshold=True,
                  threshold_estimation_window_sec=120,
                  threshold_freeze_before_detection_sec=3,
                  threshold_freeze_after_detection_sec=20,
                  threshold_fixed_init_duration_sec=10
                  ):
    assert os.path.exists(file_path), f"File does not exist: {file_path}"

    if outfile_path is not None:
        assert os.path.exists(
            os.path.dirname(outfile_path)), f"Output directory does not exist: {os.path.dirname(outfile_path)}"
        now = datetime.datetime.now()
        outfile_path = f"{outfile_path}/{now.strftime('%Y%m%d_%H%M%S')}/"
        os.makedirs(outfile_path, exist_ok=False)

    if out_audacity_lbl_file is not None:
        assert os.path.exists(
            os.path.dirname(
                out_audacity_lbl_file)), f"Output directory does not exist: {os.path.dirname(out_audacity_lbl_file)}"

    if out_csv_file is not None:
        assert os.path.exists(
            os.path.dirname(out_csv_file)), f"Output directory does not exist: {os.path.dirname(out_csv_file)}"

    # Lade WAV-Datei
    wav_sample_rate, wav_data = wav.read(file_path)

    if wav_start_sec is not None or wav_end_sec is not None:
        if wav_start_sec is None:
            wav_start_sec = 0
        if wav_end_sec is None:
            wav_end_sec = len(wav_data) / wav_sample_rate

        start_sample = int(wav_start_sec * wav_sample_rate)
        end_sample = int(wav_end_sec * wav_sample_rate)

        assert start_sample < end_sample, "Start sample must be less than end sample"
        assert end_sample <= len(wav_data), "End sample exceeds length of audio data"

        wav_data = wav_data[start_sample:end_sample]

        del wav_start_sec, wav_end_sec

    assert wav_sample_rate == 6000, f"Sample rate must be 6000 Hz, but got {wav_sample_rate} Hz"
    assert len(wav_data.shape) == 1, f"Data must be mono or stereo, but got shape {wav_data.shape}"

    print("Wav duration [sec]:", len(wav_data) / wav_sample_rate)

    if debug_plot_whole:
        # internal_print_spec(
        #     wav_data=wav_data,
        #     wav_sample_rate=wav_sample_rate,
        #     n_fft=1024 * 4,
        #     # freq_min=freq_band[0] - 50,
        #     # freq_max=freq_band[1] + 50,
        #     markers=[
        #         Marker(f_min=freq_band[0], f_max=freq_band[1], color='red'),
        #         Marker(f_min=noise_band[0], f_max=noise_band[1], color='blue')
        #     ],
        #   plt_title="Spectrogram of the whole wav file"
        # )

        internal_print_spec(
            wav_data=wav_data,
            wav_sample_rate=wav_sample_rate,
            n_fft=1024 * 4,
            freq_min=freq_band[0] - 50,
            freq_max=freq_band[1] + 50,
            markers=[
                Marker(f_min=freq_band[0], f_max=freq_band[1], color='red'),
                Marker(f_min=noise_band[0], f_max=noise_band[1], color='blue')
            ],
            plt_title="Spec Power Band"
        )

        internal_print_spec(
            wav_data=wav_data,
            wav_sample_rate=wav_sample_rate,
            n_fft=1024 * 4,
            freq_min=noise_band[0] - 50,
            freq_max=noise_band[1] + 50,
            markers=[
                Marker(f_min=freq_band[0], f_max=freq_band[1], color='red'),
                Marker(f_min=noise_band[0], f_max=noise_band[1], color='blue')
            ],
            plt_title="Spec Noise Band"
        )

        # internal_print_psd(
        #     wav_data=wav_data,
        #     wav_sample_rate=wav_sample_rate,
        #     n_fft=1024 * 4,
        #     # freq_min=freq_band[0] - 100,
        #     # freq_max=freq_band[1] + 100,
        #     markers=[
        #         Marker(f_min=freq_band[0], f_max=freq_band[1], color='red'),
        #         Marker(f_min=noise_band[0], f_max=noise_band[1], color='blue')
        #     ],
        #   plt_title="Power Spectral Density (PSD) of the whole wav file"
        # )

    if debug_plot_config:
        internal_print_psd(
            wav_data=wav_data,
            wav_sample_rate=wav_sample_rate,
            n_fft=1024 * 4,
            freq_min=freq_band[0] - 100,
            freq_max=freq_band[1] + 100,
            markers=[
                Marker(f_min=freq_band[0], f_max=freq_band[1], color='red'),
                # Marker(f_min=noise_band[0], f_max=noise_band[1], color='blue')
            ],
            plt_title="PSD Power Band"
        )

        internal_print_psd(
            wav_data=wav_data,
            wav_sample_rate=wav_sample_rate,
            n_fft=1024 * 4,
            freq_min=noise_band[0] - 100,
            freq_max=noise_band[1] + 100,
            markers=[
                # Marker(f_min=freq_band[0], f_max=freq_band[1], color='red'),
                Marker(f_min=noise_band[0], f_max=noise_band[1], color='blue')
            ],
            plt_title="PSD Noise Band"
        )

    print("n_fft [real]:", n_fft)
    n_fft = n_fft * 2

    block_size = int(wav_sample_rate * block_duration_sec)
    num_blocks = len(wav_data) // block_size

    print("Set n_fft to:", n_fft, "samples")

    print("Wav block size in samples:", block_size)
    print("Number of wav blocks:", num_blocks)

    freqs = np.fft.rfftfreq(n_fft, d=1 / wav_sample_rate)

    print("Num of freq bins:", len(freqs))
    print("Bandwidth per freq bin [Hz]:", freqs[1] - freqs[0])
    print("Min Frequency [Hz]:", freqs[0])
    print("Max Frequency [Hz]:", freqs[-1])

    print("Power Band bandwidth [Hz]:", freq_band[1] - freq_band[0])
    print("Noise Band bandwidth [Hz]:", noise_band[1] - noise_band[0])

    band_power = []
    noise_power = []

    for i in tqdm(range(num_blocks)):
        block = wav_data[i * block_size: (i + 1) * block_size]

        fft_block = np.fft.rfft(block * np.hanning(len(block)), n=n_fft)
        power_spectrum = np.abs(fft_block) ** 2

        band_mask = (freqs >= freq_band[0]) & (freqs <= freq_band[1])
        band_energy = np.sum(power_spectrum[band_mask]) + 1e-12
        band_power.append(10 * np.log10(band_energy))

        noise_mask = (freqs >= noise_band[0]) & (freqs <= noise_band[1])
        noise_energy = np.sum(power_spectrum[noise_mask]) + 1e-12
        noise_power.append(10 * np.log10(noise_energy))

    assert len(band_power) == num_blocks
    assert len(noise_power) == num_blocks

    delta_power = np.array(band_power) - np.array(noise_power)
    assert len(delta_power) == num_blocks, "Delta power length does not match number of blocks"

    def get_detections():

        # Get peaks with start and stop by delta
        t_delta_mean = np.mean(delta_power)
        t_threshold = t_delta_mean + threshold_std_factor * np.std(delta_power)

        print("Threshold for delta power detection [dB]:", t_threshold)

        # Binärmaske, wo Signal über Schwelle liegt
        above_thresh = delta_power > t_threshold

        # Start- und Endindizes der Bursts
        burst_starts = np.where(np.diff(above_thresh.astype(int)) == 1)[0] + 1
        burst_stops = np.where(np.diff(above_thresh.astype(int)) == -1)[0] + 1

        # Falls Burst am Anfang oder Ende offen ist
        if above_thresh[0]:
            burst_starts = np.insert(burst_starts, 0, 0)
        if above_thresh[-1]:
            burst_stops = np.append(burst_stops, len(delta_power) - 1)

        t_out_det: [OutputDetection] = list()

        # Ausgabe
        for start, stop in zip(burst_starts, burst_stops):
            # print(f"Burst from {start} to {stop}")
            db_meas_range = delta_power[start:stop]
            db_mean = np.mean(db_meas_range)

            t_start = start * block_duration_sec
            t_stop = stop * block_duration_sec
            t_dur = t_stop - t_start

            t_utc_start = None
            t_utc_stop = None

            if wav_start_date_time is not None:
                t_utc_start = wav_start_date_time + datetime.timedelta(seconds=t_start)
                t_utc_stop = wav_start_date_time + datetime.timedelta(seconds=t_stop)
                assert t_utc_start < t_utc_stop, "UTC start time must be before stop time"

            assert t_dur > 0, "Detection duration must be greater than 0"

            t_out_det.append(OutputDetection(
                t_start=t_start,
                t_stop=t_stop,
                dB=db_mean,
                dur_s=t_dur,
                utc_start=t_utc_start,
                utc_stop=t_utc_stop
            ))

        return t_out_det, t_threshold

    def get_detections_adaptive(threshold_estimation_window_sec=threshold_estimation_window_sec,
                                threshold_freeze_before_detection_sec=threshold_freeze_before_detection_sec,
                                threshold_freeze_after_detection_sec=threshold_freeze_after_detection_sec,
                                fixed_threshold_duration_sec=threshold_fixed_init_duration_sec):
        detections = []
        freeze_until_idx = -1
        thresholds = []

        window_blocks = int(threshold_estimation_window_sec / block_duration_sec)
        freeze_blocks_before = int(threshold_freeze_before_detection_sec / block_duration_sec)
        freeze_blocks_after = int(threshold_freeze_after_detection_sec / block_duration_sec)
        fixed_threshold_blocks = int(fixed_threshold_duration_sec / block_duration_sec)

        # Globaler Threshold für die fixe Anfangszeit
        global_mean = np.mean(delta_power)
        global_std = np.std(delta_power)
        fixed_threshold = global_mean + threshold_std_factor * global_std

        threshold = fixed_threshold  # Anfangs mit globalem Threshold

        for i in range(num_blocks):
            if i < fixed_threshold_blocks:
                threshold = fixed_threshold
            elif i > freeze_until_idx:
                # Adaptive Threshold-Schätzung nur nach fixer Zeit
                window_start = max(0, i - window_blocks)
                window_end = i
                window_delta = delta_power[window_start:window_end]
                mean_val = np.mean(window_delta)
                std_val = np.std(window_delta)
                threshold = mean_val + threshold_std_factor * std_val

            thresholds.append(threshold)

            # Detektionslogik
            if delta_power[i] > threshold:
                if not detections or i > detections[-1]['stop'] + 1:
                    detections.append({'start': i, 'stop': i})
                else:
                    detections[-1]['stop'] = i

                freeze_until_idx = i + freeze_blocks_after
                freeze_start_idx = max(0, i - freeze_blocks_before)
                freeze_until_idx = max(freeze_until_idx, freeze_start_idx)

        # Umwandlung in OutputDetection-Objekte
        t_out_det = []
        for d in detections:
            start = d['start']
            stop = d['stop'] + 1

            db_meas_range = delta_power[start:stop]
            db_mean = np.mean(db_meas_range)
            t_start = start * block_duration_sec
            t_stop = stop * block_duration_sec
            t_dur = t_stop - t_start

            t_utc_start = None
            t_utc_stop = None
            if wav_start_date_time is not None:
                t_utc_start = wav_start_date_time + datetime.timedelta(seconds=t_start)
                t_utc_stop = wav_start_date_time + datetime.timedelta(seconds=t_stop)

            t_out_det.append(OutputDetection(
                t_start=t_start,
                t_stop=t_stop,
                dB=db_mean,
                dur_s=t_dur,
                utc_start=t_utc_start,
                utc_stop=t_utc_stop
            ))

        return t_out_det, thresholds

    if not flag_adaptive_threshold:
        t_out_det, t_threshold = get_detections()
    else:
        t_out_det, t_threshold = get_detections_adaptive()

    times = np.arange(num_blocks) * block_duration_sec

    if debug_plot_output:

        if not flag_adaptive_threshold:

            plt.figure(figsize=(10, 5))
            plt.plot(times, delta_power, label=f"Delta Power")

            # Threshold-Linie
            plt.axhline(y=t_threshold, color='red', linestyle='--', label='Threshold')
            for det in t_out_det:
                plt.axvspan(det.t_start, det.t_stop, color='orange', alpha=0.5)

            plt.xlabel("Zeit (s)")
            plt.ylabel("Leistung (dB)")
            plt.title("Delta (in dB) über Zeit")
            plt.legend()
            plt.grid()
            plt.tight_layout()
            plt.show()
            plt.close("all")

        else:

            plt.figure(figsize=(10, 5))
            plt.plot(times, delta_power, label="Delta Power")
            plt.plot(times, t_threshold, label="Adaptive Threshold", linestyle="--", color="red")
            for det in t_out_det:
                plt.axvspan(det.t_start, det.t_stop, color='orange', alpha=0.5)
            plt.xlabel("Zeit (s)")
            plt.ylabel("Leistung (dB)")
            plt.legend()
            plt.grid()
            plt.tight_layout()
            plt.show()
            plt.close("all")

    # Plotly-Figur erstellen
    if debug_plot_output_interactive:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=times,
            y=band_power,
            mode='lines',
            name=f"Signalband {freq_band[0]}-{freq_band[1]} Hz [dB]"
        ))
        fig.add_trace(go.Scatter(
            x=times,
            y=noise_power,
            mode='lines',
            name=f"Noiseband {noise_band[0]}-{noise_band[1]} Hz [dB]",
            line=dict(dash='dash')  # gestrichelte Linie
        ))
        fig.update_layout(
            title="Signal- und Noiseband-Leistung (in dB) über Zeit",
            xaxis_title="Zeit (s)",
            yaxis_title="Leistung (dB)",
            legend=dict(x=0.01, y=0.99),
            template="simple_white"
        )
        fig.show()

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=times,
            y=delta_power,
            mode='lines',
            name=f"Delta [dB]"
        ))
        fig.add_trace(go.Scatter(
            x=times,
            y=[t_threshold] * len(times),
            mode='lines',
            name='Threshold',
            line=dict(color='red', dash='dash')
        ))
        for det in t_out_det:
            fig.add_shape(
                type="rect",
                x0=det.t_start,
                x1=det.t_stop,
                y0=min(delta_power),
                y1=max(delta_power),
                fillcolor="orange",
                opacity=0.5,
                line_width=0,
            )
        fig.update_layout(
            title="Delta (in dB) über Zeit",
            xaxis_title="Zeit (s)",
            yaxis_title="Leistung (dB)",
            legend=dict(x=0.01, y=0.99),
            template="simple_white"
        )
        fig.show()

    for det in t_out_det:
        print(
            f"Detection from {det.t_start:.2f} to {det.t_stop:.2f} seconds, dB: {det.dB:.2f} dB, duration: {det.dur_s:.2f} seconds UTC_START: {det.utc_start}, UTC_STOP: {det.utc_stop}")

    if out_audacity_lbl_file is not None:
        content_file_audacity = ""
        for det in t_out_det:
            content_file_audacity += f"{det.t_start:.2f}\t{det.t_stop:.2f}\tM\n"
        with open(out_audacity_lbl_file, 'w') as f:
            f.write(content_file_audacity)
        del content_file_audacity
        print("Write Pre-Lbl File to:", out_audacity_lbl_file)
        print("Wrote Items", len(t_out_det), "to Audacity LBL file")

    if out_csv_file is not None:
        # Wrote detections to CSV file
        import csv
        with open(out_csv_file, 'w', newline='') as csvfile:
            fieldnames = ['t_start', 't_stop', 'dur_s', 'dB', 'utc_start', 'utc_stop']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for det in t_out_det:
                writer.writerow({
                    't_start': det.t_start,
                    't_stop': det.t_stop,
                    'dur_s': det.dur_s,
                    'dB': det.dB,
                    'utc_start': det.utc_start.isoformat() if det.utc_start else None,
                    'utc_stop': det.utc_stop.isoformat() if det.utc_stop else None
                })

        print("Wrote Items", len(t_out_det), "to CSV file:", out_csv_file)

    if debug_plot_output:
        # Hist over duration
        durations = [det.dur_s for det in t_out_det]
        plt.figure(figsize=(10, 5))
        plt.hist(durations, bins=30, color='blue', alpha=0.7)
        plt.xlabel("Duration (s)")
        plt.ylabel("Count")
        plt.title("Histogram of Detection Durations")
        plt.grid()
        plt.gca().xaxis.set_major_formatter(ticker.StrMethodFormatter("{x:.2f}"))
        plt.gca().yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:.2f}"))
        plt.tight_layout()
        plt.show()
        plt.close("all")

        # Hist over dB
        db_values = [det.dB for det in t_out_det]
        plt.figure(figsize=(10, 5))
        plt.hist(db_values, bins=30, color='green', alpha=0.7)
        plt.xlabel("dB")
        plt.ylabel("Count")
        plt.title("Histogram of Detection dB Values")
        plt.grid()
        plt.tight_layout()
        plt.show()
        plt.close("all")

    def show_time_map():
        import pandas as pd

        hours = [
            det.utc_start.replace(minute=0, second=0, microsecond=0)
            for det in t_out_det
        ]

        # 2. Zähle Detektionen pro Stunde
        count_per_hour = Counter(hours)

        # 3. DataFrame sortieren
        df = pd.DataFrame.from_dict(count_per_hour, orient='index', columns=['Detektionen'])
        df = df.sort_index()

        # 4. X-Achse als strings mit Datum + Uhrzeit
        x_labels = [dt.strftime('%Y-%m-%d %H:%M') for dt in df.index]

        # 5. Plot
        plt.figure(figsize=(12, 6))
        plt.bar(x_labels, df['Detektionen'], color='skyblue')

        plt.xlabel('UTC Zeit (Datum + Stunde)')
        plt.ylabel('Anzahl der Detektionen')
        plt.title('Detektionen pro Stunde')
        plt.xticks(rotation=45, ha='right')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.show()
        plt.close("all")

    if debug_plot_output:
        show_time_map()

    if not disable_show_and_write:

        for det in tqdm(t_out_det):
            # print(f"Detection from {det.t_start:.2f} to {det.t_stop:.2f} seconds")
            try:

                c_before = 3
                c_after = 3

                marker_duration_sec = det.t_stop - det.t_start

                wav_start_cut = det.t_start - c_before
                wav_stop_cut = det.t_stop + c_after

                if wav_start_cut < 0:
                    wav_start_cut = 0

                if wav_stop_cut > len(wav_data) / wav_sample_rate:
                    wav_stop_cut = len(wav_data) / wav_sample_rate

                cut_wav = wav_data[int(wav_start_cut * wav_sample_rate):int(wav_stop_cut * wav_sample_rate)]
                wav_duration_sec = len(cut_wav) / wav_sample_rate

                # Calc new markers
                wav_c_det_start_sec = det.t_start - wav_start_cut
                wav_c_det_stop_sec = det.t_stop - wav_start_cut

                # select n_fft based on the cut_wav duration
                plt_n_fft = 1024

                if wav_duration_sec > c_before + c_after + 2:  # marker time is 2 seconds
                    plt_n_fft = 1024 * 2

                # if wav_duration_sec > 0.5:
                #     plt_n_fft = 2048
                # if wav_duration_sec > 1.0:
                #     plt_n_fft = 4096
                # if wav_duration_sec > 2.0:
                #     plt_n_fft = 8192

                plt_title = f"Detection from {det.t_start:.2f}s to {det.t_stop:.2f}s\n" \
                            f"Wav duration: {wav_duration_sec:.2f}s, n_fft: {plt_n_fft}\n" \
                            f"Marker duration: {det.dur_s:.2f}s / " \
                            f"dB: {det.dB:.2f}"

                # internal_print_spec(
                #     wav_data=cut_wav,
                #     wav_sample_rate=wav_sample_rate,
                #     n_fft=plt_n_fft,
                #     freq_min=freq_band[0] - 50,
                #     freq_max=freq_band[1] + 50,
                #     markers=[
                #         Marker(color='red', t_min=wav_c_det_start_sec, t_max=wav_c_det_stop_sec),
                #     ],
                #     plt_title=plt_title,
                #     plt_filepath=f"{outfile_path}spec_{det.t_start:.2f}_{det.t_stop:.2f}.png" if outfile_path else None
                # )

                internal_print_spec_and_psd_mod(
                    wav_data=cut_wav,
                    wav_sample_rate=wav_sample_rate,
                    n_fft=plt_n_fft,
                    freq_min=freq_band[0] - 50,
                    freq_max=freq_band[1] + 50,
                    markers=[
                        Marker(color='red', t_min=wav_c_det_start_sec, t_max=wav_c_det_stop_sec),
                    ],
                    plt_title=plt_title,
                    plt_filepath=f"{outfile_path}spec_and_psd_{det.t_start:.2f}_{det.t_stop:.2f}.png" if outfile_path else None
                )

                # internal_print_spec_and_psd_mod(
                #     wav_data=cut_wav,
                #     wav_sample_rate=wav_sample_rate,
                #     n_fft=plt_n_fft,
                #     # freq_min=freq_band[0] - 50,
                #     # freq_max=freq_band[1] + 50,
                #     markers=[
                #         Marker(color='red', t_min=wav_c_det_start_sec, t_max=wav_c_det_stop_sec),
                #     ],
                #     plt_title=plt_title,
                #     plt_filepath=f"{outfile_path}spec_and_psd_{det.t_start:.2f}_{det.t_stop:.2f}_all.png" if outfile_path else None
                # )

            except Exception as e:
                print(f"Error processing detection: {e}")


if __name__ == "__main__":
    # TODO: Diese Implementierung ist mit fixen Threshold pro File!!! Das ist nicht optimal, denke an u-Kurve (mit unten Flag adaptive_threshold=True schon)
    # TODO: Es gibt im Ordner old/ eine Implementierung mit fortlaufendem Threshold (siehe Video https://youtu.be/pJzIpvsYMjg)

    # TODO: Schau dir mal die Ausgabe des Programmes an (vor allem diese ersten Zeilen, dann bekommst du ein Verständnis über die Berechnungen)

    # TODO: Setzte Base Pfade
    C_BASE_PATH_IN = "/Users/maximilianbundscherer/Desktop/meteor/MData/Export-Ari/"
    # C_BASE_PATH_IN = "/Users/maximilianbundscherer/Desktop/Export-Ari-TL/"
    C_BASE_PATH_OUT = "/Users/maximilianbundscherer/Desktop/"
    C_BASE_PATH_OUT_CSV = "/Users/maximilianbundscherer/Desktop/meteor/csv_expo/"

    assert os.path.exists(C_BASE_PATH_IN), f"Input base path does not exist: {C_BASE_PATH_IN}"
    assert os.path.exists(C_BASE_PATH_OUT), f"Output base path does not exist: {C_BASE_PATH_OUT}"


    def mb_files():
        # TODO: Hier wird das Signal in der NF vermutet (debug unten mit debug_plot_whole und debug_plot_config):
        nf_freq = 1000 + 3

        # TODO: Hier wird zum Abgleich das Rauschen vermutet (debug unten mit debug_plot_whole und debug_plot_config):
        noise_freq = 700

        # TODO: Hier wird die Bandbreite für Rauschen und Signal vermutet (debug unten mit debug_plot_whole und debug_plot_config):
        bandwidth = 10

        # TODO: Setzte Namen von Datei (Tag steckt im Dateinamen)
        # file_path = f"{C_BASE_PATH_IN}expoFull_gqrx_20250605_141152_49969000.wav"
        # file_path = f"{C_BASE_PATH_IN}expoFull_gqrx_20250606_103103_49969000.wav"
        # file_path = f"{C_BASE_PATH_IN}expoFull_gqrx_20250607_064539_49969000.wav"
        # file_path = f"{C_BASE_PATH_IN}expoFull_gqrx_20250608_083013_49969000.wav"
        # file_path = f"{C_BASE_PATH_IN}expoFull_gqrx_20250609_081703_49969000.wav"
        # file_path = f"{C_BASE_PATH_IN}expoFull_gqrx_20250610_064643_49969000.wav"
        # file_path = f"{C_BASE_PATH_IN}expoFull_gqrx_20250611_063415_49969000.wav"
        # file_path = f"{C_BASE_PATH_IN}expoFull_gqrx_20250612_062533_49969000.wav"
        # file_path = f"{C_BASE_PATH_IN}expoFull_gqrx_20250613_065218_49969000.wav"
        # file_path = f"{C_BASE_PATH_IN}expoFull_gqrx_20250614_193619_49969000.wav"
        # file_path = f"{C_BASE_PATH_IN}expoFull_gqrx_20250615_091116_49969000.wav"
        # file_path = f"{C_BASE_PATH_IN}expoFull_gqrx_20250616_063910_49969000.wav"
        # file_path = f"{C_BASE_PATH_IN}expoFull_gqrx_20250617_065021_49969000.wav"
        # file_path = f"{C_BASE_PATH_IN}expoFull_gqrx_20250618_080453_49969000.wav"
        # file_path = f"{C_BASE_PATH_IN}expoFull_gqrx_20250619_090813_49969000.wav"
        # file_path = f"{C_BASE_PATH_IN}expoFull_gqrx_20250620_065830_49969000.wav"
        # file_path = f"{C_BASE_PATH_IN}expoFull_gqrx_20250621_070912_49969000.wav"
        # file_path = f"{C_BASE_PATH_IN}expoFull_gqrx_20250622_180621_49969000.wav"
        # file_path = f"{C_BASE_PATH_IN}expoFull_gqrx_20250623_081257_49969000.wav"
        # file_path = f"{C_BASE_PATH_IN}expoFull_gqrx_20250624_073902_49969000.wav"
        file_path = f"{C_BASE_PATH_IN}expoFull_gqrx_20250625_075141_49969000.wav"

        # Get Time of the file_path
        file_path_date = file_path.split("/")[-1].split("_")
        assert len(file_path_date) == 5
        file_path_date = file_path_date[2] + "-" + file_path_date[3]
        file_path_date = datetime.datetime.strptime(file_path_date, "%Y%m%d-%H%M%S")
        print(f"File path date: {file_path_date}")

        proc_wav_file(
            file_path,
            # TODO: Evtl. ändern Blockgröße:
            block_duration_sec=0.2,
            freq_band=(nf_freq - bandwidth, nf_freq + bandwidth),
            noise_band=(noise_freq - bandwidth, noise_freq + bandwidth),
            # TODO: Evtl. ändern n_fft:
            n_fft=512,
            # wav_start_sec=int(60 * 60),
            # wav_end_sec=int(60 * 120),
            # TODO: Gibt zum Debuggen alles (Spec) aus (dauert lange, daher nur für Debug mit wav_start_sec und wav_end_sec):
            debug_plot_whole=False,
            # TODO: Gibt zum Debuggen alles aus (notwendig um zu überprüfen ob Signal zB. bei 1kHz liegt) (dauert lange, daher nur für Debug mit wav_start_sec und wav_end_sec):
            debug_plot_config=False,
            # TODO: Gibt statisch Ergebnisse aus:
            debug_plot_output=True,
            # TODO: Gibt interaktiv Ergebnisse aus:
            debug_plot_output_interactive=False,
            # TODO: Evtl. Threshold anpassen:
            threshold_std_factor=4,
            wav_start_date_time=file_path_date,
            # TODO: Setzte diesen Pfad, falls Ergebnisse als Bilder gespeichert werden sollen (falls nicht gesetzt, werden diese angezeigt, in Verwendung mit dem Parameter disable_show_and_write):
            # outfile_path=f"{C_BASE_PATH_OUT}spec_export/",
            # TODO: Deaktiviere Show und Write, damit die Bilder der Ergebnisse nicht angezeigt bzw. gespeichert werden (Verwendung mit Parameter outfile_path):
            disable_show_and_write=True,
            # TODO: Setze diesen Pfad um Pre-Label Export für Audacity zu machen
            # out_audacity_lbl_file=f"{C_BASE_PATH_OUT}prelbl-audacity.txt",
            # TODO: Setze diesen Pfad um CSV Export zu machen
            # out_csv_file=f"{C_BASE_PATH_OUT_CSV}out_25_06.csv",
            flag_adaptive_threshold=True,
            threshold_estimation_window_sec=120,
            threshold_freeze_before_detection_sec=3,
            threshold_freeze_after_detection_sec=20,
            threshold_fixed_init_duration_sec=10
        )


    mb_files()


    # Für später Dateien von Thomas Lauterbach

    def tl_files():
        nf_freq = 1000 + 6
        noise_freq = 950

        bandwidth = 10

        file_path = f"{C_BASE_PATH_IN}expoFull_Brams_250607_23MESZ.wav"
        # file_path = f"{C_BASE_PATH_IN}expoFull_Brams_250607_11MESZ.wav"

        # Get Time of the file_path
        file_path_date = file_path.split("/")[-1].split("_")
        assert len(file_path_date) == 4
        file_path_date = file_path_date[2] + "-" + file_path_date[3]
        file_path_date = file_path_date.replace("MESZ.wav", "")
        file_path_date = datetime.datetime.strptime(file_path_date, "%y%m%d-%H")
        # Convert from MESZ to UTC
        file_path_date = file_path_date - datetime.timedelta(hours=2)

        proc_wav_file(
            file_path,
            block_duration_sec=0.2,
            freq_band=(nf_freq - bandwidth, nf_freq + bandwidth),
            noise_band=(noise_freq - bandwidth, noise_freq + bandwidth),
            n_fft=512,
            # wav_start_sec=int(60 * 15),
            # wav_end_sec=int(60 * 30),
            debug_plot_whole=False,
            debug_plot_config=True,
            debug_plot_output=True,
            debug_plot_output_interactive=False,
            threshold_std_factor=3.5,
            wav_start_date_time=file_path_date,
            # outfile_path=f"{C_BASE_PATH_OUT}spec_export/",
            disable_show_and_write=True,
            flag_adaptive_threshold=True,
            threshold_estimation_window_sec=120,
            threshold_freeze_before_detection_sec=3,
            threshold_freeze_after_detection_sec=20,
            threshold_fixed_init_duration_sec=10
        )

    # tl_files()
