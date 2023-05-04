import traceback
from typing import Union

import dearpygui.dearpygui as dpg
import numpy as np

from node_editor.connection_objects import NodeAttribute, AttributeType
from node_editor.editor import NodeEditor
from nodes.node import NodeBase


class Node(NodeBase):
    nodeLabel = "Code Snippet"

    def __init__(self,
                 tag: int,
                 pos: tuple[int, int],
                 editorHandle: NodeEditor):
        super().__init__(tag=tag, editor=editorHandle)
        self._width: int = self._settings.nodeWidth * 1.3
        self._currentImage: Union[np.ndarray, None] = None
        self._snippetTextInputTag: int = editorHandle.getUniqueTag()
        self._defaultText: str = "outImg = inImg"

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
                dpg.add_input_text(tag=self._snippetTextInputTag,
                                   default_value=self._defaultText,
                                   width=self._width,
                                   height=230,
                                   multiline=True)
                with dpg.group(horizontal=True, indent=70):
                    dpg.add_button(label="reset",
                                   width=80,
                                   callback=self.__callbackReset)
                    dpg.add_button(label="apply",
                                   width=80,
                                   callback=self.__applySnippet)
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
        self.__applySnippet()

    def __applySnippet(self):
        if self._currentImage is None:
            return
        img = self._currentImage.copy()
        execLocals = {"outImg": None, "inImg": img}
        snippet = dpg.get_value(item=self._snippetTextInputTag)
        try:
            exec(snippet, globals(), execLocals)
        except:
            traceback.print_exc()
        finally:
            self._attrImageOutput.data = execLocals["outImg"]

    def __callbackReset(self):
        dpg.set_value(item=self._snippetTextInputTag,
                      value=self._defaultText)
        self.__applySnippet()
