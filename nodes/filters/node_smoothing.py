from typing import Union

import cv2
import dearpygui.dearpygui as dpg
import numpy as np

from node_editor.connection_objects import NodeAttribute, AttributeType
from node_editor.editor import NodeEditor
from nodes.node import NodeBase


class Node(NodeBase):
    nodeLabel = "Smoothing / Sharpening"
    _filters = ["gaussian", "average", "median", "bilateral", "2d convolution"]

    def __init__(self,
                 tag: int,
                 pos: tuple[int, int],
                 editorHandle: NodeEditor):
        super().__init__(tag=tag, editor=editorHandle)
        self._width: int = self._settings.nodeWidth
        self._currentFilter = self._filters[0]
        self._currentImage: Union[np.ndarray, None] = None

        self._gaussianGroupTag = editorHandle.getUniqueTag()
        self._gaussianKernelSizeInputTag = editorHandle.getUniqueTag()
        self._gaussianKernelSize: tuple[int, int] = (3, 3)
        self._gaussianKernelSizeRange: tuple[int, int] = (1, 199)
        self._gaussianSigmaXYInputTag = editorHandle.getUniqueTag()
        self._gaussianSigmaXY: tuple[float, float] = (0, 0)
        self._gaussianSigmaRange: tuple[float, float] = (0, 1)

        self._averageGroupTag: int = editorHandle.getUniqueTag()
        self._averageKernelSizeInputTag: int = editorHandle.getUniqueTag()
        self._averageKernelSize: tuple[int, int] = (5, 5)
        self._averageKernelSizeRange: tuple[int, int] = (3, 40)
        self._averageAnchorInputTag: int = editorHandle.getUniqueTag()
        self._averageAnchor: tuple[int, int] = (-1, -1)
        self._averageAnchorRange: tuple[int, int] = (-10, 10)

        self._medianGroupTag: int = editorHandle.getUniqueTag()
        self._medianKernelSizeInputTag: int = editorHandle.getUniqueTag()
        self._medianKernelSize: int = 5
        self._medianKernelSizeRange: tuple[int, int] = (3, 99)

        self._bilateralGroupTag: int = editorHandle.getUniqueTag()
        self._bilateralDiameterInputTag: int = editorHandle.getUniqueTag()
        self._bilateralDiameterRange: tuple[int, int] = (0, 150)
        self._bilateralDiameter: int = 9
        self._bilateralColorSigmaInputTag: int = editorHandle.getUniqueTag()
        self._bilateralColorSigmaRange: tuple[float, float] = (0, 150)
        self._bilateralColorSigma: float = 75
        self._bilateralSpaceSigmaInputTag: int = editorHandle.getUniqueTag()
        self._bilateralSpaceSigmaRange: tuple[float, float] = (0, 150)
        self._bilateralSpaceSigma: float = 75

        self._convGroupTag = editorHandle.getUniqueTag()

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
                dpg.add_combo(items=self._filters,
                              default_value=self._currentFilter,
                              width=self._width,
                              callback=self.__callbackComboChange)

                with dpg.group(tag=self._gaussianGroupTag, indent=10):
                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="ks", indent=24)
                        dpg.add_drag_intx(tag=self._gaussianKernelSizeInputTag,
                                          size=2,
                                          width=self._width - 85,
                                          min_value=self._gaussianKernelSizeRange[0],
                                          max_value=self._gaussianKernelSizeRange[1],
                                          default_value=self._gaussianKernelSize,
                                          speed=2,
                                          callback=self.__gaussianKernelSizeChange)

                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="sigma")
                        dpg.add_drag_floatx(tag=self._gaussianSigmaXYInputTag,
                                            size=2,
                                            width=self._width - 85,
                                            min_value=self._gaussianSigmaRange[0],
                                            max_value=self._gaussianSigmaRange[1],
                                            default_value=self._gaussianSigmaXY,
                                            speed=0.01,
                                            callback=self.__callbackGaussianSigmaChange)

                with dpg.group(tag=self._averageGroupTag, indent=10, show=False):
                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="ks", indent=32)
                        dpg.add_drag_intx(tag=self._averageKernelSizeInputTag,
                                          size=2,
                                          width=self._width - 85,
                                          min_value=self._averageKernelSizeRange[0],
                                          max_value=self._averageKernelSizeRange[1],
                                          default_value=self._averageKernelSize,
                                          no_input=True,
                                          callback=self.__callbackAverageKernelSizeChange)

                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="anchor")
                        dpg.add_drag_intx(tag=self._averageAnchorInputTag,
                                          size=2,
                                          width=self._width - 85,
                                          min_value=self._averageAnchorRange[0],
                                          max_value=self._averageAnchorRange[1],
                                          default_value=self._averageAnchor,
                                          no_input=True,
                                          callback=self.__callbackAverageAnchorChange)

                with dpg.group(tag=self._medianGroupTag, indent=30, show=False):
                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="ks")
                        dpg.add_drag_int(tag=self._medianKernelSizeInputTag,
                                         width=self._width - 85,
                                         min_value=self._medianKernelSizeRange[0],
                                         max_value=self._medianKernelSizeRange[1],
                                         default_value=self._medianKernelSize,
                                         speed=2,
                                         no_input=True,
                                         callback=self.__callbackMedianKernelSizeChange)

                with dpg.group(tag=self._bilateralGroupTag, indent=4, show=False):
                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="diameter")
                        dpg.add_drag_int(tag=self._bilateralDiameterInputTag,
                                         width=self._width - 85,
                                         min_value=self._bilateralDiameterRange[0],
                                         max_value=self._bilateralDiameterRange[1],
                                         default_value=self._bilateralDiameter,
                                         callback=self.__callbackBilateralDiameterChange)

                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="c sigma", indent=8)
                        dpg.add_drag_float(tag=self._bilateralColorSigmaInputTag,
                                           width=self._width - 85,
                                           min_value=self._bilateralColorSigmaRange[0],
                                           max_value=self._bilateralColorSigmaRange[1],
                                           default_value=self._bilateralColorSigma,
                                           callback=self.__callbackBilateralColorSigmaChange)

                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="s sigma", indent=8)
                        dpg.add_drag_float(tag=self._bilateralSpaceSigmaInputTag,
                                           width=self._width - 85,
                                           min_value=self._bilateralSpaceSigmaRange[0],
                                           max_value=self._bilateralSpaceSigmaRange[1],
                                           default_value=self._bilateralSpaceSigma,
                                           callback=self.__callbackBilateralSpaceSigmaChange)

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
        self.__applyFilter()

    def __callbackComboChange(self, sender, data):
        self._currentFilter = data
        if data == "gaussian":
            dpg.show_item(item=self._gaussianGroupTag)
            dpg.hide_item(item=self._averageGroupTag)
            dpg.hide_item(item=self._medianGroupTag)
            dpg.hide_item(item=self._bilateralGroupTag)
        elif data == "average":
            dpg.hide_item(item=self._gaussianGroupTag)
            dpg.show_item(item=self._averageGroupTag)
            dpg.hide_item(item=self._medianGroupTag)
            dpg.hide_item(item=self._bilateralGroupTag)
        elif data == "median":
            dpg.hide_item(item=self._gaussianGroupTag)
            dpg.hide_item(item=self._averageGroupTag)
            dpg.show_item(item=self._medianGroupTag)
            dpg.hide_item(item=self._bilateralGroupTag)
        elif data == "bilateral":
            dpg.hide_item(item=self._gaussianGroupTag)
            dpg.hide_item(item=self._averageGroupTag)
            dpg.hide_item(item=self._medianGroupTag)
            dpg.show_item(item=self._bilateralGroupTag)
        self.__applyFilter()

    def __applyFilter(self):
        if self._currentImage is None:
            return
        img = self._currentImage.copy()
        if self._currentFilter == "gaussian":
            img = cv2.GaussianBlur(src=img,
                                   ksize=self._gaussianKernelSize,
                                   sigmaX=self._gaussianSigmaXY[0],
                                   sigmaY=self._gaussianSigmaXY[1])

        elif self._currentFilter == "average":
            img = cv2.blur(src=img, ksize=self._averageKernelSize, anchor=self._averageAnchor)

        elif self._currentFilter == "median":
            img = cv2.medianBlur(src=img, ksize=self._medianKernelSize)

        elif self._currentFilter == "bilateral":
            img = cv2.bilateralFilter(src=img,
                                      d=self._bilateralDiameter,
                                      sigmaColor=self._bilateralColorSigma,
                                      sigmaSpace=self._bilateralSpaceSigma)
        self._attrImageOutput.data = img

    def __gaussianKernelSizeChange(self, _, data):
        self._gaussianKernelSize = data[:2]
        self.__applyFilter()

    def __callbackGaussianSigmaChange(self, _, data):
        self._gaussianSigmaXY = data
        self.__applyFilter()

    def __callbackAverageKernelSizeChange(self, _, data):
        self._averageKernelSize = data[:2]
        self.__applyFilter()

    def __callbackAverageAnchorChange(self, _, data):
        self._averageAnchor = data[:2]
        self.__applyFilter()

    def __callbackMedianKernelSizeChange(self, _, data):
        self._medianKernelSize = data
        self.__applyFilter()

    def __callbackBilateralDiameterChange(self, _, data):
        self._bilateralDiameter = data
        self.__applyFilter()

    def __callbackBilateralColorSigmaChange(self, _, data):
        self._bilateralColorSigma = data
        self.__applyFilter()

    def __callbackBilateralSpaceSigmaChange(self, _, data):
        self._bilateralSpaceSigma = data
        self.__applyFilter()
