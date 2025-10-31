import os

import numpy as np
import soundfile as sf
from matplotlib import pyplot as plt
from scipy.signal import welch
from tqdm import tqdm

from backend.aggregates import State, StateInitialization, StateDetection, StateTracking
from backend.aggregates import ConfigDetection, ConfigVisualization, ConfigSpecExport
from backend.aggregates import DetectedMeteor


def wav_file_process(
        wav_file_path: str,
        config_detection: ConfigDetection,
        config_visualization: ConfigVisualization,
        config_spec_export: ConfigSpecExport,
        wav_file_start_sec: float = 0,
        wav_file_stop_sec: float = -1
):
    assert os.path.exists(wav_file_path), f"File not found: {wav_file_path}"
    if config_spec_export.output_dir != "":
        assert os.path.exists(
            config_spec_export.output_dir), f"Output Directory not found: {config_spec_export.output_dir}"

    print()
    print("###############")
    print("Init Config")
    print("###############")

    impl_param_freq_ms_start: float = config_detection.signal_freq - (config_detection.channel_width / 2)
    impl_param_freq_ms_stop: float = config_detection.signal_freq + (config_detection.channel_width / 2)

    impl_param_freq_noise_1_start: float = (config_detection.signal_freq - config_detection.noise_channel_offset) - (
            config_detection.channel_width / 2)
    impl_param_freq_noise_1_stop: float = (config_detection.signal_freq - config_detection.noise_channel_offset) + (
            config_detection.channel_width / 2)

    impl_param_freq_noise_2_start: float = (config_detection.signal_freq + config_detection.noise_channel_offset) - (
            config_detection.channel_width / 2)

    impl_param_freq_noise_2_stop: float = (config_detection.signal_freq + config_detection.noise_channel_offset) + (
            config_detection.channel_width / 2)

    print("Freq MS Min: ", impl_param_freq_ms_start)
    print("Freq MS Max: ", impl_param_freq_ms_stop)

    print("Freq Noise 1 Min: ", impl_param_freq_noise_1_start)
    print("Freq Noise 1 Max: ", impl_param_freq_noise_1_stop)

    print("Freq Noise 2 Min: ", impl_param_freq_noise_2_start)
    print("Freq Noise 2 Max: ", impl_param_freq_noise_2_stop)

    impl_param_wf_win_size: int = int(config_visualization.max_range_sec / config_detection.proc_block_sec)
    impl_param_avg_win_size: int = int(config_detection.avg_win_sec / config_detection.proc_block_sec)

    print("Waterfall Win Size: ", impl_param_wf_win_size)
    print("Avg Win Size: ", impl_param_avg_win_size)

    print()
    print("###############")
    print("Prepare Wav")
    print("###############")
    _, file_sample_rate = sf.read(wav_file_path)
    assert file_sample_rate == 4000, f"Invalid Sample Rate: {file_sample_rate}"
    if wav_file_stop_sec != -1:
        file_data, file_sample_rate = sf.read(wav_file_path, start=wav_file_start_sec * file_sample_rate,
                                              stop=wav_file_stop_sec * file_sample_rate)
    else:
        file_data, file_sample_rate = sf.read(wav_file_path, start=wav_file_start_sec * file_sample_rate)
    if len(file_data.shape) > 1:
        print("WARNING: Multichannel file detected. Using first channel only.")
        file_data = file_data[:, 0]
    file_block_size: int = int(config_detection.proc_block_sec * file_sample_rate)
    file_duration_sec: float = len(file_data) / file_sample_rate

    print("File Samplerate: ", file_sample_rate)
    print("File Blockgröße: ", file_block_size)
    print("File Dauer: ", file_duration_sec)

    print()
    print("###############")
    print("Prepare Plots")
    print("###############")
    # Init Figure
    if config_visualization.enable_ui_plots:
        plt.ion()
        glob_fig, ((glob_ax_psd, glob_ax_waterfall),
                   (glob_ax_db, glob_ax_waterfall_2),
                   (glob_ax_db_2, _)) = plt.subplots(
            3, 2,
            figsize=(20, 9))
        glob_fig.suptitle('Meteor Detection Live')

    # Init PSD
    if config_visualization.enable_ui_plots:
        tmp_frequencies, tmp_psd = welch(file_data[:file_block_size], file_sample_rate, nfft=config_detection.n_fft)
        tmp_psd_db = 10 * np.log10(tmp_psd)
        glob_line_psd, = glob_ax_psd.plot(tmp_frequencies, tmp_psd_db)
        glob_ax_psd.set_xlabel('Frequency [Hz]')
        glob_ax_psd.set_ylabel('PSD [dB]')
        glob_ax_psd.set_title('Live PSD Plot')
        del tmp_frequencies, tmp_psd, tmp_psd_db

        for freq_min, freq_max, color in [
            (impl_param_freq_ms_start, impl_param_freq_ms_stop, 'r'),
            (impl_param_freq_noise_1_start, impl_param_freq_noise_1_stop, 'grey'),
            (impl_param_freq_noise_2_start, impl_param_freq_noise_2_stop, 'brown'),
        ]:
            glob_ax_psd.axvline(freq_min, color=color, linestyle='--', label=f'{freq_min} Hz')
            glob_ax_psd.axvline(freq_max, color=color, linestyle='--', label=f'{freq_max} Hz')
        del freq_min, freq_max, color

    # Init db Plot (first)
    if config_visualization.enable_ui_plots:
        glob_lines_db_ms, = glob_ax_db.plot([], [], label=f'MS (dB)', color='r')
        glob_lines_db_noise_1, = glob_ax_db.plot([], [], label=f'Noise 1 (dB)', color='grey')
        glob_lines_db_noise_2, = glob_ax_db.plot([], [], label=f'Noise 2 (dB)', color='brown')
        glob_ax_db.set_xlabel('Time [s]')
        glob_ax_db.set_ylabel('Lautstärke [dB]')
        glob_ax_db.set_title(
            f'Lautstärke in Frequenzbereichen der letzten {config_visualization.max_range_sec} Sekunden')
        glob_ax_db.legend()

    # Init db Plot (second)
    if config_visualization.enable_ui_plots:
        glob_lines_db_2_ms, = glob_ax_db_2.plot([], [], label=f'MS (dB)', color='b')
        glob_lines_db_2_mean, = glob_ax_db_2.plot([], [], label=f'Mean (dB)', color='grey')
        glob_lines_db_2_std, = glob_ax_db_2.plot([], [], label=f'Std (dB)', color='brown')
        glob_lines_db_2_threshold, = glob_ax_db_2.plot([], [], label=f'Threshold (dB)', color='r')
        glob_ax_db_2.set_xlabel('Time [s]')
        glob_ax_db_2.set_ylabel('Lautstärke [dB]')
        glob_ax_db_2.set_title(
            f'Lautstärke in Frequenzbereichen 2 der letzten {config_visualization.max_range_sec} Sekunden')
        glob_ax_db_2.legend()

    # Plot Konfig
    if config_visualization.enable_ui_plots:
        plt.tight_layout()
        plt.show()

    print()
    print("###############")
    print("Process Loop")
    print("###############")

    # All
    local_data_times_block_end = []

    local_data_abs_meas_sig = []
    local_data_abs_meas_noise_1 = []
    local_data_abs_meas_noise_2 = []

    local_data_over_noise_sig = []
    local_data_over_noise_sig_mean = []
    local_data_over_noise_sig_std = []
    local_data_over_noise_sig_threshold = []

    # Only Waterfall
    local_wf_db_times = []
    local_wf_db_data = []

    # State
    local_my_state: State = StateInitialization(
        history_channel_dB=[]
    )

    # Auto Gain for Waterfall and Spectrogram
    local_param_psd_db_mean_from_init = None

    # Detections
    local_out_res_detections: [DetectedMeteor] = []
    local_out_res_non_exported_detections: [DetectedMeteor] = []

    for block_start_idx in tqdm(range(0, len(file_data) - file_block_size + 1, file_block_size)):
        # ----------------------------------------
        # Extract
        # ----------------------------------------
        block_data = file_data[block_start_idx:block_start_idx + file_block_size]
        block_start_elapsed_sec: float = block_start_idx / file_sample_rate
        block_end_elapsed_sec: float = (block_start_idx + file_block_size) / file_sample_rate

        # ----------------------------------------
        # Meta Log
        # ----------------------------------------
        if config_visualization.enable_debug_logs:
            print()
            print(
                "- Block //",
                "Elapsed Start:", block_start_elapsed_sec,
                "Elapsed End:", block_end_elapsed_sec,
                "from:", file_duration_sec
            )

        del block_start_idx

        if config_visualization.enable_ui_plots:
            glob_fig.suptitle(f'Meteor Detection Live {block_end_elapsed_sec:.2f}/{file_duration_sec:.2f}')

        local_data_times_block_end.append(block_end_elapsed_sec)

        # ----------------------------------------
        # Update PSD
        # ----------------------------------------
        block_frequencies, block_psd = welch(block_data, file_sample_rate, nfft=config_detection.n_fft)
        block_psd_db = 10 * np.log10(block_psd)
        if config_visualization.enable_ui_plots:
            glob_line_psd.set_ydata(block_psd_db)
            glob_ax_psd.relim()
            glob_ax_psd.autoscale_view()

            if local_param_psd_db_mean_from_init is not None:
                glob_ax_psd.axhline(local_param_psd_db_mean_from_init - config_visualization.wf_offset_vmin,
                                    color='grey', linestyle='--')
                glob_ax_psd.axhline(local_param_psd_db_mean_from_init + config_visualization.wf_offset_vmax,
                                    color='grey', linestyle='--')

        # ----------------------------------------
        # Update Waterfall
        # ----------------------------------------
        # Add new Data
        local_wf_db_data.append(block_psd_db)
        local_wf_db_times.append(block_end_elapsed_sec)

        # Clear old Data
        if len(local_wf_db_times) > impl_param_wf_win_size:
            local_wf_db_data.pop(0)
            local_wf_db_times.pop(0)

        wf_times_start = local_wf_db_times[0]
        wf_times_stop = local_wf_db_times[-1]

        # Show WF 1
        if config_visualization.enable_ui_plots:
            glob_ax_waterfall.clear()
            tmp_vmin = None
            tmp_vmax = None
            if local_param_psd_db_mean_from_init is not None:
                tmp_vmin = local_param_psd_db_mean_from_init - config_visualization.wf_offset_vmin
                tmp_vmax = local_param_psd_db_mean_from_init + config_visualization.wf_offset_vmax
            glob_ax_waterfall.imshow(np.array(local_wf_db_data).T, aspect='auto', cmap='viridis', origin='lower',
                                     extent=[local_wf_db_times[0], local_wf_db_times[-1], block_frequencies[0],
                                             block_frequencies[-1]],
                                     vmin=tmp_vmin,
                                     vmax=tmp_vmax
                                     )
            del tmp_vmin, tmp_vmax
            glob_ax_waterfall.set_xlabel('Time [s]')
            glob_ax_waterfall.set_ylabel('Frequency [Hz]')
            glob_ax_waterfall.set_title(
                f'Wasserfall-Diagramm der letzten {config_visualization.max_range_sec} Sekunden'
            )
            for freq_min, freq_max, color in [
                (impl_param_freq_ms_start, impl_param_freq_ms_stop, 'r'),
                (impl_param_freq_noise_1_start, impl_param_freq_noise_1_stop, 'grey'),
                (impl_param_freq_noise_2_start, impl_param_freq_noise_2_stop, 'brown'),
            ]:
                glob_ax_waterfall.axhline(freq_min, color=color, linestyle='--')
                glob_ax_waterfall.axhline(freq_max, color=color, linestyle='--')
            del freq_min, freq_max, color

        # Show WF 2
        if config_visualization.enable_ui_plots:
            glob_ax_waterfall_2.clear()
            tmp_vmin = None
            tmp_vmax = None
            if local_param_psd_db_mean_from_init is not None:
                tmp_vmin = local_param_psd_db_mean_from_init - config_visualization.wf_offset_vmin
                tmp_vmax = local_param_psd_db_mean_from_init + config_visualization.wf_offset_vmax
            glob_ax_waterfall_2.imshow(np.array(local_wf_db_data).T, aspect='auto', cmap='viridis', origin='lower',
                                       extent=[local_wf_db_times[0], local_wf_db_times[-1], block_frequencies[0],
                                               block_frequencies[-1]],
                                       vmin=tmp_vmin,
                                       vmax=tmp_vmax
                                       )
            del tmp_vmin, tmp_vmax
            glob_ax_waterfall_2.set_xlabel('Time [s]')
            glob_ax_waterfall_2.set_ylabel('Frequency [Hz]')
            glob_ax_waterfall_2.set_title(
                f'Wasserfall-Diagramm 2 der letzten {config_visualization.max_range_sec} Sekunden'
            )
            glob_ax_waterfall_2.set_ylim(
                config_detection.signal_freq - config_visualization.limit_freq_offset_wf2_and_export,
                config_detection.signal_freq + config_visualization.limit_freq_offset_wf2_and_export
            )
            for freq_min, freq_max, color in [
                (impl_param_freq_ms_start, impl_param_freq_ms_stop, 'r'),
            ]:
                glob_ax_waterfall_2.axhline(freq_min, color=color, linestyle='--')
                glob_ax_waterfall_2.axhline(freq_max, color=color, linestyle='--')
            del freq_min, freq_max, color

        # Export Spec
        if config_spec_export.output_dir != "":
            copy_results_detected_meteors_not_exported = local_out_res_non_exported_detections.copy()
            for t in local_out_res_non_exported_detections:
                t: DetectedMeteor = t
                t_real_start = t.time_start
                t_real_stop = t.time_stop
                t_simulated_start = t_real_start - config_spec_export.time_before_meteor_sec
                t_simulated_stop = t_real_stop + config_spec_export.time_after_meteor_sec

                if wf_times_start <= t_simulated_start <= wf_times_stop and wf_times_start <= t_simulated_stop <= wf_times_stop:
                    plt.figure(figsize=(10, 5))  # TODO
                    # plt.figure()
                    tmp_vmin = None
                    tmp_vmax = None
                    if local_param_psd_db_mean_from_init is not None:
                        tmp_vmin = local_param_psd_db_mean_from_init - config_visualization.wf_offset_vmin
                        tmp_vmax = local_param_psd_db_mean_from_init + config_visualization.wf_offset_vmax
                    plt.imshow(np.array(local_wf_db_data).T, aspect='auto', cmap='viridis', origin='lower',
                               extent=[local_wf_db_times[0], local_wf_db_times[-1], block_frequencies[0],
                                       block_frequencies[-1]],
                               vmin=tmp_vmin, vmax=tmp_vmax)
                    del tmp_vmin, tmp_vmax
                    plt.xlim(t_simulated_start, t_simulated_stop)
                    plt.ylim(
                        config_detection.signal_freq - config_visualization.limit_freq_offset_wf2_and_export,
                        config_detection.signal_freq + config_visualization.limit_freq_offset_wf2_and_export
                    )
                    plt.xlabel('Time [s]')
                    plt.ylabel('Frequency [Hz]')
                    plt.title(
                        f'Detection {t_real_start:.2f}-{t_real_stop:.2f}sec (d={t.duration:.2f}sec)\n' + f'Min={t.db_min:.2f}dB, Max={t.db_max:.2f}dB, Mean={t.db_mean:.2f}dB, Std={t.db_std:.2f}dB'
                    )
                    # Add marker
                    plt.axvline(t_real_start, color='grey', linestyle='--')
                    plt.axvline(t_real_stop, color='grey', linestyle='--')
                    plt.axhline(impl_param_freq_ms_start, color='grey', linestyle='--')
                    plt.axhline(impl_param_freq_ms_stop, color='grey', linestyle='--')
                    plt_filepath = config_spec_export.output_dir + f"spec_{t_real_start:.2f}_{t_real_stop:.2f}.jpg"
                    plt.savefig(plt_filepath,
                                bbox_inches='tight',
                                pad_inches=0)
                    if config_visualization.enable_debug_logs:
                        print(f"Saved Meteor to {plt_filepath}")
                    del plt_filepath
                    plt.close()
                    copy_results_detected_meteors_not_exported.remove(t)

            local_out_res_non_exported_detections = copy_results_detected_meteors_not_exported
            del copy_results_detected_meteors_not_exported

        # ----------------------------------------
        # Update db Plot
        # ----------------------------------------
        # Calc 1
        tmp_freq_mask = (block_frequencies >= impl_param_freq_ms_start) & (block_frequencies <= impl_param_freq_ms_stop)
        tmp_power_in_band = np.sum(block_psd[tmp_freq_mask])
        block_db_ms = 10 * np.log10(tmp_power_in_band) if tmp_power_in_band > 0 else -np.inf
        local_data_abs_meas_sig.append(block_db_ms)
        del tmp_freq_mask, tmp_power_in_band

        tmp_freq_mask = (block_frequencies >= impl_param_freq_noise_1_start) & (
                block_frequencies <= impl_param_freq_noise_1_stop)
        tmp_power_in_band = np.sum(block_psd[tmp_freq_mask])
        block_db_noise_1 = 10 * np.log10(tmp_power_in_band) if tmp_power_in_band > 0 else -np.inf
        local_data_abs_meas_noise_1.append(block_db_noise_1)
        del tmp_freq_mask, tmp_power_in_band

        tmp_freq_mask = (block_frequencies >= impl_param_freq_noise_2_start) & (
                block_frequencies <= impl_param_freq_noise_2_stop)
        tmp_power_in_band = np.sum(block_psd[tmp_freq_mask])
        block_db_noise_2 = 10 * np.log10(tmp_power_in_band) if tmp_power_in_band > 0 else -np.inf
        local_data_abs_meas_noise_2.append(block_db_noise_2)
        del tmp_freq_mask, tmp_power_in_band

        if config_visualization.enable_debug_logs:
            print("DB MS:", round(block_db_ms, 2),
                  "DB Noise 1:", round(block_db_noise_1, 2),
                  "DB Noise 2:", round(block_db_noise_2, 2))

        # Show 1
        if config_visualization.enable_ui_plots:
            glob_lines_db_ms.set_data(np.arange(len(local_data_abs_meas_sig)) * config_detection.proc_block_sec,
                                      local_data_abs_meas_sig)
            glob_lines_db_noise_1.set_data(
                np.arange(len(local_data_abs_meas_noise_1)) * config_detection.proc_block_sec,
                local_data_abs_meas_noise_1)
            glob_lines_db_noise_2.set_data(
                np.arange(len(local_data_abs_meas_noise_2)) * config_detection.proc_block_sec,
                local_data_abs_meas_noise_2)
            glob_ax_db.set_xlim(
                max(0,
                    len(local_data_abs_meas_sig) * config_detection.proc_block_sec - config_visualization.max_range_sec),
                len(local_data_abs_meas_sig) * config_detection.proc_block_sec
            )
            glob_ax_db.relim()
            glob_ax_db.autoscale_view()

        # Calc 2
        block_db_2_ms = block_db_ms - np.mean([block_db_noise_1, block_db_noise_2])
        history_db_mb_meas_ms = local_data_over_noise_sig[-impl_param_avg_win_size:]
        local_data_over_noise_sig.append(block_db_2_ms)
        if config_visualization.enable_debug_logs:
            print("DB_2 MS :", round(block_db_2_ms, 2))

        history_mean = np.mean(history_db_mb_meas_ms)
        history_std = np.std(history_db_mb_meas_ms)
        local_data_over_noise_sig_mean.append(history_mean)
        local_data_over_noise_sig_std.append(history_std)

        block_db_2_threshold = history_mean + config_detection.threshold_std_factor * history_std

        if isinstance(local_my_state, StateTracking):
            local_my_state: StateTracking = local_my_state
            block_db_2_threshold = local_my_state.locked_threshold
        elif isinstance(local_my_state, StateDetection):
            local_my_state: StateDetection = local_my_state
            if local_my_state.use_locked_threshold_until_secs > block_end_elapsed_sec:
                block_db_2_threshold = local_my_state.locked_threshold

        local_data_over_noise_sig_threshold.append(block_db_2_threshold)
        if config_visualization.enable_debug_logs:
            print("DB_2 Threshold:", round(block_db_2_threshold, 2))

        del history_db_mb_meas_ms

        # Show 2
        if config_visualization.enable_ui_plots:
            glob_lines_db_2_ms.set_data(np.arange(len(local_data_over_noise_sig)) * config_detection.proc_block_sec,
                                        local_data_over_noise_sig)
            glob_lines_db_2_mean.set_data(
                np.arange(len(local_data_over_noise_sig_mean)) * config_detection.proc_block_sec,
                local_data_over_noise_sig_mean)
            glob_lines_db_2_std.set_data(
                np.arange(len(local_data_over_noise_sig_std)) * config_detection.proc_block_sec,
                local_data_over_noise_sig_std)
            glob_lines_db_2_threshold.set_data(
                np.arange(len(local_data_over_noise_sig_threshold)) * config_detection.proc_block_sec,
                local_data_over_noise_sig_threshold)
            glob_ax_db_2.set_xlim(
                max(0,
                    len(local_data_over_noise_sig) * config_detection.proc_block_sec - config_visualization.max_range_sec),
                len(local_data_over_noise_sig) * config_detection.proc_block_sec
            )
            glob_ax_db_2.relim()
            glob_ax_db_2.autoscale_view()

        # ----------------------------------------
        # State
        # ----------------------------------------
        if isinstance(local_my_state, StateInitialization):
            local_my_state: StateInitialization = local_my_state
            if config_visualization.enable_debug_logs:
                print("State: Initialization")
            block_current_psd_db_mean = np.mean(block_psd_db)
            if config_visualization.enable_debug_logs:
                print("Current PSD Mean:", block_current_psd_db_mean)
            local_my_state.history_channel_dB.append(block_current_psd_db_mean)
            del block_current_psd_db_mean
            if block_start_elapsed_sec >= config_detection.init_detection_wait_sec:
                local_param_psd_db_mean_from_init = np.mean(local_my_state.history_channel_dB)
                local_my_state = StateDetection()
                if config_visualization.enable_debug_logs:
                    print("-> Switch to State: Detection")

        elif isinstance(local_my_state, StateDetection):
            local_my_state: StateDetection = local_my_state
            if block_db_2_ms > block_db_2_threshold:
                local_my_state = StateTracking(
                    # TODO Evtl puffer nach startk der dektion um ende sicher zu finden
                    locked_threshold=block_db_2_threshold + 0 * history_std,
                    time_start_detection=block_start_elapsed_sec,
                    history_over_noise_sig_dB=[]
                )
                if config_visualization.enable_debug_logs:
                    print("-> Switch to State: Tracking")
            if config_visualization.enable_debug_logs:
                print("State: Detection")

        elif isinstance(local_my_state, StateTracking):
            local_my_state: StateTracking = local_my_state
            local_my_state.history_over_noise_sig_dB.append(block_db_2_ms)
            if block_db_2_ms < block_db_2_threshold:
                tmp_dur = block_start_elapsed_sec - local_my_state.time_start_detection
                tmp_mean = np.mean(local_my_state.history_over_noise_sig_dB)
                if tmp_mean >= config_detection.detection_db_over_noise_mean_min and (
                        tmp_dur) >= config_detection.detection_dur_min_sec:
                    dm = DetectedMeteor(
                        time_start=local_my_state.time_start_detection,
                        time_stop=block_start_elapsed_sec,
                        duration=tmp_dur,
                        db_min=min(local_my_state.history_over_noise_sig_dB),
                        db_max=max(local_my_state.history_over_noise_sig_dB),
                        db_mean=np.mean(local_my_state.history_over_noise_sig_dB),
                        db_std=np.std(local_my_state.history_over_noise_sig_dB)
                    )
                    local_out_res_detections.append(dm)
                    local_out_res_non_exported_detections.append(dm)
                    print("Detected Meteor:", dm, "Now Detected Meteors:",
                          len(local_out_res_detections))
                    del dm
                else:
                    if config_visualization.enable_debug_logs:
                        print(
                            "Detected Meteor but not exported (db_min < config_detection.detection_db_over_noise_max_min)")
                del tmp_dur, tmp_mean
                local_my_state = StateDetection(
                    locked_threshold=local_my_state.locked_threshold,
                    use_locked_threshold_until_secs=block_start_elapsed_sec + config_detection.after_tracking_wait_sec
                )
                if config_visualization.enable_debug_logs:
                    print("-> Switch to State: Detection")
            if config_visualization.enable_debug_logs:
                print("State: Tracking")

        else:
            raise Exception("Unknown State", local_my_state)

        # Plot Detection Marks
        if config_visualization.enable_ui_plots:
            for t in local_out_res_detections:
                glob_ax_db.axvline(t.time_start, color='r', linestyle='--')
                glob_ax_db_2.axvline(t.time_start, color='r', linestyle='--')
            for t in local_out_res_detections:
                glob_ax_db.axvline(t.time_stop, color='g', linestyle='--')
                glob_ax_db_2.axvline(t.time_stop, color='g', linestyle='--')
            for t in local_out_res_detections:
                if wf_times_start <= t.time_start <= wf_times_stop:
                    glob_ax_waterfall.axvline(t.time_start, color='r', linestyle='--')
                    glob_ax_waterfall_2.axvline(t.time_start, color='r', linestyle='--')
            for t in local_out_res_detections:
                if wf_times_start <= t.time_stop <= wf_times_stop:
                    glob_ax_waterfall.axvline(t.time_stop, color='g', linestyle='--')
                    glob_ax_waterfall_2.axvline(t.time_stop, color='g', linestyle='--')

        # ----------------------------------------
        # Delay Animation
        # ----------------------------------------
        if config_visualization.enable_ui_plots:
            if config_visualization.flag_realtime_animation:
                plt.pause(config_detection.proc_block_sec / config_visualization.realtime_factor)

    if config_visualization.enable_ui_plots:
        plt.ioff()
        plt.show()

    if len(local_out_res_non_exported_detections) != 0:
        print("Detected Meteors not exported: ", len(local_out_res_non_exported_detections))
        for t in local_out_res_non_exported_detections:
            print(t)
