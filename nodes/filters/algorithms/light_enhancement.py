import cv2
import numpy as np
from numpy.fft import fft2, fftshift, ifft2


def vevid(img: np.ndarray,
          phaseStrength: float,
          spectralPhaseFcnVariance: float,
          regularizationTerm: float,
          phaseActivationGain: float,
          enhanceColor: bool,
          liteMode: bool):
    img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)

    height = img.shape[0]
    width = img.shape[1]

    # set the frequency grid
    u = np.linspace(-0.5, 0.5, height)
    v = np.linspace(-0.5, 0.5, width)
    U, V = np.meshgrid(u, v, indexing="ij")

    # construct the kernel
    theta = np.arctan2(V, U)
    rho = np.hypot(U, V)

    kernel = np.exp(-rho ** 2 / spectralPhaseFcnVariance)
    kernel = (kernel / np.max(abs(kernel))) * phaseStrength

    if enhanceColor:
        channel_idx = 1
    else:
        channel_idx = 2

    vevid_input = img[:, :, channel_idx]

    if liteMode:
        vevid_phase = np.arctan2(-phaseActivationGain * (vevid_input + regularizationTerm), vevid_input)
    else:
        vevid_input_f = fft2(vevid_input + regularizationTerm)
        img_vevid = ifft2(vevid_input_f * fftshift(np.exp(-1j * kernel)))
        vevid_phase = np.arctan2(phaseActivationGain * np.imag(img_vevid), vevid_input)
    vevid_phase_norm = (vevid_phase - vevid_phase.min()) / (vevid_phase.max() - vevid_phase.min())
    img[:, :, channel_idx] = vevid_phase_norm
    img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX)

    img = cv2.cvtColor(img, cv2.COLOR_HSV2RGB)
    vevid_output = cv2.cvtColor(img, cv2.COLOR_RGB2RGBA)

    return vevid_output
