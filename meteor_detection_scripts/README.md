# Meteor Burst Detection and Classification Project

This project comprises two main Python scripts that work together to detect and classify meteor bursts from audio spectrograms.

Please see also [description](Dokumentation_Meteor_Detection.docx).

## Overview

1. **prime_detection.py**
   - Captures audio in 30-second segments using the TwitchRealtimeHandler.
   - Creates spectrograms with the `plot_spectrogram` function.
   - Processes the spectrograms to detect and classify meteor bursts.

2. **detector_and_classification.py**
   - Contains the `detect_and_cluster_bursts` function.
   - Uses ORB feature detection and DBSCAN clustering to identify meteor bursts.
   - Classifies bursts into:
     - **Critical bursts**: Bursts lasting at least 0.5 seconds.
     - **Non-critical bursts**: Bursts lasting less than 0.5 seconds.

## prime_detection.py

### Key Features

- **Audio Recording**: Captures live audio streams from a Twitch source.
- **Spectrogram Generation**: Converts audio data into spectrogram images for processing.
- **CSV Logging**: Logs results, including the count of critical and non-critical bursts, to a daily CSV file.

### Workflow

1. **Audio Capture**:
   - Records 30-second audio segments from a specified Twitch stream.
   - Saves the audio as a WAV file.

2. **Spectrogram Generation**:
   - Plots and saves a spectrogram image from the recorded audio.
   - Dynamically adjusts the noise threshold based on spectrogram analysis.

3. **Burst Detection**:
   - Calls `detect_and_cluster_bursts` from `detector_and_classification.py`.
   - Updates hourly and daily burst counts.

4. **Daily CSV Logging**:
   - Records timestamped results to a CSV file.
   - Creates a new CSV file each day.

## detector_and_classification.py

### Key Features

- **ORB Detection**:
  - Uses the ORB algorithm to detect keypoints in the spectrogram image.
- **DBSCAN Clustering**:
  - Groups keypoints into clusters.
  - Labels clusters as bursts.

- **Burst Classification**:
  - Measures the duration of each burst.
  - Classifies bursts based on a duration threshold of 0.5 seconds.

### Workflow

1. **Feature Detection**:
   - Reads a spectrogram image.
   - Detects keypoints using the ORB algorithm.

2. **Clustering**:
   - Applies DBSCAN clustering to group keypoints.
   - Visualizes clusters with bounding boxes (green for critical, red for non-critical).

3. **Classification**:
   - Classifies bursts based on their duration.
   - Returns lists of critical and non-critical bursts.

### Output

- Annotated spectrogram image with detected bursts.
- Lists of critical and non-critical bursts.

## Installation and Run

### Prerequisites

- Python 3.8+
- Required libraries: `numpy`, `opencv-python`, `matplotlib`, `scikit-learn`, `pyaudio`, `wave`, `twitchrealtimehandler`, `pandas`.

### Setup

1. Clone this repository. Set up a new virtual environment and activate it.
2. Install dependencies using:
   ```bash
   pip install -r requirements.txt
   ```

### Usage

Activate your new virtual environment.

1. **Run `prime_detection.py`**:
   ```bash
   python prime_detection.py
   ```
   - Follow prompts to select audio input devices.

2. **Adjust Detection Parameters**:
   - Modify `eps` and `min_samples` in `detect_and_cluster_bursts` for DBSCAN clustering as needed.

### Output

- Hourly and daily burst counts logged to CSV files.
- Annotated spectrogram images saved as `spectrogram2detected.jpg`.

## Future Work

- Optimize ORB and DBSCAN parameters for better burst detection.
- Integrate real-time burst visualization.
