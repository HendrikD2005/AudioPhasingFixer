from pydub import AudioSegment
import numpy as np
import soundfile as sf
from scipy.signal import hilbert

# Adjust the 'time_shift_ms' variable as needed if the phasing issues still exist
def fix_phasing(input_path, output_path, time_shift_ms=10.0, bass_cut_freq=200):
    # Loading audio file
    audio = AudioSegment.from_file(input_path).set_channels(2)
    samples = np.array(audio.get_array_of_samples()).reshape((-1, 2))
    sample_rate = audio.frame_rate

    # Extract Left & Right Channel
    left, right = samples[:, 0], samples[:, 1]

    # Correlation Analysis
    corr = np.corrcoef(left, right)[0, 1]
    print(f"Stereo Correlation: {corr:.2f}")

    # Minimal Delay on Right Channel
    if corr < 0.3:
        print("⛑ Phasing detected: Time offset will be applied to the sound.")
        delay_samples = int((time_shift_ms / 1000.0) * sample_rate)
        right = np.concatenate((np.zeros(delay_samples), right))[:len(right)]
    
    # Mid/Side Converting
    mid = (left + right) / 2.0
    side = (left - right) / 2.0

    # Side: Low-Cut (Bass area)
    from scipy.fft import rfft, irfft, rfftfreq
    fft = rfft(side)
    freqs = rfftfreq(len(side), d=1/sample_rate)
    fft[freqs < bass_cut_freq] = 0
    side = irfft(fft)

    # Reconversion to Left & Right Channel
    left_fixed = mid + side
    right_fixed = mid - side

    # Normalization
    max_val = np.max(np.abs([left_fixed, right_fixed]))
    left_fixed = left_fixed / max_val
    right_fixed = right_fixed / max_val

    # Save
    stereo_fixed = np.stack((left_fixed, right_fixed), axis=-1)
    sf.write(output_path, stereo_fixed, sample_rate)
    print(f"Exported to: {output_path}")

# Main
if __name__ == "__main__":
    fix_phasing("file-to-convert.<mp3/wav/[...]>", "converted-file-name.<mp3/wav[...]>")
