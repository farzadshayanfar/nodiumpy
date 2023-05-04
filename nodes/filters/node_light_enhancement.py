from typing import Union

import dearpygui.dearpygui as dpg
import numpy as np

from node_editor.connection_objects import NodeAttribute, AttributeType
from node_editor.editor import NodeEditor
from nodes.filters.algorithms.light_enhancement import vevid
from nodes.node import NodeBase


class Node(NodeBase):
    nodeLabel = "Light Enhancement"

    _filters = ["VEVID"]

    def __init__(self,
                 tag: int,
                 pos: tuple[int, int],
                 editorHandle: NodeEditor):
        super().__init__(tag=tag, editor=editorHandle)
        self._width: int = self._settings.nodeWidth
        self._currentImage: Union[np.ndarray, None] = None
        self._currentFilter = self._filters[0]

        self._vevidGroupTag: int = editorHandle.getUniqueTag()
        self._vevidGenericRange: tuple[float, float] = (0, 1)
        self._vevidPhaseStrength: float = 0.3
        self._vevidSpectralPhaseFcnVariance: float = 0.001
        self._vevidRegularizationTerm: float = 0.17
        self._vevidPhaseActivationGainRange: tuple[float, float] = (1, 10)
        self._vevidPhaseActivationGain: float = 1.4
        self._vevidEnhanceColor: bool = False
        self._vevidLiteMode: bool = True

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

                with dpg.group(tag=self._vevidGroupTag, indent=25):
                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="ps", indent=16)
                        dpg.add_drag_float(tag=editorHandle.getUniqueTag(),
                                           default_value=self._vevidPhaseStrength,
                                           width=self._width - 85,
                                           callback=self.__callbackVEVIDPhaseStrengthChange,
                                           min_value=self._vevidGenericRange[0],
                                           max_value=self._vevidGenericRange[1],
                                           no_input=False,
                                           speed=0.01)

                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="b", indent=24)
                        dpg.add_drag_float(tag=editorHandle.getUniqueTag(),
                                           default_value=self._vevidRegularizationTerm,
                                           width=self._width - 85,
                                           callback=self.__callbackVEVIDRegTermChange,
                                           min_value=self._vevidGenericRange[0],
                                           max_value=self._vevidGenericRange[1],
                                           no_input=False,
                                           speed=0.01)

                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="gain")
                        dpg.add_drag_float(tag=editorHandle.getUniqueTag(),
                                           default_value=self._vevidPhaseActivationGain,
                                           width=self._width - 85,
                                           callback=self.__callbackVEVIDGainChange,
                                           min_value=self._vevidPhaseActivationGainRange[0],
                                           max_value=self._vevidPhaseActivationGainRange[1],
                                           no_input=False,
                                           speed=0.01)

                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="variance")
                        dpg.add_drag_float(tag=editorHandle.getUniqueTag(),
                                           default_value=self._vevidSpectralPhaseFcnVariance,
                                           width=self._width - 118,
                                           callback=self.__callbackVEVIDVarianceChange,
                                           min_value=self._vevidGenericRange[0],
                                           max_value=self._vevidGenericRange[1],
                                           no_input=False,
                                           speed=0.01)

                    dpg.add_checkbox(label="enhance color",
                                     default_value=self._vevidEnhanceColor,
                                     callback=self.__callbackVEVIDEnhanceColor)

                    dpg.add_checkbox(label="lite mode",
                                     default_value=self._vevidLiteMode,
                                     callback=self.__callbackVEVIDLiteMode)

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

    def __applyFilter(self):
        if self._currentImage is None:
            return
        img = self._currentImage.copy()
        if self._currentFilter == "VEVID":
            img = vevid(img=img,
                        phaseStrength=self._vevidPhaseStrength,
                        spectralPhaseFcnVariance=self._vevidSpectralPhaseFcnVariance,
                        regularizationTerm=self._vevidRegularizationTerm,
                        phaseActivationGain=self._vevidPhaseActivationGain,
                        enhanceColor=self._vevidEnhanceColor,
                        liteMode=self._vevidLiteMode)
            self._attrImageOutput.data = img

    def __callbackComboChange(self, _, data):
        self._currentFilter = data
        if data == "VEVID":
            dpg.show_item(item=self._vevidGroupTag)
        self.__applyFilter()

    def __callbackVEVIDPhaseStrengthChange(self, _, data):
        self._vevidPhaseStrength = data
        self.__applyFilter()

    def __callbackVEVIDVarianceChange(self, _, data):
        self._vevidSpectralPhaseFcnVariance = data
        self.__applyFilter()

    def __callbackVEVIDRegTermChange(self, _, data):
        self._vevidRegularizationTerm = data
        self.__applyFilter()

    def __callbackVEVIDGainChange(self, _, data):
        self._vevidPhaseActivationGain = data
        self.__applyFilter()

    def __callbackVEVIDEnhanceColor(self, _, data):
        self._vevidEnhanceColor = data
        self.__applyFilter()

    def __callbackVEVIDLiteMode(self, _, data):
        self._vevidLiteMode = data
        self.__applyFilter()
