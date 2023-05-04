import time

import cv2
import dearpygui.dearpygui as dpg
import numpy as np
from PIL import ImageGrab

from node_editor.connection_objects import NodeAttribute, AttributeType
from node_editor.editor import NodeEditor
from nodes.node import NodeBase


class Node(NodeBase):
    nodeLabel = "Screen Recorder"
    _modes = ["only main screen", "all screens"]

    def __init__(self,
                 tag: int,
                 pos: tuple[int, int],
                 editorHandle: NodeEditor):
        super().__init__(tag=tag, editor=editorHandle)
        self._width: int = self._settings.nodeWidth
        self._captureMode: str = self._modes[0]
        self._keepCapturing: bool = True
        self._captureInterval: float = 0.033
        self._keepTicking: bool = False
        self._t1: float = 0
        self._t2: float = 0

        self._captureIntervalGroupTag: int = editorHandle.getUniqueTag()
        self._frameSizeTextTag: int = editorHandle.getUniqueTag()
        self._currentFrameSize: tuple[int, int] = (0, 0)

        self._attrImageOutput = NodeAttribute(tag=editorHandle.getUniqueTag(),
                                              parentNodeTag=self._tag,
                                              attrType=AttributeType.Image)

        self.outAttrs.append(self._attrImageOutput)

        with dpg.node(tag=self._tag,
                      parent=editorHandle.tag,
                      label=self.nodeLabel,
                      pos=pos):
            with dpg.node_attribute(tag=editorHandle.getUniqueTag(),
                                    attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_combo(items=self._modes,
                              default_value=self._captureMode,
                              width=self._width,
                              callback=self.__callbackCaptureModeChange)
                dpg.add_button(label="capture",
                               width=self._width,
                               callback=self.__callbackCapture)
                dpg.add_checkbox(label="keep capturing",
                                 default_value=self._keepCapturing,
                                 callback=self.__callbackKeepCapturingChange)
                with dpg.group(tag=self._captureIntervalGroupTag, horizontal=True, show=self._keepCapturing):
                    dpg.add_text(default_value="interval")
                    dpg.add_input_float(width=140,
                                        min_value=0,
                                        min_clamped=True,
                                        step=0.01,
                                        default_value=self._captureInterval)

            with dpg.node_attribute(tag=self._attrImageOutput.tag,
                                    attribute_type=dpg.mvNode_Attr_Output,
                                    shape=dpg.mvNode_PinShape_Triangle):
                dpg.add_text(tag=self._frameSizeTextTag,
                             wrap=self._width,
                             indent=self._width - 100)
            self.__capture()

    def update(self):
        if not self._keepCapturing:
            return
        if not self._keepTicking:
            self._keepTicking = True
            self._t1 = time.perf_counter()
        self._t2 = time.perf_counter()
        if self._t2 - self._t1 > self._captureInterval:
            self.__capture()
            self._keepTicking = False

    def __capture(self):
        if self._captureMode == "all screens":
            img = ImageGrab.grab(all_screens=True, include_layered_windows=True)
        else:
            img = ImageGrab.grab(all_screens=False, include_layered_windows=True)

        img = np.asarray(a=img)
        img = cv2.cvtColor(src=img, code=cv2.COLOR_RGB2RGBA)
        img = (img / 255).astype(np.float32)
        self._attrImageOutput.data = img
        if self._currentFrameSize != img.shape[:2]:
            self._currentFrameSize = img.shape[:2]
            dpg.set_value(item=self._frameSizeTextTag, value=img.shape[:2])

    def __callbackCapture(self):
        if self._keepCapturing:
            return
        self.__capture()

    def __callbackCaptureModeChange(self, _, data):
        self._captureMode = data
        self.__capture()

    def __callbackKeepCapturingChange(self, _, data):
        self._keepCapturing = data
        if data:
            dpg.show_item(item=self._captureIntervalGroupTag)
        else:
            dpg.hide_item(item=self._captureIntervalGroupTag)
        self.__capture()
