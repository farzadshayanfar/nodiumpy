#!/usr/bin/env python
# -*- coding: utf-8 -*-
import threading
from typing import Union

import cv2
import dearpygui.dearpygui as dpg
import numpy as np

from node_editor.connection_objects import NodeAttribute, AttributeType
from node_editor.editor import NodeEditor
from nodes.node import NodeBase


class Node(NodeBase):
    nodeLabel = "Webcam"

    def __init__(self,
                 tag: int,
                 pos: tuple[int, int],
                 editorHandle: NodeEditor):
        super().__init__(tag=tag, editor=editorHandle)
        self._width: int = self._settings.nodeWidth
        self._deviceIndexList: list[int] = list()
        self._currentVideoCapture: Union[cv2.VideoCapture, None] = None
        self._currentDevice: int = 0
        self._loadingAttrTag: int = editorHandle.getUniqueTag()
        self._loadingTextTag: int = editorHandle.getUniqueTag()
        self._loadingIndicatorTag: int = editorHandle.getUniqueTag()
        self._deviceComboTag: int = editorHandle.getUniqueTag()

        self._attrImageOutput = NodeAttribute(tag=editorHandle.getUniqueTag(),
                                              parentNodeTag=self._tag,
                                              attrType=AttributeType.Image)
        self.outAttrs.append(self._attrImageOutput)

        with dpg.node(tag=self._tag,
                      parent=editorHandle.tag,
                      label=self.nodeLabel,
                      pos=pos):
            with dpg.node_attribute(tag=self._loadingAttrTag,
                                    attribute_type=dpg.mvNode_Attr_Static):
                with dpg.group():
                    dpg.add_text(tag=self._loadingTextTag,
                                 default_value="Checking available cameras:\n(this can take a while)")
                    dpg.add_loading_indicator(tag=self._loadingIndicatorTag, indent=80)
                    dpg.add_spacer(width=self._width)

            with dpg.node_attribute(tag=self._attrImageOutput.tag,
                                    attribute_type=dpg.mvNode_Attr_Output,
                                    shape=dpg.mvNode_PinShape_Triangle,
                                    show=False):
                dpg.add_spacer(width=self._width)
        threading.Thread(target=self.__checkAndAddCameraDevices).start()

    def update(self):
        if self._currentVideoCapture is None:
            return
        ret, frame = self._currentVideoCapture.read()
        if ret:
            frame = cv2.cvtColor(src=frame, code=cv2.COLOR_BGR2RGBA)
            frame = frame.astype(np.float32) / 255
            self._attrImageOutput.data = frame

    def close(self):
        if self._currentVideoCapture is not None:
            self._currentVideoCapture.release()
        dpg.delete_item(item=self._tag)

    def __checkAndAddCameraDevices(self):
        for i in range(5):
            cap = cv2.VideoCapture(i)
            if cap is None or not cap.isOpened():
                count = len(self._deviceIndexList)
                dpg.set_value(item=self._loadingTextTag, value=f"{count} cameras were found")
                dpg.hide_item(item=self._loadingIndicatorTag)
                break
            self._deviceIndexList.append(i)
            cap.release()
        if self._deviceIndexList:
            dpg.hide_item(item=self._loadingTextTag)
            dpg.hide_item(item=self._loadingIndicatorTag)
            items = [f"device {x}" for x in self._deviceIndexList]
            dpg.add_combo(parent=self._loadingAttrTag,
                          tag=self._deviceComboTag,
                          width=self._width,
                          items=items,
                          default_value=items[0],
                          callback=self.__callbackDeviceChange)
            dpg.show_item(item=self._attrImageOutput.tag)
            self.__useWebcam(deviceIndex=0)

    def __callbackDeviceChange(self, sender, data):
        index = int(data.split(" ")[-1])
        self.__useWebcam(deviceIndex=index)

    def __useWebcam(self, deviceIndex: int):
        if self._currentVideoCapture is not None:
            self._currentVideoCapture.release()
        self._currentVideoCapture = cv2.VideoCapture(deviceIndex, cv2.CAP_DSHOW)
        self._currentVideoCapture.set(cv2.CAP_PROP_FRAME_WIDTH, self._settings.webcamWidth)
        self._currentVideoCapture.set(cv2.CAP_PROP_FRAME_HEIGHT, self._settings.windowHeight)
