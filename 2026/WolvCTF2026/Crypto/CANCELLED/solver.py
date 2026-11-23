import sys
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, decimate, sosfiltfilt, spectrogram

wav1 = sys.argv[1] if len(sys.argv) > 1 else "wav1.wav"
wav2 = sys.argv[2] if len(sys.argv) > 2 else "wav2.wav"
out = sys.argv[3] if len(sys.argv) > 3 else "flag.png"

sr, a = wavfile.read(wav1)
sr2, b = wavfile.read(wav2)
assert sr == sr2 and a.shape == b.shape
d = a.astype(np.float64) - b.astype(np.float64)
d = sosfiltfilt(butter(6, 30, fs=sr, output="sos"), d)
x = decimate(decimate(d, 9), 7)
fs = sr / 63

f, t, S = spectrogram(x, fs=fs, nperseg=700, noverlap=680, nfft=8192)
m = f < 22
L = 10 * np.log10(S[m] + 1e-6)

plt.figure(figsize=(36, 5))
plt.pcolormesh(t, f[m], L, cmap="gray", shading="auto", vmin=np.percentile(L, 65))
plt.xlabel("time [s]")
plt.ylabel("freq [Hz]")
plt.tight_layout()
plt.savefig(out, dpi=50)
print(f"[+] saved {out}")
print("[+] 上段(13-19Hz) -> 下段(2-8Hz) の順に読む")
