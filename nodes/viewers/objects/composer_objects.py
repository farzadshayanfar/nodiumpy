import enum
import random
from typing import Union

import cv2
import numpy as np


class BlendModes(enum.Enum):
    NORMAL = 0
    DISSOLVE = 1
    DANCING_DISSOLVE = 2
    MULTIPLY = 3
    SCREEN = 4
    OVERLAY = 5
    SUBTRACT = 6
    DIFFERENCE = 7


class Canvas:
    defaultWidth: int = 1920
    defaultHeight: int = 1080
    defaultColor: tuple[int, int, int, int] = (1, 1, 1, 1)

    def __init__(self):
        self._width: int = self.defaultWidth
        self._height: int = self.defaultHeight
        self._color = self.defaultColor
        self._img: np.ndarray = np.nan
        self._layers: list[CanvasImage] = list()
        self.createBackground()

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value: int):
        self._width = value
        self.createBackground()

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value: int):
        self._height = value
        self.createBackground()

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, value: tuple[int, int, int, int]):
        self._color = value
        self.createBackground()

    def createBackground(self):
        reds: np.ndarray = np.ones(shape=(self._height, self._width), dtype=np.float32) * self._color[0]
        greens: np.ndarray = np.ones(shape=(self._height, self._width), dtype=np.float32) * self._color[1]
        blues: np.ndarray = np.ones(shape=(self._height, self._width), dtype=np.float32) * self._color[2]
        alphas: np.ndarray = np.ones(shape=(self._height, self._width), dtype=np.float32) * self._color[3]
        self._img = (np.dstack(tup=(reds, greens, blues, alphas))).astype(np.float32)

    @property
    def layers(self):
        return self._layers

    def render(self) -> np.ndarray:
        img = self._img.copy()
        canvasHeight, canvasWidth = img.shape[:2]
        layers = self._layers.copy()
        layers.reverse()

        for layer in layers:
            if layer.currentImage is None:
                continue
            layerImage = layer.currentImage.copy()
            layerWidth = layer.currentWidth
            layerHeight = layer.currentHeight
            layerTop = layer.top
            layerLeft = layer.left
            layerAlpha = layer.opacity / 100
            layerBlendMode = layer.blendMode
            staticDissolveSeed = layer.staticDissolveSeed

            if layer.currentImage is None:
                continue
            if layerTop > canvasHeight \
                    or layerTop + canvasHeight < 0 \
                    or layerLeft > canvasWidth \
                    or layerLeft + canvasWidth < 0:
                continue

            # canvas start and end indices
            canvasRowStart = layerTop if layerTop > 0 else 0
            canvasRowEnd = layerTop + layerHeight
            if canvasRowEnd > canvasHeight:
                canvasRowEnd = canvasHeight

            canvasColStart = layerLeft if layerLeft > 0 else 0
            canvasColEnd = layerLeft + layerWidth
            if canvasColEnd > canvasWidth:
                canvasColEnd = canvasWidth

            # layer start and end indices
            layerRowStart = 0 if layerTop > 0 else abs(layerTop)
            if layerTop + layerHeight < canvasHeight:
                layerRowEnd = layerHeight
            else:
                layerRowEnd = canvasHeight - layerTop

            layerColStart = 0 if layerLeft > 0 else abs(layerLeft)
            if layerLeft + layerWidth < canvasWidth:
                layerColEnd = layerWidth
            else:
                layerColEnd = canvasWidth - layerLeft

            layerImage = layerImage[layerRowStart:layerRowEnd, layerColStart:layerColEnd]
            canvasRegion = img[canvasRowStart:canvasRowEnd, canvasColStart:canvasColEnd]
            indices2Fade = layerImage[:, :, 3] == 0
            pixels2replace = canvasRegion[indices2Fade].copy()

            # adding layers and applying blend mode
            if layerBlendMode == BlendModes.NORMAL:
                canvasRegion *= (1 - layerAlpha)
                canvasRegion += layerImage * layerAlpha

            elif layerBlendMode == BlendModes.DISSOLVE or layerBlendMode == BlendModes.DANCING_DISSOLVE:
                if layerBlendMode == BlendModes.DISSOLVE:
                    np.random.seed(staticDissolveSeed)
                indices = np.random.choice(a=[True, False],
                                           size=(layerRowEnd - layerRowStart, layerColEnd - layerColStart),
                                           p=(layerAlpha, 1 - layerAlpha))
                canvasRegion[indices] = 0
                layerImage[np.logical_not(indices)] = 0
                canvasRegion += layerImage

            elif layer.blendMode == BlendModes.MULTIPLY:
                layerImage *= canvasRegion
                canvasRegion *= (1 - layerAlpha)
                canvasRegion += layerImage * layerAlpha

            elif layer.blendMode == BlendModes.SCREEN:
                layerImage = 1 - (1 - layerImage) * (1 - canvasRegion)
                canvasRegion *= (1 - layerAlpha)
                canvasRegion += layerImage * layerAlpha

            elif layer.blendMode == BlendModes.OVERLAY:
                pass
                piece1 = layerImage * canvasRegion * 2
                piece2 = 1 - 2 * (1 - layerImage) * (1 - canvasRegion)
                condition = canvasRegion < 0.5
                layerImage = np.where(condition, piece1, piece2)
                canvasRegion *= (1 - layerAlpha)
                canvasRegion += layerImage * layerAlpha

            elif layer.blendMode == BlendModes.SUBTRACT:
                layerImage[:, :, :3] = canvasRegion[:, :, :3] - layerImage[:, :, :3]
                layerImage[layerImage < 0] = 0
                canvasRegion *= (1 - layerAlpha)
                canvasRegion += layerImage * layerAlpha

            elif layer.blendMode == BlendModes.DIFFERENCE:
                pass

            canvasRegion[indices2Fade] = pixels2replace
        return img


