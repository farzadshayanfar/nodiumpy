from pathlib import Path
from typing import Union

import cv2
import dearpygui.dearpygui as dpg
import numpy as np

from node_editor.connection_objects import NodeAttribute, AttributeType
from node_editor.editor import NodeEditor
from nodes.node import NodeBase


class Node(NodeBase):
    nodeLabel = "Image Folder"
    _filePatterns = ["*.png", "*.PNG", "*.jpg", "*.jpeg", "*.JPEG"]

    def __init__(self,
                 tag: int,
                 pos: tuple[int, int],
                 editorHandle: NodeEditor):
        super().__init__(tag=tag, editor=editorHandle)
        self._width: int = self._settings.nodeWidth
        self._searchSubDirs: bool = False
        self._currentImageIndex: int = 0
        self._currentPath: Union[Path, None] = None
        self._pathList: list[Path] = list()
        self._intDragTag = editorHandle.getUniqueTag()
        self._frameSizeTextTag: int = editorHandle.getUniqueTag()
        self._fileCount: int = 0
        self._iterate: bool = False
        self._loop: bool = False

        self._attrImageOutput = NodeAttribute(tag=editorHandle.getUniqueTag(),
                                              parentNodeTag=self._tag,
                                              attrType=AttributeType.Image)

        self.outAttrs.append(self._attrImageOutput)

        with dpg.node(tag=self._tag,
                      parent=editorHandle.tag,
                      label=self.nodeLabel,
                      pos=pos):
            folderDialogTag = editorHandle.getUniqueTag()
            editorHandle.createFolderSelectionDialog(tag=folderDialogTag, callback=self.__callbackGetImages)
            with dpg.node_attribute(tag=editorHandle.getUniqueTag(),
                                    attribute_type=dpg.mvNode_Attr_Static):
                with dpg.group():
                    dpg.add_button(label='select folder',
                                   width=self._width,
                                   callback=lambda: dpg.show_item(item=folderDialogTag))
                    dpg.add_checkbox(label="subdirs", callback=self.__callbackSearchSubDirs)

            with dpg.node_attribute(tag=editorHandle.getUniqueTag(),
                                    attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_drag_int(tag=self._intDragTag,
                                 width=self._width,
                                 min_value=0,
                                 clamped=True,
                                 format="0 / 0",
                                 callback=self.__callbackCurrentImageChange)
                with dpg.group(horizontal=True):
                    dpg.add_checkbox(label="iterate",
                                     default_value=self._iterate,
                                     callback=self.__callbackIterate)
                    dpg.add_checkbox(label="loop",
                                     default_value=self._loop,
                                     callback=self.__callbackLoop)

            with dpg.node_attribute(tag=self._attrImageOutput.tag,
                                    attribute_type=dpg.mvNode_Attr_Output,
                                    shape=dpg.mvNode_PinShape_Triangle):
                dpg.add_text(tag=self._frameSizeTextTag,
                             wrap=self._width,
                             indent=self._width - 100)

    def update(self):
        if self._iterate:
            if self._loop and self._currentImageIndex + 1 == self._fileCount:
                self._currentImageIndex = -1
            if self._fileCount == 0 or self._currentImageIndex + 1 == self._fileCount:
                return
            self._currentImageIndex += 1
            dpg.set_value(item=self._intDragTag, value=self._currentImageIndex)
            self.__loadCurrentIndexImage()

    def __callbackGetImages(self, sender: str, data: dict):
        # data is a dictionary with some keys being "file_path_name", \
        # "file_name", "current_path", "current_filter"
        self._currentPath = Path(data['file_path_name'])
        self._pathList.clear()
        if self._searchSubDirs:
            for pattern in self._filePatterns:
                self._pathList.extend(list(self._currentPath.rglob(pattern=pattern)))
        else:
            for pattern in self._filePatterns:
                self._pathList.extend(list(self._currentPath.glob(pattern=pattern)))

        if not self._pathList:
            dpg.configure_item(item=self._intDragTag,
                               format="0 / 0")
            return

        self._currentImageIndex = 0
        dpg.configure_item(item=self._intDragTag,
                           format=f"index %f / {len(self._pathList) - 1}",
                           default_value=0,
                           max_value=len(self._pathList) - 1)

        self._fileCount = len(self._pathList)
        self.__loadCurrentIndexImage()

    def __loadCurrentIndexImage(self):
        img = cv2.imread(filename=str(self._pathList[self._currentImageIndex].resolve()), flags=cv2.IMREAD_UNCHANGED)
        if img is None:
            print(f"can't properly open this file:\n{self._pathList[self._currentImageIndex].resolve()}")
            return
        if img.ndim == 3 and img.shape[2] == 4:
            img = cv2.cvtColor(src=img, code=cv2.COLOR_BGRA2RGBA)
        else:
            img = cv2.cvtColor(src=img, code=cv2.COLOR_BGR2RGBA)
        img = img.astype(np.float32) / 255
        self._attrImageOutput.data = img
        dpg.set_value(item=self._frameSizeTextTag, value=img.shape[:2])

    def __callbackSearchSubDirs(self, _, data):
        self._searchSubDirs = data
        if self._currentPath is not None:
            self.__callbackGetImages(sender=str(), data={"file_path_name": str(self._currentPath.resolve())})

    def __callbackIterate(self, _, data):
        self._iterate = data

    def __callbackLoop(self, _, data):
        self._loop = data

    def __callbackCurrentImageChange(self, _, data):
        self._currentImageIndex = data
        self.__loadCurrentIndexImage()
