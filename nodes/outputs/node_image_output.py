from pathlib import Path
from typing import Union

import cv2
import dearpygui.dearpygui as dpg
import numpy as np

from node_editor.connection_objects import NodeAttribute, AttributeType
from node_editor.editor import NodeEditor
from nodes.node import NodeBase


class Node(NodeBase):
    nodeLabel = "Image Writer"

    _formats = [".jpg", ".png"]
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
        self._fileFormat: str = self._formats[0]
        self._currentImage: np.ndarray = np.zeros(shape=(2, 2))
        self._isWriting: bool = True
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
                    dpg.add_text(default_value="format", indent=23)
                    dpg.add_combo(items=self._formats,
                                  default_value=self._fileFormat,
                                  width=self._width - 90,
                                  callback=self.__callbackFileFormatChange)

                dpg.add_checkbox(label="write",
                                 default_value=self._isWriting,
                                 callback=self.__callbackWriteStateChange)

                dpg.add_checkbox(label="overwrite existing",
                                 default_value=self._overwrite,
                                 callback=self.__callbackOverWriteStateChange)

                with dpg.group(horizontal=True, horizontal_spacing=5, indent=50):
                    dpg.add_text(tag=self._nameChangeIntTextTag, default_value="unq int: 1")
                    dpg.add_button(label="R", width=30, height=30, callback=self.__callbackResetNameChanger)

    def update(self):
        if self._outDirPath is None or not self._isWriting:
            return
        data = self._attrImageInput.data
        if data is not None:
            if np.array_equal(data, self._currentImage):
                return
            filename = self._outDirPath.joinpath(self._fileBaseName + "_"
                                                 + str(self._nameChangerInt)
                                                 + self._fileFormat)
            if filename.exists() and not self._overwrite:
                return
            self._currentImage = data.copy()
            self._nameChangerInt += 1
            cv2.imwrite(filename=str(filename.resolve()), img=cv2.cvtColor(self._currentImage, cv2.COLOR_BGR2RGB))
            dpg.set_value(item=self._nameChangeIntTextTag, value=f"unq int: {self._nameChangerInt}")

    def __callbackSetOutDir(self, sender, data):
        self._outDirPath = Path(data["file_path_name"])
        dpg.set_value(item=self._outDirTextInputTag, value=str(self._outDirPath.resolve()))
        self.__callbackResetNameChanger()

    def __callbackWriteStateChange(self, sender, data):
        self._isWriting = data

    def __callbackBaseNameChange(self, sender, data):
        self._fileBaseName = data

    def __callbackOverWriteStateChange(self, sender, data):
        self._overwrite = data

    def __callbackFileFormatChange(self, sender, data):
        self._fileFormat = data

    def __callbackResetNameChanger(self):
        self._nameChangerInt = 1
        dpg.set_value(item=self._nameChangeIntTextTag, value="unq int: 1")
