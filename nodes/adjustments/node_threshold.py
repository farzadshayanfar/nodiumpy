from typing import Union

import cv2
import dearpygui.dearpygui as dpg
import numpy as np

from node_editor.connection_objects import NodeAttribute, AttributeType
from node_editor.editor import NodeEditor
from nodes.node import NodeBase


class Node(NodeBase):
    nodeLabel: str = "Threshold"
    _modes2FcnMap: dict = {"binary": cv2.THRESH_BINARY,
                           "inverted binary": cv2.THRESH_BINARY_INV,
                           "trunc": cv2.THRESH_TRUNC,
                           "tozero": cv2.THRESH_TOZERO,
                           "inverted tozero": cv2.THRESH_TOZERO_INV,
                           "adaptive mean": cv2.ADAPTIVE_THRESH_MEAN_C,
                           "adaptive gaussian": cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                           "Otsu": cv2.THRESH_OTSU}
    _modes = list(_modes2FcnMap.keys())

    def __init__(self,
                 tag: int,
                 pos: tuple[int, int],
                 editorHandle: NodeEditor):
        super().__init__(tag=tag, editor=editorHandle)
        self._width: int = self._settings.nodeWidth
        self._currentImage: Union[np.ndarray, None] = None
        self._currentGrayImage: Union[np.ndarray, None] = None
        self._currentMode = self._modes[0]
        self._thresholdGroupTag: int = editorHandle.getUniqueTag()
        self._threshold: float = 0.5
        self._adaptiveGroupTag: int = editorHandle.getUniqueTag()
        self._adaptiveBlockSize: int = 11
        self._adaptiveConstant: int = 2

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
                dpg.add_combo(items=self._modes,
                              default_value=self._currentMode,
                              width=self._width,
                              callback=self.__callbackComboChange)
                with dpg.group(tag=self._thresholdGroupTag, horizontal=True, indent=10):
                    dpg.add_text(default_value="threshold")
                    dpg.add_input_float(width=self._width - 100,
                                        default_value=self._threshold,
                                        min_value=0,
                                        min_clamped=True,
                                        max_value=1,
                                        max_clamped=True,
                                        step=0.05,
                                        callback=self.__callbackThresholdChange)

                with dpg.group(tag=self._adaptiveGroupTag, show=False):
                    with dpg.group(horizontal=True, indent=6):
                        dpg.add_text(default_value="block size")
                        dpg.add_input_int(width=self._width - 100,
                                          default_value=self._adaptiveBlockSize,
                                          min_value=3,
                                          min_clamped=True,
                                          max_value=149,
                                          max_clamped=True,
                                          callback=self.__callbackAdaptiveBlockSizeChange)

                    with dpg.group(horizontal=True, indent=6):
                        dpg.add_text(default_value="constant", indent=16)
                        dpg.add_input_int(width=self._width - 100,
                                          default_value=self._adaptiveConstant,
                                          callback=self.__callbackAdaptiveConstantChange)

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
        self._currentGrayImage = cv2.cvtColor(src=data, code=cv2.COLOR_RGBA2GRAY)
        self.__applyThreshold()

    def __applyThreshold(self):
        if self._currentImage is None:
            return
        img = self._currentGrayImage.copy()
        if self._currentMode in ["binary", "inverted binary", "trunc", "tozero", "inverted tozero"]:
            _, img = cv2.threshold(src=img,
                                   thresh=self._threshold,
                                   maxval=1,
                                   type=self._modes2FcnMap[self._currentMode])
        elif self._currentMode in ["adaptive mean", "adaptive gaussian"]:
            img = (img * 255).astype(np.uint8)
            img = cv2.adaptiveThreshold(src=img,
                                        maxValue=255,
                                        adaptiveMethod=self._modes2FcnMap[self._currentMode],
                                        thresholdType=cv2.THRESH_BINARY,
                                        blockSize=self._adaptiveBlockSize,
                                        C=self._adaptiveConstant)
            img = (img / 255).astype(np.float32)
        elif self._currentMode == "Otsu":
            img = (img * 255).astype(np.uint8)
            _, img = cv2.threshold(src=img,
                                   thresh=self._threshold,
                                   maxval=255,
                                   type=cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            img = (img / 255).astype(np.float32)
        self._attrImageOutput.data = cv2.cvtColor(src=img, code=cv2.COLOR_GRAY2RGBA)

    def __callbackComboChange(self, _, data):
        self._currentMode = data
        if data in ["adaptive mean", "adaptive gaussian"]:
            dpg.hide_item(item=self._thresholdGroupTag)
            dpg.show_item(item=self._adaptiveGroupTag)
        elif data == "Otsu":
            dpg.hide_item(item=self._thresholdGroupTag)
            dpg.hide_item(item=self._adaptiveGroupTag)
        else:
            dpg.show_item(item=self._thresholdGroupTag)
            dpg.hide_item(item=self._adaptiveGroupTag)
        self.__applyThreshold()

    def __callbackThresholdChange(self, _, data):
        self._threshold = data
        self.__applyThreshold()

    def __callbackAdaptiveBlockSizeChange(self, sender, data):
        if data > self._adaptiveBlockSize:
            self._adaptiveBlockSize = data if data % 2 != 0 else data + 1
        else:
            self._adaptiveBlockSize = data if data % 2 != 0 else data - 1
        dpg.set_value(item=sender, value=self._adaptiveBlockSize)
        self.__applyThreshold()

    def __callbackAdaptiveConstantChange(self, sender, data):
        self._adaptiveConstant = data
        self.__applyThreshold()
