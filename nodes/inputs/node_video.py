from typing import Union

import cv2
import dearpygui.dearpygui as dpg
import numpy as np

from node_editor.connection_objects import NodeAttribute, AttributeType
from nodes.inputs.objects.video_objects import VideoFile
from node_editor.editor import NodeEditor
from nodes.node import NodeBase


class Node(NodeBase):
    nodeLabel = "Video"

    def __init__(self,
                 tag: int,
                 pos: tuple[int, int],
                 editorHandle: NodeEditor):
        super().__init__(tag=tag, editor=editorHandle)
        self._width: int = self._settings.nodeWidth
        self._editorHandle = editorHandle

        self._cvf: Union[VideoFile, None] = None

        self._frameSizeTextTag: int = editorHandle.getUniqueTag()
        self._isPlayingTag: int = editorHandle.getUniqueTag()
        self._seekSliderTag: int = editorHandle.getUniqueTag()
        self._controlAttrTag: int = editorHandle.getUniqueTag()

        self._loop: bool = True
        self._play: bool = False
        self._skipRange = (1, 15)
        self._skipValue = self._skipRange[0]
        self._seekRange: tuple[int, int] = (0, 999)

        self._attrImageOutput = NodeAttribute(tag=editorHandle.getUniqueTag(),
                                              parentNodeTag=self._tag,
                                              attrType=AttributeType.Image)
        self.outAttrs.append(self._attrImageOutput)

        with dpg.node(tag=self._tag, parent=editorHandle.tag, label=self.nodeLabel, pos=pos):
            self.fileDialogTag = editorHandle.getUniqueTag()
            editorHandle.createVideoFileSelectionDialog(tag=self.fileDialogTag, callback=self.__callbackOpenFile)
            with dpg.node_attribute(tag=editorHandle.getUniqueTag(),
                                    attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_button(label='select video',
                               width=self._width,
                               callback=self.__callbackSelectVideo)

            with dpg.node_attribute(tag=self._controlAttrTag,
                                    attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_drag_int(tag=editorHandle.getUniqueTag(),
                                 width=self._width,
                                 format="x %f",
                                 default_value=self._skipValue,
                                 min_value=self._skipRange[0],
                                 max_value=self._skipRange[1],
                                 clamped=True,
                                 callback=self.__callbackSkipRate)
                dpg.add_drag_int(tag=self._seekSliderTag,
                                 width=self._width,
                                 format="pos %f",
                                 default_value=0,
                                 min_value=self._seekRange[0],
                                 max_value=self._seekRange[1],
                                 clamped=True,
                                 callback=self.__callbackSeekFrame)

                with dpg.group(tag=editorHandle.getUniqueTag(), horizontal=True):
                    dpg.add_checkbox(label='loop',
                                     callback=self.__callbackLooping,
                                     default_value=self._loop)
                    dpg.add_checkbox(label='play',
                                     tag=self._isPlayingTag,
                                     callback=self.__callbackPlaying,
                                     default_value=self._play)

            with dpg.node_attribute(tag=self._attrImageOutput.tag,
                                    attribute_type=dpg.mvNode_Attr_Output,
                                    shape=dpg.mvNode_PinShape_Triangle):
                dpg.add_text(tag=self._frameSizeTextTag,
                             wrap=self._width,
                             indent=self._width - 100)

    def __callbackSelectVideo(self):
        self._editorHandle.pause()
        dpg.show_item(item=self.fileDialogTag)

    def update(self):
        if self._cvf is None:
            return
        if not self._play:
            return
        dpg.set_value(item=self._seekSliderTag, value=self._cvf.currentFrame)
        if not self._cvf.currentFrame + self._skipValue >= self._cvf.frameCount:
            self._cvf.currentFrame += self._skipValue
        else:
            if self._loop:
                self._cvf.currentFrame = 0
            else:
                self._cvf.currentFrame = self._cvf.frameCount - 1
                dpg.set_value(item=self._isPlayingTag, value=False)
                self._play = False
                dpg.enable_item(item=self._seekSliderTag)
                return
        frame = self._cvf.readCurrentFrame()
        frame = cv2.cvtColor(src=frame, code=cv2.COLOR_BGR2RGBA)
        frame = frame.astype(np.float32) / 255
        self._attrImageOutput.data = frame

    def close(self):
        if self._cvf is not None:
            self._cvf.closeVideoFile()
        dpg.delete_item(item=self._tag)

    def __callbackOpenFile(self, _, data):
        # data is a dictionary with some keys being "file_path_name", \
        # "file_name", "current_path", "current_filter"
        self._cvf = VideoFile(inputFile=data["file_path_name"])
        self._seekRange = (0, self._cvf.frameCount - 1)
        dpg.configure_item(item=self._seekSliderTag,
                           default_value=0,
                           min_value=self._seekRange[0],
                           max_value=self._seekRange[1])
        frame = self._cvf.readCurrentFrame()
        frame = cv2.cvtColor(src=frame, code=cv2.COLOR_BGR2RGBA)
        frame = frame.astype(np.float32) / 255
        self._attrImageOutput.data = frame

        dpg.set_value(item=self._frameSizeTextTag, value=frame.shape[:2])
        self._editorHandle.resume()

    def __callbackLooping(self, _, data):
        self._loop = data

    def __callbackPlaying(self, _, data):
        self._play = data
        if data:
            dpg.disable_item(item=self._seekSliderTag)
        else:
            dpg.enable_item(item=self._seekSliderTag)

    def __callbackSkipRate(self, _, data):
        self._skipValue = data

    def __callbackSeekFrame(self, _, data):
        if self._cvf is None:
            return
        if self._play:
            return
        frame = self._cvf.retrieveFrame(frameIndex=data)
        frame = cv2.cvtColor(src=frame, code=cv2.COLOR_BGR2RGBA)
        frame = frame.astype(np.float32) / 255
        self._attrImageOutput.data = frame
