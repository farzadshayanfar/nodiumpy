from typing import Callable, Union

import dearpygui.dearpygui as dpg

from node_editor.connection_objects import NodeAttribute
from node_editor.editor import NodeEditor
from settings import AppSettings


class NodeBase:
    def __init__(self,
                 tag: int,
                 editor: NodeEditor):
        self._tag: int = tag
        self._editor: NodeEditor = editor
        self._settings: AppSettings = editor.settings
        self._inAttrs: list[NodeAttribute] = list()
        self._outAttrs: list[NodeAttribute] = list()
        self._updateFcn: Union[Callable, None] = None

    @property
    def tag(self):
        return self._tag

    @property
    def editor(self):
        return self._editor

    @property
    def settings(self):
        return self._settings

    @property
    def inAttrs(self):
        return self._inAttrs

    @property
    def outAttrs(self):
        return self._outAttrs

    @property
    def updateFcn(self):
        return self._updateFcn

    def update(self):
        pass

    def close(self):
        dpg.delete_item(item=self._tag)
