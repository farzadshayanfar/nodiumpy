from typing import Union

import dearpygui.dearpygui as dpg
import numpy as np

from node_editor.connection_objects import NodeAttribute, AttributeType
from node_editor.editor import NodeEditor
from nodes.node import NodeBase


class Node(NodeBase):
    nodeLabel = "Crop"
    _modes = ["center crop", "two corner crop"]

    def __init__(self,
                 tag: int,
                 pos: tuple[int, int],
                 editorHandle: NodeEditor):
        super().__init__(tag=tag, editor=editorHandle)
        self._width: int = self._settings.nodeWidth
        self._currentMode: str = self._modes[0]
        self._currentImage: Union[np.ndarray, None] = None

        self._inputImageSizeLabelTag: int = editorHandle.getUniqueTag()
        self._outputImageSizeLabelTag: int = editorHandle.getUniqueTag()
        self._centerCropGroupTag: int = editorHandle.getUniqueTag()
        self._twoCenterCropGroupTag: int = editorHandle.getUniqueTag()

        self._cropWidth: int = 100
        self._cropHeight: int = 100
        self._corner1Left: int = 0
        self._corner1Top: int = 0
        self._corner2Left: int = 50
        self._corner2Top: int = 50

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
                dpg.add_combo(width=self._width,
                              items=self._modes,
                              default_value=self._currentMode,
                              callback=self.__callbackCropModeChange)
                with dpg.group(tag=self._centerCropGroupTag, indent=50):
                    dpg.add_drag_int(default_value=self._cropWidth,
                                     speed=10,
                                     format="width %f",
                                     width=self._width - 100,
                                     min_value=0,
                                     max_value=3840,
                                     clamped=True,
                                     callback=self.__callbackCenterWidthChange)
                    dpg.add_drag_int(default_value=self._cropHeight,
                                     speed=10,
                                     format="height %f",
                                     width=self._width - 100,
                                     min_value=0,
                                     max_value=3840,
                                     clamped=True,
                                     callback=self.__callbackCenterHeightChange)
                with dpg.group(tag=self._twoCenterCropGroupTag, show=False):
                    with dpg.group(horizontal=True, indent=18):
                        dpg.add_drag_int(default_value=self._corner1Left,
                                         speed=10,
                                         format="c1 left %f",
                                         width=self._width - 150,
                                         min_value=0,
                                         max_value=3840,
                                         clamped=True,
                                         callback=self.__callbackCorner1LeftChange)
                        dpg.add_drag_int(default_value=self._corner1Top,
                                         speed=10,
                                         format="c1 top %f",
                                         width=self._width - 150,
                                         min_value=0,
                                         max_value=3840,
                                         clamped=True,
                                         callback=self.__callbackCorner2TopChange)
                    with dpg.group(horizontal=True, indent=18):
                        dpg.add_drag_int(default_value=self._corner2Left,
                                         speed=10,
                                         format="c2 left %f",
                                         width=self._width - 150,
                                         min_value=0,
                                         max_value=3840,
                                         clamped=True,
                                         callback=self.__callbackCorner2LeftChange)
                        dpg.add_drag_int(default_value=self._corner2Top,
                                         speed=10,
                                         format="c2 top %f",
                                         width=self._width - 150,
                                         min_value=0,
                                         max_value=3840,
                                         clamped=True,
                                         callback=self.__callbackCorner2TopChange)
                dpg.add_spacer(width=self._width)

            with dpg.node_attribute(tag=self._attrImageOutput.tag,
                                    attribute_type=dpg.mvNode_Attr_Output,
                                    shape=dpg.mvNode_PinShape_Triangle):
                dpg.add_text(tag=self._outputImageSizeLabelTag, indent=self._width - 85)

    def update(self):
        data = self._attrImageInput.data
        if data is None:
            dpg.set_value(item=self._inputImageSizeLabelTag, value="")
            self._currentImage = None
            return
        if np.array_equal(data, self._currentImage):
            return
        dpg.set_value(item=self._inputImageSizeLabelTag, value=data.shape[:2])
        self._currentImage = data

        self.__crop()

    def __crop(self):
        if self._currentImage is None:
            return
        img = self._currentImage.copy()
        height, width = img.shape[:2]
        if self._currentMode == "center crop":
            centerRow = height // 2
            centerCol = width // 2
            rowStart = centerRow - self._cropHeight // 2
            rowEnd = centerRow + self._cropHeight // 2
            colStart = centerCol - self._cropWidth // 2
            colEnd = centerCol + self._cropWidth // 2
        else:
            rowStart = self._corner1Top
            rowEnd = self._corner2Top
            colStart = self._corner1Left
            colEnd = self._corner2Left
        if rowEnd < rowStart or colEnd < colStart:
            return
        if rowStart < 0:
            rowStart = 0
        if colStart < 0:
            colStart = 0
        if rowEnd > height:
            rowEnd = height
        if colEnd > width:
            colEnd = width

        outImg = img[rowStart:rowEnd, colStart:colEnd]
        dpg.set_value(item=self._outputImageSizeLabelTag, value=outImg.shape[:2])
        self._attrImageOutput.data = outImg

    def __callbackCropModeChange(self, _, data):
        self._currentMode = data
        if data == "center crop":
            dpg.show_item(item=self._centerCropGroupTag)
            dpg.hide_item(item=self._twoCenterCropGroupTag)
        else:
            dpg.hide_item(item=self._centerCropGroupTag)
            dpg.show_item(item=self._twoCenterCropGroupTag)
        self.__crop()

    def __callbackCenterWidthChange(self, _, data):
        self._cropWidth = data
        self.__crop()

    def __callbackCenterHeightChange(self, _, data):
        self._cropHeight = data
        self.__crop()

    def __callbackCorner1LeftChange(self, _, data):
        self._corner1Left = data
        self.__crop()

    def __callbackCorner1TopChange(self, _, data):
        self._corner1Top = data
        self.__crop()

    def __callbackCorner2LeftChange(self, _, data):
        self._corner2Left = data
        self.__crop()

    def __callbackCorner2TopChange(self, _, data):
        self._corner2Top = data
        self.__crop()
