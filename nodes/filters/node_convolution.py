from typing import Union

import cv2
import dearpygui.dearpygui as dpg
import numpy as np

from node_editor.connection_objects import NodeAttribute, AttributeType
from node_editor.editor import NodeEditor
from nodes.node import NodeBase


class Node(NodeBase):
    nodeLabel = "Convolution"
    _borderTypes = ["default", "constant", "replicate", "reflect", "reflect101", "transparent", "isolated"]
    _borderType2CVEnumMap = {"default": cv2.BORDER_DEFAULT,
                             "constant": cv2.BORDER_CONSTANT,
                             "replicate": cv2.BORDER_REPLICATE,
                             "reflect": cv2.BORDER_REFLECT,
                             "reflect101": cv2.BORDER_REFLECT101,
                             "transparent": cv2.BORDER_TRANSPARENT,
                             "isolated": cv2.BORDER_ISOLATED}

    def __init__(self,
                 tag: int,
                 pos: tuple[int, int],
                 editorHandle: NodeEditor):
        super().__init__(tag=tag, editor=editorHandle)
        self._width: int = self._settings.nodeWidth
        self._currentImage: Union[np.ndarray, None] = None
        self._border: str = self._borderTypes[0]
        self._kernelSize: tuple[int, int] = (3, 3)
        self._kernel: np.ndarray = np.ones(shape=self._kernelSize)
        self._kernelRange: tuple[float, float] = (-10, 10)
        self._newKernel: np.ndarray = self._kernel
        self._anchor: list[int, int] = [self._kernelSize[0] // 2, self._kernelSize[1] // 2]

        self._kernelSizeWindowTag: int = editorHandle.getUniqueTag()
        self._kernelWidthInputTag: int = editorHandle.getUniqueTag()
        self._kernelHeightInputTag: int = editorHandle.getUniqueTag()
        self._kernelValuesWindowTag: int = editorHandle.getUniqueTag()
        self._kernelValuesTableTag: int = editorHandle.getUniqueTag()
        self._kernelAnchorWindowTag: int = editorHandle.getUniqueTag()
        self._kernelAnchorTableTag: int = editorHandle.getUniqueTag()

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

            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_button(label="size", width=150, height=30, indent=45,
                               callback=self.__callbackShowKernelSizeWindow)
                dpg.add_button(label="values", width=150, height=30, indent=45,
                               callback=self.__callbackShowKernelValuesWindow)
                dpg.add_button(label="anchor", width=150, height=30, indent=45,
                               callback=self.__callbackShowAnchorWindow)
                with dpg.group(horizontal=True):
                    dpg.add_text(default_value="border type")
                    dpg.add_combo(width=self._width - 95,
                                  items=self._borderTypes,
                                  default_value=self._border,
                                  callback=self.__callbackBorderTypeChange)

                with dpg.window(tag=self._kernelSizeWindowTag, no_title_bar=True, modal=True, no_resize=True,
                                show=False, no_scrollbar=True):
                    dpg.add_text(default_value="kernel size", color=(232, 173, 9))
                    dpg.add_separator()
                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="rows")
                        dpg.add_input_int(tag=self._kernelWidthInputTag,
                                          default_value=self._kernelSize[0],
                                          width=160,
                                          min_value=1,
                                          min_clamped=True)
                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="cols")
                        dpg.add_input_int(tag=self._kernelHeightInputTag,
                                          default_value=self._kernelSize[1],
                                          width=160,
                                          min_value=1,
                                          min_clamped=True)
                    dpg.add_button(label="Okay",
                                   indent=85,
                                   callback=self.__callbackSetKernelSize)

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

    def close(self):
        dpg.delete_item(item=self._tag)

    def __applyFilter(self):
        if self._currentImage is None:
            return
        img = self._currentImage.copy()
        img = cv2.filter2D(src=img,
                           ddepth=cv2.CV_32F,
                           kernel=self._kernel,
                           anchor=self._anchor,
                           borderType=self._borderType2CVEnumMap[self._border])
        self._attrImageOutput.data = img

    def __callbackShowKernelSizeWindow(self):
        self._editor.pause()
        dpg.set_value(item=self._kernelWidthInputTag, value=self._kernelSize[0])
        dpg.set_value(item=self._kernelHeightInputTag, value=self._kernelSize[1])
        dpg.show_item(item=self._kernelSizeWindowTag)

    def __callbackSetKernelSize(self):
        width = dpg.get_value(item=self._kernelWidthInputTag)
        height = dpg.get_value(item=self._kernelHeightInputTag)
        self._kernelSize = (width, height)
        self._kernel = np.ones(shape=self._kernelSize)
        self._newKernel = self._kernel
        dpg.hide_item(item=self._kernelSizeWindowTag)
        self._editor.resume()
        self.__applyFilter()

    def __callbackShowKernelValuesWindow(self):
        self._editor.pause()
        with dpg.window(tag=self._kernelValuesWindowTag, no_title_bar=True, modal=True, no_scrollbar=False,
                        no_resize=True):
            dpg.add_text(default_value="kernel values", color=(232, 173, 9))
            dpg.add_separator()
            with dpg.table(tag=self._kernelValuesTableTag,
                           parent=self._kernelValuesWindowTag,
                           header_row=False):
                for _ in range(self._kernelSize[1]):
                    dpg.add_table_column()
                for i in range(self._kernelSize[0]):
                    with dpg.table_row():
                        for k in range(self._kernelSize[1]):
                            dpg.add_drag_float(width=55,
                                               speed=0.01,
                                               default_value=self._kernel[i, k],
                                               format="%.3f",
                                               user_data=[i, k],
                                               min_value=self._kernelRange[0],
                                               max_value=self._kernelRange[1],
                                               callback=self.__callbackUpdateKernel)
            dpg.add_button(label="Okay",
                           indent=85,
                           callback=self.__callbackSetKernelValues)

    def __callbackSetKernelValues(self):
        self._kernel = self._newKernel
        dpg.delete_item(item=self._kernelValuesWindowTag)
        self._editor.resume()
        self.__applyFilter()

    def __callbackUpdateKernel(self, _, data, user_data):
        self._newKernel[user_data[0], user_data[1]] = data

    def __callbackShowAnchorWindow(self):
        self._editor.pause()
        with dpg.window(tag=self._kernelAnchorWindowTag, no_title_bar=True, modal=True, no_scrollbar=False,
                        no_resize=True):
            dpg.add_text(default_value="kernel anchor", color=(232, 173, 9))
            dpg.add_separator()
            with dpg.table(tag=self._kernelAnchorTableTag,
                           parent=self._kernelAnchorWindowTag,
                           header_row=False):
                for _ in range(self._kernelSize[1]):
                    dpg.add_table_column()
                for i in range(self._kernelSize[0]):
                    with dpg.table_row():
                        for k in range(self._kernelSize[1]):
                            dpg.add_selectable(label=f"{[i, k]}",
                                               default_value=False,
                                               callback=self.__callbackSetKernelAnchor,
                                               user_data=[i, k])

    def __callbackSetKernelAnchor(self, _, data, user_data):
        dpg.delete_item(item=self._kernelAnchorWindowTag)
        self._anchor = user_data
        self._editor.resume()
        self.__applyFilter()

    def __callbackBorderTypeChange(self, _, data):
        self._border = data
        self.__applyFilter()
