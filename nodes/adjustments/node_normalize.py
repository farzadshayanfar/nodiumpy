from typing import Union

import dearpygui.dearpygui as dpg
import numpy as np

from node_editor.connection_objects import NodeAttribute, AttributeType
from node_editor.editor import NodeEditor
from nodes.node import NodeBase


class Node(NodeBase):
    nodeLabel = "Normalize"
    _defaultMean: list[float, float, float] = [0.485, 0.456, 0.406]
    _defaultStd: list[float, float, float] = [0.229, 0.224, 0.225]

    def __init__(self,
                 tag: int,
                 pos: tuple[int, int],
                 editorHandle: NodeEditor):
        super().__init__(tag=tag, editor=editorHandle)
        self._width: int = self._settings.nodeWidth
        self._currentImage: Union[np.ndarray, None] = None
        self._meanInputTag: int = editorHandle.getUniqueTag()
        self._stdInputTag: int = editorHandle.getUniqueTag()
        self._mean: list[float, float, float] = self._defaultMean
        self._std: list[float, float, float] = self._defaultStd

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
                with dpg.group(horizontal=True):
                    dpg.add_text(default_value="mean")
                    dpg.add_drag_floatx(tag=self._meanInputTag,
                                        size=3,
                                        default_value=self._mean,
                                        format="%.3f",
                                        width=self._width - 41,
                                        min_value=0,
                                        clamped=True,
                                        speed=0.005,
                                        callback=self.__callbackMeanChange)
                with dpg.group(horizontal=True):
                    dpg.add_text(default_value="std", indent=7)
                    dpg.add_drag_floatx(tag=self._stdInputTag,
                                        size=3,
                                        default_value=self._std,
                                        format="%.3f",
                                        width=self._width - 41,
                                        min_value=0,
                                        clamped=True,
                                        speed=0.005,
                                        callback=self.__callbackStdChange)
                dpg.add_button(label="R",
                               width=32,
                               height=32,
                               indent=self._width // 2 - 16,
                               callback=self.__callbackReset)
            dpg.add_node_attribute(tag=self._attrImageOutput.tag,
                                   attribute_type=dpg.mvNode_Attr_Output,
                                   shape=dpg.mvNode_PinShape_Triangle)

    def update(self):
        data = self._attrImageInput.data
        if data is None:
            return
        if np.array_equal(data, self._currentImage):
            return
        self._currentImage = data

        self.__normalize()

    def __normalize(self):
        if self._currentImage is None:
            return
        img = self._currentImage.copy()
        mean = np.array(self._mean)
        std = np.array(self._std)
        img[:, :, :3] = (img[:, :, :3] - mean) / std
        self._attrImageOutput.data = img

    def __callbackMeanChange(self, sender, data):
        self._mean = data[:3]
        self.__normalize()

    def __callbackStdChange(self, sender, data):
        self._std = data[:3]
        self.__normalize()

    def __callbackReset(self):
        self._mean = self._defaultMean
        self._std = self._defaultStd
        dpg.set_value(item=self._meanInputTag, value=self._mean)
        dpg.set_value(item=self._stdInputTag, value=self._std)
        self.__normalize()
