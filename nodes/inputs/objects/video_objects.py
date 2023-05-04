from pathlib import Path
from typing import Union, Iterator

import cv2
import numpy as np


class VideoFile:
    def __init__(self, inputFile: Union[Path, str]):
        filePath = Path(inputFile)
        assert filePath.exists() and filePath.is_file()
        self._VC = cv2.VideoCapture(str(filePath.resolve()))
        self._fps: int = self._VC.get(cv2.CAP_PROP_FPS)
        self._frameCount: int = self._VC.get(cv2.CAP_PROP_FRAME_COUNT)
        self._currentFrame: int = 0

    @property
    def videoCapture(self):
        return self._VC

    @property
    def fps(self):
        return self._fps

    @property
    def frameCount(self):
        return self._frameCount

    @property
    def currentFrame(self):
        return self.videoCapture.get(cv2.CAP_PROP_POS_FRAMES)

    @currentFrame.setter
    def currentFrame(self, value):
        self._currentFrame = value
        self.videoCapture.set(cv2.CAP_PROP_POS_FRAMES, value)

    @property
    def isOpened(self):
        return self.videoCapture.isOpened()

    def readCurrentFrame(self) -> np.ndarray:
        success, frame = self.videoCapture.read()
        if success:
            # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return frame

    def readNextFrame(self) -> np.ndarray:
        self.currentFrame += 1
        return self.readCurrentFrame()

    def retrieveFrame(self, frameIndex: int) -> np.ndarray:
        self.currentFrame = frameIndex
        return self.readCurrentFrame()

    def getFramesEveryNSeconds(self, n: float) -> Iterator[np.ndarray]:
        numberOfFramesToReturn = int(self.frameCount / self.fps / n)
        frameIndices = np.linspace(start=0,
                                   stop=self.frameCount,
                                   num=numberOfFramesToReturn,
                                   endpoint=False,
                                   dtype=np.int)

        return (self.retrieveFrame(idx) for idx in frameIndices)

    def getFrameEveryNFrame(self, n: int) -> Iterator[np.ndarray]:
        numberOfFramesToReturn = int(self.frameCount / n)
        frameIndices = np.linspace(start=0,
                                   stop=self.frameCount,
                                   num=numberOfFramesToReturn,
                                   endpoint=False,
                                   dtype=np.int)
        return (self.retrieveFrame(idx) for idx in frameIndices)

    def getInterval(self, startFrame: int, endFrame: int) -> Iterator[np.ndarray]:
        """

        :param startFrame: startFrame is included
        :param endFrame: startFrame is included
        :return:
        """
        assert startFrame < endFrame
        if endFrame + 1 < self.frameCount:
            results = (self.retrieveFrame(frameIndex=idx) for idx in range(startFrame, endFrame + 1))
        else:
            results = (self.retrieveFrame(frameIndex=idx) for idx in range(startFrame, self.frameCount - 1))
        return results

    def closeVideoFile(self):
        if self.isOpened:
            self.videoCapture.release()
