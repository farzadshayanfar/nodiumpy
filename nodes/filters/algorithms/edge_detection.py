import numpy as np
from numpy.fft import fft2, fftshift, ifft2


def pst(img: np.ndarray,
        phaseStrength: float,
        warpStrength: float,
        lpfSigma: float,
        minThreshold: float,
        maxThreshold: float,
        useMorph: bool) -> np.ndarray:
    height = img.shape[0]
    width = img.shape[1]
    u = np.linspace(-0.5, 0.5, height, dtype=np.float32)
    v = np.linspace(-0.5, 0.5, width, dtype=np.float32)
    U, V = np.meshgrid(u, v, indexing="ij")
    theta = np.arctan2(V, U)
    rho = np.hypot(U, V)
    kernel = warpStrength * rho * np.arctan(warpStrength * rho) - 0.5 * np.log(1 + (warpStrength * rho) ** 2)
    kernel = phaseStrength * kernel / np.max(kernel)

    # denoising
    img_orig = np.fft.fft2(img)
    expo = np.fft.fftshift(np.exp(-0.5 * np.power((np.divide(rho, np.sqrt((lpfSigma ** 2) / np.log(2)))), 2)))
    img_denoised = np.real(np.fft.ifft2((np.multiply(img_orig, expo)))).astype(np.float32)

    img_pst = ifft2(fft2(img_denoised) * fftshift(np.exp(-1j * kernel)))
    x = np.angle(img_pst).astype(np.float32)
    pst_feature = (x - x.min()) / (x.max() - x.min())

    if useMorph:
        if len(pst_feature.shape) == 3:
            quantile_max = np.quantile(pst_feature[::4, ::4, ::4], maxThreshold)
            quantile_min = np.quantile(pst_feature[::4, ::4, ::4], minThreshold)
        elif len(pst_feature.shape) == 2:
            quantile_max = np.quantile(pst_feature[::4, ::4], maxThreshold)
            quantile_min = np.quantile(pst_feature[::4, ::4], minThreshold)

        digital_feature = np.zeros(pst_feature.shape)
        digital_feature[pst_feature > quantile_max] = 1
        digital_feature[pst_feature < quantile_min] = 1
        digital_feature[img < (np.amax(img) / 20)] = 0
        digital_feature = digital_feature.real.astype(np.float32)
        return digital_feature

    pst_feature = pst_feature.real
    return pst_feature


def page(img: np.ndarray,
         directionBins: int,
         mu1: float,
         mu2: float,
         sigma1: float,
         sigma2: float,
         phaseStrength1: float,
         phaseStrength2: float,
         lpfSigma: float,
         minThreshold: float,
         maxThreshold: float,
         useMorph: bool) -> np.ndarray:
    height = img.shape[0]
    width = img.shape[1]

    # set the frequency grid
    u = np.linspace(-0.5, 0.5, height)
    v = np.linspace(-0.5, 0.5, width)
    U, V = np.meshgrid(u, v, indexing="ij")

    theta = np.arctan2(V, U)
    rho = np.hypot(U, V)

    minDirection = np.pi / 180
    directionSpan = np.pi / directionBins
    directions = np.arange(start=minDirection, stop=np.pi, step=directionSpan)

    # create PAGE kernels channel by channel
    kernel = np.zeros(shape=(height, width, directionBins))

    for i in range(directionBins):
        tetav = directions[i]

        # Project onto new directionality basis for PAGE filter creation
        Uprime = U * np.cos(tetav) + V * np.sin(tetav)
        Vprime = -U * np.sin(tetav) + V * np.cos(tetav)

        # Create Normal component of PAGE filter
        Phi_1 = np.exp(-0.5 * ((abs(Uprime) - mu1) / sigma1) ** 2) / (1 * np.sqrt(2 * np.pi) * sigma1)
        Phi_1 = (Phi_1 / np.max(Phi_1[:])) * phaseStrength1

        # Create Log-Normal component of PAGE filter
        Phi_2 = np.exp(-0.5 * ((np.log(abs(Vprime)) - mu2) / sigma2) ** 2) / (abs(Vprime) * np.sqrt(2 * np.pi) * sigma2)
        Phi_2 = (Phi_2 / np.max(Phi_2[:])) * phaseStrength2

        # Add overall directional filter to PAGE filter array
        kernel[:, :, i] = Phi_1 * Phi_2

    # denoise on the loaded image
    img_orig = np.fft.fft2(img)
    expo = np.fft.fftshift(np.exp(-0.5 * np.power((np.divide(rho, np.sqrt((lpfSigma ** 2) / np.log(2)))), 2)))
    img_denoised = np.real(np.fft.ifft2((np.multiply(img_orig, expo))))
    page_output = np.zeros(shape=(height, width, directionBins))

    # apply the kernel channel by channel
    for i in range(directionBins):
        img_page = ifft2(fft2(img_denoised) * fftshift(np.exp(-1j * kernel[:, :, i])))
        x = np.angle(img_page)
        page_feature = (x - x.min()) / (x.max() - x.min())

        # apply morphological operation if applicable
        if useMorph:
            if len(page_feature.shape) == 3:
                quantile_max = np.quantile(page_feature[::4, ::4, ::4], maxThreshold)
                quantile_min = np.quantile(page_feature[::4, ::4, ::4], minThreshold)
            elif len(page_feature.shape) == 2:
                quantile_max = np.quantile(page_feature[::4, ::4], maxThreshold)
                quantile_min = np.quantile(page_feature[::4, ::4], minThreshold)

            digital_feature = np.zeros(page_feature.shape)
            digital_feature[page_feature > quantile_max] = 1
            digital_feature[page_feature < quantile_min] = 1
            digital_feature[img < (np.amax(img) / 20)] = 0
            page_output[:, :, i] = digital_feature

        else:
            page_output[:, :, i] = page_feature

    # Create a weighted color image of PAGE output to visualize directionality of edges
    weight_step = 255 * 3 / directionBins
    color_weight = np.arange(0, 255, weight_step)
    page_edge = np.zeros(shape=(height, width, 3))
    # step_edge = int(round(self.direction_bins/3))
    step_edge = directionBins // 3
    for i in range(step_edge):
        page_edge[:, :, 0] = (color_weight[i] * page_output[:, :, i] + page_edge[:, :, 0])
        page_edge[:, :, 1] = (color_weight[i] * page_output[:, :, i + step_edge] + page_edge[:, :, 1])
        page_edge[:, :, 2] = (color_weight[i] * page_output[:, :, i + (2 * step_edge)] + page_edge[:, :, 2])

    page_edge = (page_edge - np.min(page_edge)) / (np.max(page_edge) - np.min(page_edge))
    return page_edge.astype(np.float32)
