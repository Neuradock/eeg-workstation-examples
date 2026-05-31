import numpy as np
from scipy.fft import rfft, rfftfreq
from scipy.signal import welch

import numpy as np
from scipy.signal import welch
import os
import numpy as np
from numpy.fft import rfft, rfftfreq

def data_reader(file_path:str):
    """Use this tool to read and decode data, returning raw data and marker information.
       Usage: data, data_marker = data_reader("1111.txt")
       data is a 2D np.array (rows=channels, cols=data_length);
       marker is a list where each entry contains the raw signal line number and event label,
       e.g., [[1008, 'trial0\n'], [1260, 'trial1-target\n']].
       Args:
           file_path: data file path.
       Returns:
           raw data, marker information
    """
    data1 = []
    data1_marker = []
    with open (file_path) as f:
        d = f.readlines()
        header_line = d[0]

        if not header_line.startswith('HEADER_DEF,'):
            raise ValueError("File header format is incorrect; must start with 'HEADER_DEF,'.")
        header_parts = header_line.strip().split(',')[1:]
        channel_indices = [i for i, part in enumerate(header_parts) if part == 'C']
        package_size = len(channel_indices)//7


        for i in range(1,len(d)):
            try:
                data_line_split = d[i].strip().split(',')
                data_line = [[float(data_line_split[x]) for x in channel_indices[j*7:j*7+7]] for j in range(package_size)]
                data1 = data1+data_line

            except:
                data1_marker.append([len(data1), d[i]])
    
    data1 = np.array(data1).transpose(1,0)

    return data1,data1_marker



