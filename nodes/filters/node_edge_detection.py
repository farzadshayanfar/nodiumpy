#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Union

import cv2
import dearpygui.dearpygui as dpg
import numpy as np

from node_editor.connection_objects import NodeAttribute, AttributeType
from node_editor.editor import NodeEditor
from nodes.filters.algorithms.edge_detection import pst, page
from nodes.node import NodeBase


class Node(NodeBase):
    nodeLabel = "Edge Detection"
    _filters = ["Canny", "Sobel", "Laplacian", "PST", "PAGE"]

    def __init__(self,
                 tag: int,
                 pos: tuple[int, int],
                 editorHandle: NodeEditor):
        super().__init__(tag=tag, editor=editorHandle)
        self._width: int = self._settings.nodeWidth
        self._currentFilter: str = self._filters[0]
        self._currentImage: Union[np.ndarray, None] = None

        self._cannyGroupTag: int = editorHandle.getUniqueTag()
        self._cannyMinTag: int = editorHandle.getUniqueTag()
        self._cannyMaxTag: int = editorHandle.getUniqueTag()
        self._cannyThresholdRange: tuple[int, int] = (0, 500)
        self._cannyMax: int = 200
        self._cannyMin: int = 100
        self._cannyApertureSizeRange: tuple[int, int] = (3, 7)
        self._cannyApertureSize: int = 3
        self._cannyL2Grad: bool = False

        self._sobelGroupTag: int = editorHandle.getUniqueTag()
        self._sobelDxTag: int = editorHandle.getUniqueTag()
        self._sobelDyTag: int = editorHandle.getUniqueTag()
        self._sobelKsTag: int = editorHandle.getUniqueTag()
        self._sobelDxRange: tuple[int, int] = (0, 10)
        self._sobelDx: int = 1
        self._sobelDyRange: tuple[int, int] = (0, 10)
        self._sobelDy: int = 0
        self._sobelKsRange: tuple[int, int] = (1, 49)
        self._sobelKs: int = 5

        self._pstGroupTag: int = editorHandle.getUniqueTag()
        self._pstPhaseStrengthRange: tuple[float, float] = (0, 1)
        self._pstPhaseStrength: float = 0.4
        self._pstWarpStrengthRange: tuple[float, float] = (0, 100)
        self._pstWarpStrength: float = 20
        self._pstLPFSigmaRange: tuple[float, float] = (0, 1)
        self._pstLPFSigma: float = 0.1
        self._pstThresholdRange: tuple[float, float] = (0, 1)
        self._pstMinThreshold: float = 0.1
        self._pstMaxThreshold: float = 0.8
        self._pstUseMorph: bool = True

        self._pageGroupTag: int = editorHandle.getUniqueTag()
        self._pageDirectionBinsRange: tuple[int, int] = (1, 100)
        self._pageDirectionBins: int = 10
        self._pageGenericRange: tuple[float, float] = (0, 1)
        self._pageMu1: float = 0
        self._pageMu2: float = 0.35
        self._pageSigma1: float = 0.05
        self._pageSigma2: float = 0.8
        self._pagePhaseStrength1: float = 0.8
        self._pagePhaseStrength2: float = 0.8
        self._pageLPFSigma: float = 0.1
        self._pageMinThreshold: float = 0
        self._pageMaxThreshold: float = 0.9
        self._pageUseMorph: bool = True

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
                              default_value=self._filters[0],
                              width=self._width,
                              callback=self.__callbackComboChange)

                with dpg.group(tag=self._cannyGroupTag, indent=25):
                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="max")
                        dpg.add_drag_int(tag=self._cannyMaxTag,
                                         default_value=self._cannyMax,
                                         width=self._width - 85,
                                         callback=self.__callbackCannyMaxChange,
                                         min_value=self._cannyThresholdRange[0],
                                         max_value=self._cannyThresholdRange[1],
                                         no_input=True)

                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="min")
                        dpg.add_drag_int(tag=self._cannyMinTag,
                                         default_value=self._cannyMin,
                                         width=self._width - 85,
                                         callback=self.__callbackCannyMinChange,
                                         min_value=self._cannyThresholdRange[0],
                                         max_value=self._cannyThresholdRange[1],
                                         no_input=True)

                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="aperture")
                        dpg.add_drag_int(tag=editorHandle.getUniqueTag(),
                                         default_value=self._cannyApertureSize,
                                         width=self._width - 125,
                                         callback=self.__callbackCannyApertureSizeChange,
                                         min_value=self._cannyApertureSizeRange[0],
                                         max_value=self._cannyApertureSizeRange[1],
                                         no_input=True,
                                         speed=2)

                    dpg.add_checkbox(tag=editorHandle.getUniqueTag(),
                                     label="L2 gradient",
                                     default_value=self._cannyL2Grad,
                                     callback=self.__callbackCannyL2GradChange)

                with dpg.group(tag=self._sobelGroupTag, indent=25, show=False):
                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="dx")
                        dpg.add_drag_int(tag=self._sobelDxTag,
                                         default_value=self._sobelDx,
                                         width=self._width - 85,
                                         callback=self.__callbackSobelDxChange,
                                         min_value=self._sobelDxRange[0],
                                         max_value=self._sobelDxRange[1],
                                         no_input=True)

                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="dy")
                        dpg.add_drag_int(tag=self._sobelDyTag,
                                         default_value=self._sobelDy,
                                         width=self._width - 85,
                                         callback=self.__callbackSobelDyChange,
                                         min_value=self._sobelDyRange[0],
                                         max_value=self._sobelDyRange[1],
                                         no_input=True)

                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="ks")
                        dpg.add_drag_int(tag=self._sobelKsTag,
                                         default_value=self._sobelKs,
                                         width=self._width - 85,
                                         callback=self.__callbackSobelKsChange,
                                         min_value=self._sobelKsRange[0],
                                         max_value=self._sobelKsRange[1],
                                         no_input=True,
                                         speed=2)

                with dpg.group(tag=self._pstGroupTag, indent=25, show=False):
                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="ps", indent=8)
                        dpg.add_drag_float(tag=editorHandle.getUniqueTag(),
                                           default_value=self._pstPhaseStrength,
                                           width=self._width - 85,
                                           callback=self.__callbackPSTPhaseStrengthChange,
                                           min_value=self._pstPhaseStrengthRange[0],
                                           max_value=self._pstPhaseStrengthRange[1],
                                           no_input=True,
                                           speed=0.01)

                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="ws", indent=8)
                        dpg.add_drag_float(tag=editorHandle.getUniqueTag(),
                                           default_value=self._pstWarpStrength,
                                           width=self._width - 85,
                                           callback=self.__callbackPSTWarpStrengthChange,
                                           min_value=self._pstWarpStrengthRange[0],
                                           max_value=self._pstWarpStrengthRange[1],
                                           no_input=True,
                                           speed=0.1)

                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="max")
                        dpg.add_drag_float(tag=editorHandle.getUniqueTag(),
                                           default_value=self._pstMaxThreshold,
                                           width=self._width - 85,
                                           callback=self.__callbackPSTMaxThresholdChange,
                                           min_value=self._pstThresholdRange[0],
                                           max_value=self._pstThresholdRange[1],
                                           no_input=True,
                                           speed=0.01)

                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="min")
                        dpg.add_drag_float(tag=editorHandle.getUniqueTag(),
                                           default_value=self._pstMinThreshold,
                                           width=self._width - 85,
                                           callback=self.__callbackPSTMinThresholdChange,
                                           min_value=self._pstThresholdRange[0],
                                           max_value=self._pstThresholdRange[1],
                                           speed=0.01)

                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="lpf std")
                        dpg.add_drag_float(tag=editorHandle.getUniqueTag(),
                                           default_value=self._pstLPFSigma,
                                           width=self._width - 117,
                                           callback=self.__callbackPST_LPF_SigmaChange,
                                           min_value=self._pstLPFSigmaRange[0],
                                           max_value=self._pstLPFSigmaRange[1],
                                           no_input=True,
                                           speed=0.01)

                    dpg.add_checkbox(label="use morph",
                                     default_value=self._pstUseMorph,
                                     callback=self.__callbackPSTUseMorphChange)

                with dpg.group(tag=self._pageGroupTag, indent=35, show=False):
                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="bins")
                        dpg.add_drag_int(default_value=self._pageDirectionBins,
                                         min_value=self._pageDirectionBinsRange[0],
                                         max_value=self._pageDirectionBinsRange[1],
                                         width=self._width - 118,
                                         callback=self.__callbackPageDirectionBinsChange)

                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="mu1")
                        dpg.add_drag_float(default_value=self._pageMu1,
                                           min_value=self._pageGenericRange[0],
                                           max_value=self._pageGenericRange[1],
                                           width=self._width - 110,
                                           speed=0.01,
                                           callback=self.__callbackPageMu1Change)

                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="mu2")
                        dpg.add_drag_float(default_value=self._pageMu2,
                                           min_value=self._pageGenericRange[0],
                                           max_value=self._pageGenericRange[1],
                                           width=self._width - 110,
                                           speed=0.01,
                                           callback=self.__callbackPageMu2Change)

                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="sigma1")
                        dpg.add_drag_float(default_value=self._pageSigma1,
                                           min_value=self._pageGenericRange[0],
                                           max_value=self._pageGenericRange[1],
                                           width=self._width - 134,
                                           speed=0.01,
                                           callback=self.__callbackPageSigma1Change)

                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="sigma2")
                        dpg.add_drag_float(default_value=self._pageSigma2,
                                           min_value=self._pageGenericRange[0],
                                           max_value=self._pageGenericRange[1],
                                           width=self._width - 134,
                                           speed=0.01,
                                           callback=self.__callbackPageSigma2Change)

                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="ps1")
                        dpg.add_drag_float(default_value=self._pagePhaseStrength1,
                                           min_value=self._pageGenericRange[0],
                                           max_value=self._pageGenericRange[1],
                                           width=self._width - 110,
                                           speed=0.01,
                                           callback=self.__callbackPagePhaseStrength1Change)

                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="ps2")
                        dpg.add_drag_float(default_value=self._pagePhaseStrength2,
                                           min_value=self._pageGenericRange[0],
                                           max_value=self._pageGenericRange[1],
                                           width=self._width - 110,
                                           speed=0.01,
                                           callback=self.__callbackPagePhaseStrength2Change)

                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="lpf std")
                        dpg.add_drag_float(default_value=self._pageLPFSigma,
                                           min_value=self._pageGenericRange[0],
                                           max_value=self._pageGenericRange[1],
                                           width=self._width - 143,
                                           speed=0.01,
                                           callback=self.__callbackPageLPFSigmaChange)

                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="max")
                        dpg.add_drag_float(default_value=self._pageMaxThreshold,
                                           min_value=self._pageGenericRange[0],
                                           max_value=self._pageGenericRange[1],
                                           width=self._width - 110,
                                           speed=0.01,
                                           callback=self.__callbackPageMaxThresholdChange)

                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="min")
                        dpg.add_drag_float(default_value=self._pageMinThreshold,
                                           min_value=self._pageGenericRange[0],
                                           max_value=self._pageGenericRange[1],
                                           width=self._width - 110,
                                           speed=0.01,
                                           callback=self.__callbackPageMinThresholdChange)

                    dpg.add_checkbox(label="use morph",
                                     default_value=self._pageUseMorph,
                                     callback=self.__callbackPageUseMorphChange)

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

    def __callbackComboChange(self, _, data):
        self._currentFilter = data
        if data == "Canny":
            dpg.show_item(item=self._cannyGroupTag)
            dpg.hide_item(item=self._sobelGroupTag)
            dpg.hide_item(item=self._pstGroupTag)
            dpg.hide_item(item=self._pageGroupTag)
        elif data == "Sobel":
            dpg.hide_item(item=self._cannyGroupTag)
            dpg.show_item(item=self._sobelGroupTag)
            dpg.hide_item(item=self._pstGroupTag)
            dpg.hide_item(item=self._pageGroupTag)
        elif data == "PST":
            dpg.hide_item(item=self._cannyGroupTag)
            dpg.hide_item(item=self._sobelGroupTag)
            dpg.show_item(item=self._pstGroupTag)
            dpg.hide_item(item=self._pageGroupTag)
        elif data == "PAGE":
            dpg.hide_item(item=self._cannyGroupTag)
            dpg.hide_item(item=self._sobelGroupTag)
            dpg.hide_item(item=self._pstGroupTag)
            dpg.show_item(item=self._pageGroupTag)
        self.__applyFilter()

    def __applyFilter(self):
        if self._currentImage is None:
            return
        img = self._currentImage.copy()
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2GRAY)
        if self._currentFilter == "Canny":
            img = (img * 255).astype(np.uint8)
            img = cv2.Canny(image=img,
                            threshold1=self._cannyMin,
                            threshold2=self._cannyMax,
                            apertureSize=self._cannyApertureSize,
                            L2gradient=self._cannyL2Grad)
            img = (img / 255).astype(np.float32)
            self._attrImageOutput.data = cv2.cvtColor(img, cv2.COLOR_GRAY2RGBA)

        elif self._currentFilter == "Sobel":
            img = cv2.GaussianBlur(img, (3, 3), 0)
            img = cv2.Sobel(src=img,
                            ddepth=cv2.CV_32F,
                            dx=self._sobelDx,
                            dy=self._sobelDy,
                            scale=1,
                            delta=0,
                            ksize=self._sobelKs)
            self._attrImageOutput.data = cv2.cvtColor(img, cv2.COLOR_GRAY2RGBA)

        elif self._currentFilter == "PST":
            img = pst(img=img,
                      phaseStrength=self._pstPhaseStrength,
                      warpStrength=self._pstWarpStrength,
                      lpfSigma=self._pstLPFSigma,
                      minThreshold=self._pstMinThreshold,
                      maxThreshold=self._pstMaxThreshold,
                      useMorph=self._pstUseMorph)
            self._attrImageOutput.data = cv2.cvtColor(img, cv2.COLOR_GRAY2RGBA)

        elif self._currentFilter == "PAGE":
            img = page(img=img,
                       directionBins=self._pageDirectionBins,
                       mu1=self._pageMu1,
                       mu2=self._pageMu2,
                       sigma1=self._pageSigma1,
                       sigma2=self._pageSigma2,
                       phaseStrength1=self._pagePhaseStrength1,
                       phaseStrength2=self._pagePhaseStrength2,
                       lpfSigma=self._pageLPFSigma,
                       minThreshold=self._pageMinThreshold,
                       maxThreshold=self._pageMaxThreshold,
                       useMorph=self._pageUseMorph)
            self._attrImageOutput.data = cv2.cvtColor(img, cv2.COLOR_RGB2RGBA)

    def __callbackCannyMinChange(self, _, data):
        self._cannyMin = data
        if self._cannyMin >= self._cannyMax:
            self._cannyMin = self._cannyMax - 1
            dpg.set_value(item=self._cannyMinTag, value=self._cannyMin)
        self.__applyFilter()

    def __callbackCannyMaxChange(self, _, data):
        self._cannyMax = data
        if self._cannyMin >= self._cannyMax:
            self._cannyMin = self._cannyMax - 1
            dpg.set_value(item=self._cannyMinTag, value=self._cannyMin)
        self.__applyFilter()

    def __callbackCannyApertureSizeChange(self, _, data):
        self._cannyApertureSize = data
        self.__applyFilter()

    def __callbackCannyL2GradChange(self, _, data):
        self._cannyL2Grad = data
        self.__applyFilter()

    def __callbackSobelDxChange(self, _, data):
        self._sobelDx = data
        if self._sobelDx == 0 and self._sobelDy == 0:
            self._sobelDx = 1
            dpg.set_value(item=self._sobelDxTag, value=self._sobelDx)
        self.__applyFilter()

    def __callbackSobelDyChange(self, _, data):
        self._sobelDy = data
        if self._sobelDx == 0 and self._sobelDy == 0:
            self._sobelDx = 1
            dpg.set_value(item=self._sobelDxTag, value=self._sobelDx)
        self.__applyFilter()

    def __callbackSobelKsChange(self, _, data):
        self._sobelKs = data
        self.__applyFilter()

    def __callbackPSTPhaseStrengthChange(self, _, data):
        self._pstPhaseStrength = data
        self.__applyFilter()

    def __callbackPSTWarpStrengthChange(self, _, data):
        self._pstWarpStrength = data
        self.__applyFilter()

    def __callbackPST_LPF_SigmaChange(self, _, data):
        self._pstLPFSigma = data
        self.__applyFilter()

    def __callbackPSTMaxThresholdChange(self, _, data):
        self._pstMaxThreshold = data
        self.__applyFilter()

    def __callbackPSTMinThresholdChange(self, _, data):
        self._pstMinThreshold = data
        self.__applyFilter()

    def __callbackPSTUseMorphChange(self, _, data):
        self._pstUseMorph = data
        self.__applyFilter()

    def __callbackPageDirectionBinsChange(self, _, data):
        self._pageDirectionBins = data
        self.__applyFilter()

    def __callbackPageMu1Change(self, _, data):
        self._pageMu1 = data
        self.__applyFilter()

    def __callbackPageMu2Change(self, _, data):
        self._pageMu2 = data
        self.__applyFilter()

    def __callbackPageSigma1Change(self, _, data):
        self._pageSigma1 = data
        self.__applyFilter()

    def __callbackPageSigma2Change(self, _, data):
        self._pageSigma2 = data
        self.__applyFilter()

    def __callbackPagePhaseStrength1Change(self, _, data):
        self._pagePhaseStrength1 = data
        self.__applyFilter()

    def __callbackPagePhaseStrength2Change(self, _, data):
        self._pagePhaseStrength2 = data
        self.__applyFilter()

    def __callbackPageLPFSigmaChange(self, _, data):
        self._pageLPFSigma = data
        self.__applyFilter()

    def __callbackPageMaxThresholdChange(self, _, data):
        self._pageMaxThreshold = data
        self.__applyFilter()

    def __callbackPageMinThresholdChange(self, _, data):
        self._pageMinThreshold = data
        self.__applyFilter()

    def __callbackPageUseMorphChange(self, _, data):
        self._pageUseMorph = data
        self.__applyFilter()
