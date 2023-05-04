from typing import Union

import cv2
import dearpygui.dearpygui as dpg
import numpy as np

from node_editor.connection_objects import NodeAttribute, AttributeType
from node_editor.editor import NodeEditor
from nodes.node import NodeBase


class Node(NodeBase):
    nodeLabel = "Image"

    def __init__(self,
                 tag: int,
                 pos: tuple[int, int],
                 editorHandle: NodeEditor):
        super().__init__(tag=tag, editor=editorHandle)
        self._width: int = self._settings.nodeWidth
        self._frameSizeTextTag: int = editorHandle.getUniqueTag()

        self._currentImage: Union[np.ndarray, None] = None

        self._attrImageOutput = NodeAttribute(tag=editorHandle.getUniqueTag(),
                                              parentNodeTag=self._tag,
                                              attrType=AttributeType.Image)
        self.outAttrs.append(self._attrImageOutput)

        with dpg.node(tag=self._tag,
                      parent=editorHandle.tag,
                      label=self.nodeLabel,
                      pos=pos):
            fileDialogTag = editorHandle.getUniqueTag()
            editorHandle.createImageFileSelectionDialog(tag=fileDialogTag, callback=self.__callbackOpenFile)
            with dpg.node_attribute(tag=editorHandle.getUniqueTag(),
                                    attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_button(label='select image',
                               width=self._width,
                               callback=lambda: dpg.show_item(item=fileDialogTag))

            with dpg.node_attribute(tag=self._attrImageOutput.tag,
                                    attribute_type=dpg.mvNode_Attr_Output,
                                    shape=dpg.mvNode_PinShape_Triangle):
                dpg.add_text(tag=self._frameSizeTextTag,
                             indent=self._width - 100)

    def update(self):
        return None

    def __callbackOpenFile(self, sender: str, data: dict):
        # data is a dictionary with some keys being "file_path_name", \
        # "file_name", "current_path", "current_filter"
        img = cv2.imread(filename=data['file_path_name'], flags=cv2.IMREAD_UNCHANGED)
        if img.ndim == 3 and img.shape[2] == 4:
            img = cv2.cvtColor(src=img, code=cv2.COLOR_BGRA2RGBA)
        else:
            img = cv2.cvtColor(src=img, code=cv2.COLOR_BGR2RGBA)
        img = img.astype(np.float32) / 255
        self._attrImageOutput.data = img
        dpg.set_value(item=self._frameSizeTextTag, value=img.shape[:2])
