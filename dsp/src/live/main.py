from backend import processor
from backend.aggregates import ConfigDetection, ConfigVisualization, ConfigSpecExport

if __name__ == '__main__':
    # processor.wav_file_process(
    #     wav_file_path="/Users/maximilianbundscherer/Downloads/meteor/data/TestData/short_resampled.wav",
    #     config_detection=ConfigDetection(
    #         proc_block_sec=0.5,
    #         n_fft=4096,
    #         signal_freq=1020,
    #     ),
    #     config_visualization=ConfigVisualization(
    #         enable_ui_plots=True,
    #         wf_offset_vmin=0,
    #         wf_offset_vmax=25,
    #     ),
    #     config_spec_export=ConfigSpecExport(
    #         output_dir=""
    #     )
    # )

    processor.wav_file_process(
        wav_file_path="/Users/maximilianbundscherer/Downloads/meteor/data/TestData/gqrx_20241213_171350_49969000_sampled.wav",
        # wav_file_start_sec=90,

        config_detection=ConfigDetection(
            proc_block_sec=0.20,
            n_fft=4096,
            detection_db_over_noise_mean_min=1,
            detection_dur_min_sec=0.5,
            signal_freq=1020,
        ),
        config_visualization=ConfigVisualization(
            enable_ui_plots=False,
            wf_offset_vmin=0,
            wf_offset_vmax=25,
            max_range_sec=60,
        ),
        config_spec_export=ConfigSpecExport(
            output_dir="spec_export/test_my_file/"
        )
    )

    processor.wav_file_process(
        wav_file_path="/Users/maximilianbundscherer/Downloads/meteor/data/TestData/HDSDR_20241231_000142Z_49969kHz_AF_resampled.wav",
        # wav_file_start_sec=115,
        # wav_file_start_sec=225,  # best
        # wav_file_start_sec=280,
        # wav_file_start_sec=310,

        config_detection=ConfigDetection(
            proc_block_sec=0.20,
            n_fft=4096,
            detection_db_over_noise_mean_min=1,
            detection_dur_min_sec=0.5,
            signal_freq=1025,
        ),
        config_visualization=ConfigVisualization(
            enable_ui_plots=False,
            wf_offset_vmin=-10,
            wf_offset_vmax=35,
            max_range_sec=60,
        ),
        config_spec_export=ConfigSpecExport(
            output_dir="spec_export/test_sonneberg/"
        )
    )