def EEG_quality_check(data_path, segment_len_sec, fs, powerline_freq=50):
    """
    EEG Data Quality Scoring System (Expert Version)
    
    Detected artifacts:
    1. Electrode detachment (Flatline)
    2. EMG interference
    3. Signal saturation
    4. Baseline wander
    5. Power-line noise

    Parameters:
    data_path (str): Path to the EEG data file.
    segment_len_sec (int): Length of each data segment (seconds).
    fs (int): Sampling rate of the data (Hz).
    powerline_freq (int): Power-line noise frequency (usually 50 or 60 Hz).

    Returns:
    tuple: (quality_scores, quality_flags, is_usable_matrix, data)
        - quality_scores (np.array): Score matrix with shape (segments, channels), range 0-100.
        - quality_flags (np.array): Artifact flag matrix with shape (segments, channels, 5).
        - is_usable_matrix (np.array): Boolean matrix with shape (segments, channels), True means usable.
        - data (np.array): Raw EEG data read from the file.
    """
    # 1. Load data
    data, _ = data_reader(data_path)
    
    # 2. Define parameters
    n_channels, n_samples = data.shape
    segment_len_samples = int(segment_len_sec * fs)
    segment_num = n_samples // segment_len_samples
    
    # 3. Initialize result arrays (use dict for readability)
    ARTIFACT_INDICES = {
        'detachment': 0, 
        'emg': 1, 
        'saturation': 2, 
        'baseline_drift': 3, 
        'powerline': 4
    }
    n_artifact_types = len(ARTIFACT_INDICES)
    quality_flags = np.zeros((segment_num, n_channels, n_artifact_types), dtype=int)
    quality_scores = np.full((segment_num, n_channels), 100.0) # full score 100

    # 4. Define artifact detection thresholds (adjustable)
    # Saturation / flatline
    SATURATION_THRESHOLD = 300      # uV, peak-to-peak threshold for signal saturation
    DETACHMENT_STD_THRESHOLD = 2.0  # uV, std threshold for flatline
    # Frequency-domain thresholds
    SIGNAL_FREQ_LOW = 2             # Hz, main signal band
    SIGNAL_FREQ_HIGH = 50           # Hz
    EMG_FREQ_LOW = 30               # Hz, EMG band
    EMG_FREQ_HIGH = 70            # Hz
    BASELINE_FREQ_HIGH = 1.0        # Hz, baseline wander band
    
    # Power-ratio thresholds
    EMG_POWER_RATIO_THRESHOLD = 3     # Ratio of EMG power to signal power
    BASELINE_POWER_RATIO_THRESHOLD = 5.0 # Ratio of baseline power to signal power
    POWERLINE_PEAK_RATIO_THRESHOLD = 5.0 # Ratio of powerline peak to surrounding average power

    # 5. Define scoring system parameters
    SCORE_UNUSABLE_THRESHOLD = 40  # Segments below this score are considered completely unusable
    PENALTIES = {
        'emg': 30,
        'baseline_drift': 25,
        'powerline': 20
    }

    # 6. Iterate over all segments and channels
    for i in range(segment_num):
        for j in range(n_channels):
            start_idx = i * segment_len_samples
            end_idx = start_idx + segment_len_samples
            segment = data[j, start_idx:end_idx]
            
            if len(segment) < segment_len_samples:
                continue

            # --- Artifact detection ---
            is_flat = np.std(segment) < DETACHMENT_STD_THRESHOLD
            is_saturated = max(segment) - min(segment) > SATURATION_THRESHOLD

            # a) Electrode detachment (fatal)
            if is_flat:
                quality_flags[i, j, ARTIFACT_INDICES['detachment']] = 1
            
            # b) Signal saturation (fatal)
            if is_saturated:
                quality_flags[i, j, ARTIFACT_INDICES['saturation']] = 1
            
            # If fatal artifact, score 0 and skip subsequent frequency analysis
            if is_flat or is_saturated:
                quality_scores[i, j] = 0
                continue
            
            # --- Frequency analysis (Welch method is more stable) ---
            freqs, psd = welch(segment, fs=fs, nperseg=segment_len_samples, scaling='density')
            
            # Calculate total power per band
            def get_band_power(f_low, f_high):
                band_indices = np.where((freqs >= f_low) & (freqs < f_high))[0]
                return np.sum(psd[band_indices]) if len(band_indices) > 0 else 1e-10

            signal_power = get_band_power(SIGNAL_FREQ_LOW, SIGNAL_FREQ_HIGH)

            # c) Baseline wander detection
            baseline_power = get_band_power(0, BASELINE_FREQ_HIGH)
            baseline_ratio = baseline_power / signal_power
            if baseline_ratio > BASELINE_POWER_RATIO_THRESHOLD:
                quality_flags[i, j, ARTIFACT_INDICES['baseline_drift']] = 1

            # d) EMG interference detection
            emg_power = get_band_power(EMG_FREQ_LOW, EMG_FREQ_HIGH)
            emg_ratio = emg_power / signal_power
            if emg_ratio > EMG_POWER_RATIO_THRESHOLD:
                quality_flags[i, j, ARTIFACT_INDICES['emg']] = 1
                
            # e) Power-line noise detection
            powerline_band_indices = np.where((freqs > powerline_freq - 1) & (freqs < powerline_freq + 1))[0]
            if len(powerline_band_indices) > 0:
                powerline_peak_power = np.max(psd[powerline_band_indices])
                # Calculate average power of surrounding bands as reference
                surrounding_indices_1 = np.where((freqs > powerline_freq - 5) & (freqs < powerline_freq - 2))[0]
                surrounding_indices_2 = np.where((freqs > powerline_freq + 2) & (freqs < powerline_freq + 5))[0]
                surrounding_power = np.mean(psd[np.concatenate((surrounding_indices_1, surrounding_indices_2))])
                surrounding_power = max(surrounding_power, 1e-10) # prevent division by zero
                
                if powerline_peak_power / surrounding_power > POWERLINE_PEAK_RATIO_THRESHOLD:
                    quality_flags[i, j, ARTIFACT_INDICES['powerline']] = 1

    # 7. Calculate final scores
    for i in range(segment_num):
        for j in range(n_channels):
            # Only deduct points for non-fatal errors
            if quality_scores[i, j] > 0:
                score = 100
                if quality_flags[i, j, ARTIFACT_INDICES['emg']] == 1:
                    score -= PENALTIES['emg']
                if quality_flags[i, j, ARTIFACT_INDICES['baseline_drift']] == 1:
                    score -= PENALTIES['baseline_drift']
                if quality_flags[i, j, ARTIFACT_INDICES['powerline']] == 1:
                    score -= PENALTIES['powerline']
                quality_scores[i, j] = max(0, score) # score not below 0
    
    # 8. Generate usability matrix
    is_usable_matrix = quality_scores >= SCORE_UNUSABLE_THRESHOLD
    
    return quality_scores, quality_flags, is_usable_matrix, data

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


