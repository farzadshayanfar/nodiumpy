from typing import Union

import cv2
import dearpygui.dearpygui as dpg
import numpy as np

from node_editor.connection_objects import NodeAttribute, AttributeType
from node_editor.editor import NodeEditor
from nodes.node import NodeBase


class Node(NodeBase):
    nodeLabel = "Resize"

    _modes = dict(nearest=cv2.INTER_NEAREST,
                  linear=cv2.INTER_LINEAR,
                  area=cv2.INTER_AREA,
                  cubic=cv2.INTER_CUBIC,
                  LANCZOS4=cv2.INTER_LANCZOS4)

    def __init__(self,
                 tag: int,
                 pos: tuple[int, int],
                 editorHandle: NodeEditor):
        super().__init__(tag=tag, editor=editorHandle)
        self._width: int = self._settings.nodeWidth
        self._currentImage: Union[np.ndarray, None] = None
        self._currentMode = list(self._modes.keys())[0]

        self._desiredWidthInputTag: int = editorHandle.getUniqueTag()
        self._desiredHeightInputTag: int = editorHandle.getUniqueTag()
        self._desiredWidth: int = 1280
        self._desiredHeight: int = 720

        self._inputImageSizeLabelTag: int = editorHandle.getUniqueTag()

        self._attrImageInput = NodeAttribute(tag=editorHandle.getUniqueTag(),
                                             parentNodeTag=self._tag,
                                             attrType=AttributeType.Image)
        self.inAttrs.append(self._attrImageInput)

        self._attrImageOutput = NodeAttribute(tag=editorHandle.getUniqueTag(),
                                              parentNodeTag=self._tag,
                                              attrType=AttributeType.Image)
        self.outAttrs.append(self._attrImageOutput)

        with dpg.node(tag=self._tag,
                      parent=editorHandle.tag,
                      label=self.nodeLabel,
                      pos=pos):
            with dpg.node_attribute(tag=self._attrImageInput.tag,
                                    attribute_type=dpg.mvNode_Attr_Input,
                                    shape=dpg.mvNode_PinShape_QuadFilled):
                dpg.add_text(tag=self._inputImageSizeLabelTag)

            with dpg.node_attribute(tag=editorHandle.getUniqueTag(),
                                    attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_combo(items=list(self._modes.keys()),
                              default_value=self._currentMode,
                              width=self._width,
                              callback=self.__callbackComboChange)
                with dpg.group(indent=20):
                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="width", indent=8)
                        dpg.add_input_int(tag=self._desiredWidthInputTag,
                                          width=self._width - 100,
                                          default_value=self._desiredWidth,
                                          callback=self.__callbackDesiredWidthChange)

                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="height")
                        dpg.add_input_int(tag=self._desiredHeightInputTag,
                                          width=self._width - 100,
                                          default_value=self._desiredHeight,
                                          callback=self.__callbackDesiredHeightChange)

            dpg.add_node_attribute(tag=self._attrImageOutput.tag,
                                   attribute_type=dpg.mvNode_Attr_Output,
                                   shape=dpg.mvNode_PinShape_Triangle)

    def update(self):
        data = self._attrImageInput.data
        if data is None:
            return
        if np.array_equal(data, self._currentImage):
            return
        dpg.set_value(item=self._inputImageSizeLabelTag, value=data.shape[:2])
        self._currentImage = data

        self.__resize()

    def __resize(self):
        if self._currentImage is None:
            return
        img = self._currentImage.copy()
        img = cv2.resize(src=img,
                         dsize=(self._desiredWidth, self._desiredHeight),
                         interpolation=self._modes[self._currentMode])

        self._attrImageOutput.data = img

    def __callbackComboChange(self, _, data):
        self._currentMode = data
        self.__resize()

    def __callbackDesiredWidthChange(self, _, data):
        self._desiredWidth = data
        self.__resize()

    def __callbackDesiredHeightChange(self, _, data):
        self._desiredHeight = data
        self.__resize()
