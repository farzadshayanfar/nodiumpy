from pathlib import Path
from typing import Union

import cv2
import dearpygui.dearpygui as dpg
import numpy as np

from node_editor.connection_objects import NodeAttribute, AttributeType
from node_editor.editor import NodeEditor
from nodes.node import NodeBase


class Node(NodeBase):
    nodeLabel = "Video Writer"

    _encoderType = {".mp4": "mp4v", ".avi": "DIVX"}
    _settings = None

    def __init__(self,
                 tag: int,
                 pos: tuple[int, int],
                 editorHandle: NodeEditor):
        super().__init__(tag=tag, editor=editorHandle)
        self._width: int = self.settings.nodeWidth
        self._folderDialogTag: int = editorHandle.getUniqueTag()
        self._outDirPath: Union[Path, None] = None
        self._outDirTextInputTag: int = editorHandle.getUniqueTag()
        self._outDirBrowseBtnTag: int = editorHandle.getUniqueTag()
        self._fileBaseName: str = str()
        self._nameChangerInt: int = 1
        self._nameChangeIntTextTag: int = editorHandle.getUniqueTag()
        self._baseNameTextInputTag: int = editorHandle.getUniqueTag()
        self._sizeInputTag: int = editorHandle.getUniqueTag()
        self._size: tuple[int, int] = (1280, 720)
        self._fpsInputTag: int = editorHandle.getUniqueTag()
        self._fpsRange: tuple = (1, 60)
        self._fps: int = 24
        self._fileFormat: str = list(self._encoderType.keys())[0]
        self._saveModes: list[str] = ["record stop", "frame limit"]
        self._saveMode: str = self._saveModes[0]
        self._frameLimitGroupTag: int = editorHandle.getUniqueTag()
        self._frameLimitInputTag: int = editorHandle.getUniqueTag()
        self._frameLimitMin: int = 10
        self._frameLimit: int = 240
        self._currentImage: np.ndarray = np.zeros(shape=(2, 2))
        self._frameCache: list[np.ndarray] = list()
        self._isRecording: bool = True
        self._overwrite: bool = True

        self._attrImageInput = NodeAttribute(tag=editorHandle.getUniqueTag(),
                                             parentNodeTag=self._tag,
                                             attrType=AttributeType.Image)

        with dpg.node(tag=self._tag,
                      parent=editorHandle.tag,
                      label=self.nodeLabel,
                      pos=pos):
            with dpg.node_attribute(tag=self._attrImageInput.tag,
                                    attribute_type=dpg.mvNode_Attr_Input,
                                    user_data=self._attrImageInput,
                                    shape=dpg.mvNode_PinShape_QuadFilled,
                                    indent=5):
                editorHandle.createFolderSelectionDialog(tag=self._folderDialogTag, callback=self.__callbackSetOutDir)
                dpg.add_button(label="select out dir",
                               width=self._width - 10,
                               callback=lambda: dpg.show_item(item=self._folderDialogTag))
                with dpg.group(horizontal=True):
                    dpg.add_text(default_value="out dir", indent=15)
                    dpg.add_input_text(tag=self._outDirTextInputTag,
                                       width=self._width - 90,
                                       readonly=True)

                with dpg.group(horizontal=True):
                    dpg.add_text(default_value="base name")
                    dpg.add_input_text(tag=self._baseNameTextInputTag,
                                       width=self._width - 90,
                                       callback=self.__callbackBaseNameChange)

                with dpg.group(horizontal=True):
                    dpg.add_text(default_value="fps", indent=48)
                    dpg.add_input_int(tag=self._fpsInputTag,
                                      min_value=self._fpsRange[0],
                                      max_value=self._fpsRange[1],
                                      default_value=self._fps,
                                      width=self._width - 90,
                                      min_clamped=True,
                                      max_clamped=True,
                                      callback=self.__callbackFPSChange)

                with dpg.group(horizontal=True):
                    dpg.add_text(default_value="size", indent=40)
                    dpg.add_input_intx(tag=self._sizeInputTag, size=2, default_value=self._size,
                                       width=self._width - 90, callback=self.__callbackSizeChange)

                with dpg.group(horizontal=True):
                    dpg.add_text(default_value="format", indent=23)
                    dpg.add_combo(items=list(self._encoderType.keys()),
                                  default_value=self._fileFormat,
                                  width=self._width - 90,
                                  callback=self.__callbackFileFormatChange)

                with dpg.group(horizontal=True):
                    dpg.add_text(default_value="save mode", indent=0)
                    dpg.add_combo(items=self._saveModes,
                                  default_value=self._saveMode,
                                  width=self._width - 90,
                                  callback=self.__callbackSaveModeChange)

                with dpg.group(tag=self._frameLimitGroupTag, horizontal=True, show=False):
                    dpg.add_text(default_value="limit", indent=32)
                    dpg.add_input_int(tag=self._frameLimitInputTag,
                                      width=self._width - 90,
                                      min_value=self._frameLimitMin,
                                      min_clamped=True,
                                      default_value=self._frameLimit,
                                      callback=self.__callbackLimitChange)

                dpg.add_checkbox(label="record",
                                 default_value=self._isRecording,
                                 callback=self.__callbackRecordStateChange)

                dpg.add_checkbox(label="overwrite existing",
                                 default_value=self._overwrite,
                                 callback=self.__callbackOverWriteStateChange)

                with dpg.group(horizontal=True, horizontal_spacing=5, indent=50):
                    dpg.add_text(tag=self._nameChangeIntTextTag, default_value="unq int: 1")
                    dpg.add_button(label="R", width=30, height=30, callback=self.__callbackResetNameChanger)

    def update(self):
        if self._outDirPath is None:
            return

        if not self._isRecording:
            return

        data = self._attrImageInput.data

        if data is None:
            return

        if np.array_equal(data, self._currentImage):
            return

        self._currentImage = data.copy()
        self._frameCache.append(self._currentImage)
        print(len(self._frameCache))
        if self._saveMode == "frame limit":
            if len(self._frameCache) < self._frameLimit:
                return
            frames = self._frameCache.copy()
            self.__writeVideo(frames=frames)
            self._frameCache.clear()

    def __writeVideo(self, frames: list[np.ndarray]):
        filePath = self._outDirPath.joinpath(self._fileBaseName + "_"
                                             + str(self._nameChangerInt)
                                             + self._fileFormat)
        if filePath.exists() and not self._overwrite:
            return
        self._nameChangerInt += 1
        dpg.set_value(item=self._nameChangeIntTextTag, value=f"unq int: {self._nameChangerInt}")
        theFormat = self._encoderType[self._fileFormat]
        encoder = cv2.VideoWriter_fourcc(*theFormat)
        writer = cv2.VideoWriter(str(filePath.resolve()),
                                 encoder,
                                 self._fps,
                                 self._size,
                                 True)
        for frame in frames:
            writer.write(frame[:, :, ::-1])
        writer.release()

    def __callbackSetOutDir(self, _, data):
        self._outDirPath = Path(data["file_path_name"])
        dpg.set_value(item=self._outDirTextInputTag, value=str(self._outDirPath.resolve()))
        self.__callbackResetNameChanger()

    def __callbackBaseNameChange(self, _, data):
        self._fileBaseName = data

    def __callbackFPSChange(self, _, data):
        self._fps = data

    def __callbackSizeChange(self, _, data):
        self._size = data

    def __callbackLimitChange(self, _, data):
        self._frameLimit = data

    def __callbackRecordStateChange(self, _, data):
        self._isRecording = data
        if self._outDirPath is None:
            return
        if not data:
            if self._frameCache:
                frames = self._frameCache.copy()
                self.__writeVideo(frames=frames)
                self._frameCache.clear()

    def __callbackOverWriteStateChange(self, _, data):
        self._overwrite = data

    def __callbackFileFormatChange(self, _, data):
        self._fileFormat = data

    def __callbackSaveModeChange(self, _, data):
        if data == "record stop":
            dpg.hide_item(item=self._frameLimitGroupTag)
        else:
            dpg.show_item(item=self._frameLimitGroupTag)
        self._saveMode = data

    def __callbackResetNameChanger(self):
        self._nameChangerInt = 1
        dpg.set_value(item=self._nameChangeIntTextTag, value="unq int: 1")