def visualize_eeg_quality(data, fs, segment_len_sec, quality_flags, artifact_indices):
    """
    Visualize EEG signal quality assessment results professionally (V3: optimized lines, fonts, and legend).

    Parameters:
    data (np.array): Raw EEG data (channels, samples).
    fs (int): Sampling rate (Hz).
    segment_len_sec (int): Segment length (seconds).
    quality_flags (np.array): Artifact flag matrix (segments, channels, n_artifact_types).
    artifact_indices (dict): Dictionary mapping artifact names to their indices in quality_flags.
    """
    n_channels, n_samples = data.shape
    time_axis = np.arange(n_samples) / fs

    # --- Define visualization parameters ---
    MIN_YLIM_RANGE = 100.0
    Y_PADDING_FACTOR = 0.1
    TICK_FONTSIZE = 12  # <--- new: define tick font size
    LINE_WIDTH = 1.5    # <--- new: define signal line width

    idx_to_name = {v: k for k, v in artifact_indices.items()}
    artifact_colors = {
        'saturation':     ('crimson', 0.2),
        'detachment':     ('black', 0.2),
        'emg':            ('orange', 0.2),
        'baseline_drift': ('royalblue', 0.2),
        'powerline':      ('darkviolet', 0.2),
    }

    # --- Create figure ---
    fig_height = max(16, n_channels * 1.5)
    fig, axes = plt.subplots(n_channels, 1, figsize=(20, fig_height), sharex=True, sharey=False)
    if n_channels == 1:
        axes = [axes]

    # Move main title up slightly to make room for legend
    fig.suptitle('EEG Quality Assessment Visualization', fontsize=16, y=0.98)

    # --- Iterate over each channel and plot ---
    for j in range(n_channels):
        ax = axes[j]
        channel_data = data[j, :]
        
        # 1. Dynamically calculate and set Y-axis range
        data_min, data_max = np.min(channel_data), np.max(channel_data)
        if np.isclose(data_min, data_max):
            data_min -= 1; data_max += 1
        data_range = data_max - data_min
        display_range = max(data_range, MIN_YLIM_RANGE)
        padding = display_range * Y_PADDING_FACTOR
        y_center = (data_max + data_min) / 2
        ax.set_ylim(y_center - (display_range / 2) - padding, 
                    y_center + (display_range / 2) + padding)

        # 2. Plot raw EEG signal (change: thicker lines)
        ax.plot(time_axis, channel_data, color='black', linewidth=LINE_WIDTH) # <--- change point
        ax.set_ylabel(f'Ch {j}\n(uV)', rotation=0, labelpad=25, va='center')
        ax.grid(True, linestyle=':', alpha=0.6)
        
        # (change: enlarge tick fonts)
        ax.tick_params(axis='both', which='major', labelsize=TICK_FONTSIZE) # <--- change point

        # 3. Draw artifact markers on background
        segment_num = quality_flags.shape[0]
        for i in range(segment_num):
            start_time = i * segment_len_sec
            end_time = start_time + segment_len_sec
            segment_flags = quality_flags[i, j, :]
            detected_indices = np.where(segment_flags == 1)[0]
            if len(detected_indices) > 0:
                priority_order = ['saturation', 'detachment', 'emg', 'baseline_drift', 'powerline']
                best_artifact_to_show = None
                for name in priority_order:
                    if artifact_indices[name] in detected_indices:
                        best_artifact_to_show = name
                        break
                if best_artifact_to_show:
                    color, alpha = artifact_colors[best_artifact_to_show]
                    ax.axvspan(start_time, end_time, color=color, alpha=alpha, ec=None, zorder=0)

    # --- Set axes and legend ---
    axes[-1].set_xlabel('Time (s)', fontsize=14)
    
    legend_patches = [mpatches.Patch(color=c, alpha=a, label=name.replace('_', ' ').title()) 
                      for name, (c, a) in artifact_colors.items()]
    
    # (change: place legend at top in horizontal layout)
    fig.legend(handles=legend_patches,
               loc='lower center',             # align legend bottom center
               bbox_to_anchor=(0.5, 0.92),     # place at top center of figure
               ncol=len(artifact_colors),      # horizontal arrangement
               fontsize=20,
               frameon=False)                  # remove border for cleaner look
    
    # Adjust layout to prevent label overlap and make room for top legend/title
    plt.tight_layout(rect=[0, 0, 1, 0.92]) # rect=[left, bottom, right, top]
    plt.show()

