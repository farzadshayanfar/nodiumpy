from typing import Union

import cv2
import dearpygui.dearpygui as dpg
import numpy as np

from node_editor.connection_objects import NodeAttribute, AttributeType
from node_editor.editor import NodeEditor
from nodes.node import NodeBase


class Node(NodeBase):
    nodeLabel: str = "Mask"

    def __init__(self,
                 tag: int,
                 pos: tuple[int, int],
                 editorHandle: NodeEditor):
        super().__init__(tag=tag, editor=editorHandle)
        self._width: int = self._settings.nodeWidth
        self._currentImage: Union[np.ndarray, None] = None
        self._currentMask: Union[np.ndarray, None] = None

        self._attrImageInput = NodeAttribute(tag=editorHandle.getUniqueTag(),
                                             parentNodeTag=self._tag,
                                             attrType=AttributeType.Image)
        self._attrMaskInput = NodeAttribute(tag=editorHandle.getUniqueTag(),
                                            parentNodeTag=self._tag,
                                            attrType=AttributeType.Image)
        self.inAttrs.extend([self._attrImageInput, self._attrMaskInput])

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
                dpg.add_text(default_value="input image")

            with dpg.node_attribute(tag=self._attrMaskInput.tag,
                                    attribute_type=dpg.mvNode_Attr_Input,
                                    shape=dpg.mvNode_PinShape_QuadFilled):
                dpg.add_text(default_value="mask (binary image)")

            with dpg.node_attribute(tag=self._attrImageOutput.tag,
                                    attribute_type=dpg.mvNode_Attr_Output,
                                    shape=dpg.mvNode_PinShape_Triangle):
                dpg.add_spacer(width=self._width)

    def update(self):
        inputImage = self._attrImageInput.data
        maskImage = self._attrMaskInput.data
        if inputImage is None or maskImage is None:
            return
        if np.array_equal(inputImage, self._currentImage) and np.array_equal(maskImage, self._currentMask):
            return
        self._currentImage = inputImage
        self._currentMask = maskImage
        self.__applyMask()

    def __applyMask(self):
        if self._currentImage is None:
            return
        img = self._currentImage.copy()
        mask = self._currentMask.copy()
        height, width = img.shape[:2]
        mask = cv2.resize(src=mask, dsize=(width, height))
        img[mask == 0] = 0
        self._attrImageOutput.data = img