class CanvasImage:
    def __init__(self):
        self._src: Union[np.ndarray, None] = None
        self._width: int = 0
        self._height: int = 0
        self._currentImage: Union[np.ndarray, None] = None
        self._currentWidth: int = 0
        self._currentHeight: int = 0
        self._scale: int = 1
        self._left: int = 0
        self._top: int = 0
        self._rot: float = 0
        self._blendMode: BlendModes = BlendModes.NORMAL
        self._opacity: int = 100
        self._staticDissolveSeed = random.randint(a=1, b=1000)

    @property
    def src(self):
        return self._src

    @src.setter
    def src(self, value: Union[np.ndarray, None]):
        self._src = value
        if value is None:
            self._currentImage = None
            return
        self._width = self._src.shape[1]
        self._height = self._src.shape[0]
        self.__update()

    @property
    def currentWidth(self):
        return self._currentWidth

    @property
    def currentHeight(self):
        return self._currentHeight

    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, value: float):
        self._scale = value
        self.__update()

    @property
    def left(self):
        return self._left

    @left.setter
    def left(self, value: int):
        self._left = value

    @property
    def top(self):
        return self._top

    @top.setter
    def top(self, value: int):
        self._top = value

    @property
    def rot(self):
        return self._rot

    @rot.setter
    def rot(self, value: float):
        self._rot = value
        self.__update()

    @property
    def blendMode(self):
        return self._blendMode

    @blendMode.setter
    def blendMode(self, value: BlendModes):
        self._blendMode = value

    @property
    def opacity(self):
        return self._opacity

    @opacity.setter
    def opacity(self, value: int):
        self._opacity = value

    @property
    def staticDissolveSeed(self):
        return self._staticDissolveSeed

    @property
    def currentImage(self):
        return self._currentImage

    def __update(self):
        self._currentImage = self.rotate_image(mat=self._src, angle=self._rot)
        self._currentWidth = int(self._currentImage.shape[1] * self._scale)
        self._currentHeight = int(self._currentImage.shape[0] * self._scale)
        self._currentImage = cv2.resize(src=self._currentImage, dsize=(self._currentWidth, self._currentHeight))

    def rotate_image(self, mat, angle):
        """
        Rotates an image (angle in degrees) and expands image to avoid cropping
        """

        height, width = mat.shape[:2]
        image_center = (width / 2,
                        height / 2)

        rotation_mat = cv2.getRotationMatrix2D(center=image_center, angle=angle, scale=1)

        # rotation calculates the cos and sin, taking absolutes of those.
        abs_cos = abs(rotation_mat[0, 0])
        abs_sin = abs(rotation_mat[0, 1])

        # find the new width and height bounds
        bound_w = int(height * abs_sin + width * abs_cos)
        bound_h = int(height * abs_cos + width * abs_sin)

        # subtract old image center (bringing image back to origo) and adding the new image center coordinates
        rotation_mat[0, 2] += bound_w / 2 - image_center[0]
        rotation_mat[1, 2] += bound_h / 2 - image_center[1]

        # rotate image with the new bounds and translated rotation matrix
        rotated_mat = cv2.warpAffine(src=mat, M=rotation_mat, dsize=(bound_w, bound_h), borderValue=0)
        return rotated_mat