import numpy as np
from scipy import signal
import numpy as np
from scipy.fft import rfft, rfftfreq
from scipy.signal import welch

import numpy as np
from scipy.signal import welch
import os
import numpy as np
from numpy.fft import rfft, rfftfreq
from itertools import combinations

def data_reader(file_path:str):
    """Use this tool to read and decode data, returning raw data and marker information.
       Usage: data, data_marker = data_reader("1111.txt")
       data is a 2D np.array (rows=channels, cols=data_length);
       marker is a list where each entry contains the raw signal line number and event label,
       e.g., [[1008, 'trial0\n'], [1260, 'trial1-target\n']].
       Args:
           file_path: data file path.
       Returns:
           raw data, marker information
    """
    data1 = []
    data1_marker = []
    with open (file_path) as f:
        d = f.readlines()
        header_line = d[0]

        if not header_line.startswith('HEADER_DEF,'):
            raise ValueError("File header format is incorrect; must start with 'HEADER_DEF,'.")
        header_parts = header_line.strip().split(',')[1:]
        channel_indices = [i for i, part in enumerate(header_parts) if part == 'C']
        package_size = len(channel_indices)//7


        for i in range(1,len(d)):
            try:
                data_line_split = d[i].strip().split(',')
                data_line = [[float(data_line_split[x]) for x in channel_indices[j*7:j*7+7]] for j in range(package_size)]
                data1 = data1+data_line

            except:
                data1_marker.append([len(data1), d[i]])
    
    data1 = np.array(data1).transpose(1,0)

    return data1,data1_marker

def global_optimum_indices(matrix: np.ndarray) -> tuple[list[int], list[int]]:

    m, n = matrix.shape

    # Handle transpose to ensure we always enumerate the smaller dimension
    transposed = False
    if m < n:
        matrix = matrix.T
        m, n = n, m  # update dimensions
        transposed = True

    max_area = 0
    best_rows_mask = np.zeros(m, dtype=bool)
    best_cols_indices = []

    for k in range(n, 0, -1):
        if k * m <= max_area:
            break
        for col_indices in combinations(range(n), k):
            sub_matrix_cols = matrix[:, list(col_indices)]
            retained_rows_mask = np.all(sub_matrix_cols, axis=1)
            num_retained_rows = np.sum(retained_rows_mask)
            current_area = num_retained_rows * k
            
            if current_area > max_area:
                max_area = current_area
                best_rows_mask = retained_rows_mask
                best_cols_indices = list(col_indices)

    # Get row indices from boolean mask
    retained_rows_indices = np.where(best_rows_mask)[0].tolist()
    retained_cols_indices = best_cols_indices

    # If matrix was transposed, swap row and column indices back
    if transposed:
        return retained_cols_indices, retained_rows_indices
    else:
        return retained_rows_indices, retained_cols_indices
    
