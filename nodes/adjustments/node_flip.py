from typing import Union

import cv2
import dearpygui.dearpygui as dpg
import numpy as np

from node_editor.connection_objects import NodeAttribute, AttributeType
from node_editor.editor import NodeEditor
from nodes.node import NodeBase


class Node(NodeBase):
    nodeLabel = "Flip"

    def __init__(self,
                 tag: int,
                 pos: tuple[int, int],
                 editorHandle: NodeEditor):
        super().__init__(tag=tag, editor=editorHandle)
        self._width: int = self._settings.nodeWidth
        self._currentImage: Union[np.ndarray, None] = None
        self._verticalFlipCheckBoxTag: int = editorHandle.getUniqueTag()
        self._verticalFlip: bool = False
        self._horizontalFlipCheckBoxTag: int = editorHandle.getUniqueTag()
        self._horizontalFlip: bool = True

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
            dpg.add_node_attribute(tag=self._attrImageInput.tag,
                                   attribute_type=dpg.mvNode_Attr_Input,
                                   shape=dpg.mvNode_PinShape_QuadFilled)

            with dpg.node_attribute(tag=editorHandle.getUniqueTag(),
                                    attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_checkbox(tag=self._verticalFlipCheckBoxTag,
                                 label="vertical",
                                 default_value=self._verticalFlip,
                                 callback=self.__callbackVerticalFlipChange)
                dpg.add_checkbox(tag=self._horizontalFlipCheckBoxTag,
                                 label="horizontal",
                                 default_value=self._horizontalFlip,
                                 callback=self.__callbackHorizontalFlipChange)
                dpg.add_spacer(width=self._width)

            dpg.add_node_attribute(tag=self._attrImageOutput.tag,
                                   attribute_type=dpg.mvNode_Attr_Output,
                                   shape=dpg.mvNode_PinShape_Triangle)

    def update(self):
        data = self._attrImageInput.data
        if data is None:
            self._currentImage = None
            return
        if np.array_equal(data, self._currentImage):
            return
        self._currentImage = data

        self.__flip()

    def __flip(self):
        if self._currentImage is None:
            return
        img = self._currentImage.copy()
        if self._verticalFlip:
            img = cv2.flip(src=img, flipCode=0)
        if self._horizontalFlip:
            img = cv2.flip(src=img, flipCode=1)
        self._attrImageOutput.data = img

    def __callbackVerticalFlipChange(self, sender, data):
        self._verticalFlip = data
        self.__flip()

    def __callbackHorizontalFlipChange(self, sender, data):
        self._horizontalFlip = data
        self.__flip()
