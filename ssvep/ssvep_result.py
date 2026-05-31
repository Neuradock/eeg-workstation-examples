

from Neuradock_lib import data_reader, butter_bandpass_filter, data_selecter
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import welch  # import welch method for PSD calculation
import matplotlib as mpl
mpl.rcParams['pdf.fonttype'] = 42
mpl.rcParams['ps.fonttype'] = 42
# ================= Parameters =================
file_path = '1.txt'
fs = 250
epoch_len = 1000  # extracted length (2.4 seconds)
# num_channels = 7

# ================= Data reading and preprocessing =================
data, data_marker = data_reader(file_path)

# data_marker = data_marker[:10] # Uncomment if limiting marker count is needed
data, data_marker = data_selecter(data, data_marker)
print(f"Markers count: {len(data_marker)}")
num_channels = data.shape[0]

# Filtering (apply to all channels)
filtered_data = []
for i in range(num_channels):
    # Assuming butter_bandpass_filter returns a 1D array
    filtered_data.append(butter_bandpass_filter(data[i], 2, 80, fs, 5))
filtered_data = np.array(filtered_data) # shape: (num_channels, total_samples)

# ================= Plot preparation =================
# Create canvas with num_channels rows and 2 columns
# First column: Time Domain
# Second column: Frequency Domain / PSD
fig, axes = plt.subplots(num_channels, 2, figsize=(14, 3 * num_channels))

# Adjust layout to prevent overlap, especially with many rows
plt.subplots_adjust(hspace=0.4)

# If only one channel, axes shape may be (2,); reshape to (1, 2)
if num_channels == 1:
    axes = np.expand_dims(axes, axis=0)

# ================= Process each channel =================
for ch in range(num_channels):
    data_i_list = []
    
    # 1. Extract epochs
    for marker in data_marker:
        start_idx = marker[0]
        end_idx = start_idx + epoch_len
        
        # Boundary check
        if end_idx <= filtered_data.shape[1]:
            segment = filtered_data[ch, start_idx:end_idx]
            data_i_list.append(segment)
    
    # Skip if no valid epochs extracted
    if not data_i_list:
        print(f"Channel {ch+1}: No valid epochs found.")
        continue

    # shape: (num_epochs, epoch_len)
    epochs_array = np.array(data_i_list) 
    
    # Calculate ERP average
    # axis=0 averages across trials
    channel_mean = np.mean(epochs_array, axis=0)
    
    # ================= Plot first column: time-domain ERP =================
    ax_time = axes[ch, 0]
    
    # Plot faint gray lines for single trials
    for epoch in epochs_array:
        ax_time.plot(epoch, linewidth=0.5, color='gray', alpha=0.3)
        
    # Plot thick line for averaged ERP
    ax_time.plot(channel_mean, linewidth=1.5, color='blue', label='Mean')
    
    ax_time.set_title(f'Ch {ch+1} - Time Domain (ERP)', fontsize=10)
    ax_time.grid(True, linestyle='--', alpha=0.5)
    
    # ================= Plot second column: PSD of averaged marker =================
    ax_psd = axes[ch, 1]
    
    # Calculate power spectral density (PSD)
    # Setting nperseg=epoch_len gives full resolution for this window length
    f, Pxx = welch(channel_mean, fs=fs, nperseg=len(channel_mean))
    
    # Plot PSD curve
    ax_psd.plot(f, Pxx, color='red', linewidth=1.5, label='PSD')
    
    # Set PSD plot properties
    ax_psd.set_title(f'Ch {ch+1} - PSD (of Mean)', fontsize=10)
    ax_psd.grid(True, linestyle='--', alpha=0.5)
    ax_psd.set_ylabel('Power/Frequency')
    
    # Since filter range is 2-45Hz, limit X-axis for clarity (e.g., 0-60Hz)
    ax_psd.set_xlim(0, 60)

    # ================= Set axis labels (only last row) =================
    if ch == num_channels - 1:
        ax_time.set_xlabel('Time (samples)')
        ax_psd.set_xlabel('Frequency (Hz)')

# ================= Save figure =================
plt.tight_layout()
save_name = "7_channels_mean_and_psd15hz.pdf"
plt.savefig(save_name)
print(f"Plot saved to {save_name}")
plt.close()