def get_raw_data_indices_to_keep(retained_block_rows: list[int], row_chunk_size: int) -> list[int]:

    raw_indices = []
    for block_index in retained_block_rows:
        start_index = block_index * row_chunk_size
        end_index = start_index + row_chunk_size
        # Use range to generate all raw indices within this block
        raw_indices.extend(range(start_index, end_index))
    return raw_indices

def data_selecter(data,data_marker):
    fs = 250  # Sampling frequency
    lowcut = 2
    highcut = 45
    order = 5

    filtered_data = []
    for channel in range(data.shape[0]):
        filtered_channel = butter_bandpass_filter(data[channel, :], lowcut, highcut, fs, order)
        filtered_data.append(filtered_channel)
    filtered_data = np.array(filtered_data)

    
    
    noise_value,ann_onsets, ann_durations = noise_calculation(filtered_data, data_marker)
    noise_types = ["50Hz","EMG","Baseline","outlier"]
    thresh = [10,20,40,2]
    for r in range(4):
        noise_value[:,:,r] /= thresh[r]

    selected_channel = [0,1,2,3,4,5,6]
    bool_arr = noise_value < 10

    mask = np.all(bool_arr, axis=2)
    
    retained_block_rows,retained_rows_indices = global_optimum_indices(mask)
    new_markers = []  
    if data_marker != []:

        good_data_chunks = []      # store good-segment data blocks

        current_length = 0         # current length of new data stream


        # --- 2. Iterate over segments to keep, concatenate and update ---
        for idx in retained_block_rows:
            # a) Get original start/end info of current good segment
            onset_s = ann_onsets[idx]
            duration_s = ann_durations[idx]
            
            start_sample = onset_s 
            end_sample = start_sample +duration_s
            
            
            # b) Extract good-segment data
            segment_data = data[:, start_sample:end_sample]
            good_data_chunks.append(segment_data)
            
            # c) Find and update markers located within this good segment
            for original_marker_sample, marker_info in data_marker:
                # Check if marker falls within this good segment range.
                # Note boundary condition: usually inclusive start, exclusive end.
                if start_sample <= original_marker_sample < end_sample:
                    # Calculate marker relative position within this segment
                    relative_pos = original_marker_sample - start_sample
                    
                    # Calculate marker absolute position in new continuous data stream
                    new_marker_sample = current_length + relative_pos
                    
                    new_markers.append((new_marker_sample, marker_info))
                    
            # d) Update total length of new data stream for next good segment
            segment_length = end_sample - start_sample
            current_length += segment_length

        # --- 3. Final concatenation ---
        new_eeg_data = np.concatenate(good_data_chunks, axis=1)
        new_eeg_data = new_eeg_data[retained_rows_indices,:]
    else:
        raw_rows_to_keep = get_raw_data_indices_to_keep(retained_block_rows, 1250)

        raw_rows_to_keep = np.array(raw_rows_to_keep)
        raw_rows_to_keep = raw_rows_to_keep[raw_rows_to_keep<filtered_data.shape[1]]
        new_eeg_data = filtered_data[retained_rows_indices,:]
        new_eeg_data = new_eeg_data[:,raw_rows_to_keep]
    return new_eeg_data, new_markers

def noise_calculation(data,data_marker):
    noise_value = []
    ann_onsets = []
    ann_durations = []
    n_samples = data.shape[1]
    if data_marker!= []:
        

        # Add segment from data start to first marker
        first_marker_idx = data_marker[0][0]
        
        if first_marker_idx > 0:
            ann_onsets.append(0)
            ann_durations.append(first_marker_idx)
            index = 0
            end_index = first_marker_idx
            noise_value_seg = []
            for i in range(7):
                f, Pxx = signal.welch(data[i,index:end_index], 250, nperseg=2048)
                power_50hz = np.sum(Pxx[np.where((f >= 49) & (f <= 51))])
                power_emg = np.sum(Pxx[np.where((f >= 20) & (f <= 40))])
                power_baseline = np.sum(Pxx[np.where((f >= 0.5) & (f <= 4))])
                outlier = np.where((data[i,index:end_index]<=-50) | (data[i,index:end_index]>=50))[0].shape[0]

                noise_value_seg.append([power_50hz,power_emg,power_baseline,outlier])

            noise_value.append(noise_value_seg)
        # Add segments between markers
        for i in range(len(data_marker) - 1):
            start_marker_idx = data_marker[i][0]
            end_marker_idx = data_marker[i+1][0]
            
            onset = start_marker_idx 
            duration = end_marker_idx - start_marker_idx
            
            ann_onsets.append(onset)
            ann_durations.append(duration)
            
            index = start_marker_idx
            end_index = end_marker_idx
            noise_value_seg = []
            for i in range(7):
                f, Pxx = signal.welch(data[i,index:end_index], 250, nperseg=2048)
                power_50hz = np.sum(Pxx[np.where((f >= 49) & (f <= 51))])
                power_emg = np.sum(Pxx[np.where((f >= 20) & (f <= 40))])
                power_baseline = np.sum(Pxx[np.where((f >= 0.5) & (f <= 4))])
                outlier = np.where((data[i,index:end_index]<=-50) | (data[i,index:end_index]>=50))[0].shape[0]

                noise_value_seg.append([power_50hz,power_emg,power_baseline,outlier])

            noise_value.append(noise_value_seg)

            
        # Add segment from last marker to data end
        last_marker_idx = data_marker[-1][0]
        if last_marker_idx < n_samples:
            ann_onsets.append(last_marker_idx)
            ann_durations.append((n_samples - last_marker_idx))

            
            index = last_marker_idx
            noise_value_seg = []
            for i in range(7):
                f, Pxx = signal.welch(data[i,index:], 250, nperseg=2048)
                power_50hz = np.sum(Pxx[np.where((f >= 49) & (f <= 51))])
                power_emg = np.sum(Pxx[np.where((f >= 20) & (f <= 40))])
                power_baseline = np.sum(Pxx[np.where((f >= 0.5) & (f <= 4))])
                outlier = np.where((data[i,index:]<=-50) | (data[i,index:]>=50))[0].shape[0]

                noise_value_seg.append([power_50hz,power_emg,power_baseline,outlier])

            noise_value.append(noise_value_seg)
    else:

        data_length = data.shape[1]

        for index in range(0,data_length,1250):

            noise_value_seg = []
            for i in range(7):
                end_index = min(index+1250,data_length-1)

                f, Pxx = signal.welch(data[i,index:end_index], 250, nperseg=2048)
                power_50hz = np.sum(Pxx[np.where((f >= 49) & (f <= 51))])
                power_emg = np.sum(Pxx[np.where((f >= 20) & (f <= 40))])
                power_baseline = np.sum(Pxx[np.where((f >= 0.5) & (f <= 4))])
                outlier = np.where((data[i,index:end_index]<=-50) | (data[i,index:end_index]>=50))[0].shape[0]

                noise_value_seg.append([power_50hz,power_emg,power_baseline,outlier])

            noise_value.append(noise_value_seg)
    noise_value = np.array(noise_value)

    return noise_value,ann_onsets, ann_durations

def butter_bandpass_filter(data1, lowcut, highcut, fs, order):  

    nyq = 0.5 * fs  
    low = lowcut / nyq  
    high = highcut / nyq  
    b, a = signal.butter(order, [low, high], btype='band')   
    y = signal.filtfilt(b, a, data1)  
    return y  


