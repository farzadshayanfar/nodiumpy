import dearpygui.dearpygui as dpg
import numpy as np

from node_editor.connection_objects import NodeAttribute, AttributeType
from node_editor.editor import NodeEditor
from nodes.node import NodeBase
from nodes.viewers.objects.composer_objects import Canvas, CanvasImage, BlendModes


class Node(NodeBase):
    nodeLabel = "Canvas"

    _settings = None
    _blendModes = ["normal", "dissolve", "dancing dissolve", "multiply", "screen", "overlay", "subtract", "difference"]
    _blendModeStringToEnum = {"normal": BlendModes.NORMAL,
                              "dissolve": BlendModes.DISSOLVE,
                              "dancing dissolve": BlendModes.DANCING_DISSOLVE,
                              "multiply": BlendModes.MULTIPLY,
                              "screen": BlendModes.SCREEN,
                              "overlay": BlendModes.OVERLAY,
                              "subtract": BlendModes.SUBTRACT,
                              "difference": BlendModes.DIFFERENCE}

    def __init__(self,
                 tag: int,
                 pos: tuple[int, int],
                 editorHandle: NodeEditor):
        super().__init__(tag=tag, editor=editorHandle)
        self._width: int = self.settings.nodeWidth
        self._inputAttrTag2InputAttrMap: dict[int, NodeAttribute] = dict()
        self._inputAttrTag2CanvasImageMap: dict[int, CanvasImage] = dict()
        self._inputCount: int = 1

        self._canvas = Canvas()

        self._attrImageOutput = NodeAttribute(tag=editorHandle.getUniqueTag(),
                                              parentNodeTag=self._tag,
                                              attrType=AttributeType.Image)

        self.outAttrs.append(self._attrImageOutput)

        with dpg.node(tag=self._tag,
                      parent=editorHandle.tag,
                      label=self.nodeLabel,
                      pos=pos):
            with dpg.node_attribute(tag=self._attrImageOutput.tag,
                                    attribute_type=dpg.mvNode_Attr_Output,
                                    shape=dpg.mvNode_PinShape_Triangle):
                with dpg.group(indent=18):
                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="size", indent=8)
                        dpg.add_input_intx(size=2,
                                           width=self._width - 100,
                                           default_value=(self._canvas.defaultWidth, self._canvas.defaultHeight),
                                           min_value=10,
                                           max_value=3840,
                                           min_clamped=True,
                                           max_clamped=True,
                                           callback=self.__callbackCanvasSizeChange)
                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="input")
                        dpg.add_input_int(width=self._width - 100,
                                          default_value=self._inputCount,
                                          min_value=1,
                                          min_clamped=True,
                                          on_enter=True,
                                          callback=self.__callbackInputCountChange)
                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="bkg", indent=15)
                        dpg.add_color_edit(no_inputs=True,
                                           alpha_bar=True,
                                           default_value=[255, 255, 255, 255],
                                           callback=self.__callbackCanvasColorChange)

            self.__addInputAttr()
            self._attrImageOutput.data = self._canvas.render()

    def update(self):
        anyChange = False
        tag2attrMap = self._inputAttrTag2InputAttrMap.copy()
        for attrTag, inputAttr in tag2attrMap.items():
            data = inputAttr.data
            if data is None:
                continue
            canvasImage = self._inputAttrTag2CanvasImageMap[attrTag]
            if not inputAttr.blocked:
                canvasImage.src = None
                anyChange = True
                continue
            if canvasImage.src is None:
                canvasImage.src = data
                anyChange = True
                continue
            if np.array_equal(a1=data, a2=canvasImage.src):
                continue
            canvasImage.src = data
            anyChange = True
        if anyChange:
            self._attrImageOutput.data = self._canvas.render()

    def __addInputAttr(self):
        tag = self._editor.getUniqueTag()
        attr = NodeAttribute(tag=tag, parentNodeTag=self._tag, attrType=AttributeType.Image)
        self.inAttrs.append(attr)
        self._inputAttrTag2InputAttrMap[tag] = attr
        canvasImage = CanvasImage()
        self._canvas.layers.append(canvasImage)
        self._inputAttrTag2CanvasImageMap[tag] = canvasImage

        with dpg.node_attribute(tag=attr.tag,
                                parent=self._tag,
                                attribute_type=dpg.mvNode_Attr_Input,
                                shape=dpg.mvNode_PinShape_QuadFilled):
            dpg.add_spacer(width=self._width, height=10)

            with dpg.group(indent=6):
                with dpg.group(horizontal=True):
                    dpg.add_drag_int(default_value=0,
                                     speed=10,
                                     format="left %.2f",
                                     width=self._width - 135,
                                     min_value=-3840,
                                     max_value=3840,
                                     clamped=True,
                                     callback=self.__callbackLeftChange,
                                     user_data=canvasImage)
                    dpg.add_drag_int(default_value=0,
                                     speed=10,
                                     format="top %.2f",
                                     width=self._width - 135,
                                     min_value=-3840,
                                     max_value=3840,
                                     clamped=True,
                                     callback=self.__callbackTopChange,
                                     user_data=canvasImage)
                with dpg.group(horizontal=True):
                    dpg.add_drag_float(default_value=1,
                                       min_value=-0.25,
                                       max_value=4,
                                       clamped=True,
                                       format="scale %.2f",
                                       speed=0.05,
                                       width=self._width - 135,
                                       callback=self.__callbackScaleChange,
                                       user_data=canvasImage)
                    dpg.add_drag_int(default_value=0,
                                     min_value=-180,
                                     max_value=180,
                                     format="rot %f",
                                     clamped=True,
                                     speed=1,
                                     width=self._width - 135,
                                     callback=self.__callbackRotationChange,
                                     user_data=canvasImage)
                with dpg.group(horizontal=True):
                    dpg.add_combo(items=self._blendModes,
                                  default_value=self._blendModes[0],
                                  width=self._width - 135,
                                  no_arrow_button=True,
                                  callback=self.__callbackBlendModeChange,
                                  user_data=canvasImage)
                    dpg.add_drag_int(default_value=100,
                                     min_value=0,
                                     format="opacity %f",
                                     max_value=100,
                                     width=self._width - 135,
                                     callback=self.__callbackOpacityChange,
                                     user_data=canvasImage)

    def __removeInputAttr(self, attrTag: int):
        attr = self._inputAttrTag2InputAttrMap[attrTag]
        self.inAttrs.remove(attr)
        del self._inputAttrTag2InputAttrMap[attrTag]
        canvasImage = self._inputAttrTag2CanvasImageMap[attrTag]
        self._canvas.layers.remove(canvasImage)
        del self._inputAttrTag2CanvasImageMap[attrTag]
        if attr.connections:
            self._editor.callbackRemoveLink(sender=None, data=attr.connections[0].tag)
        dpg.delete_item(item=attr.tag)
        self._attrImageOutput.data = self._canvas.render()

    def __callbackInputCountChange(self, _, data):
        if self._inputCount == data:
            return

        dif = abs(self._inputCount - data)
        if self._inputCount > data:
            attrTags = list(self._inputAttrTag2InputAttrMap.keys())
            for _ in range(dif):
                tag = attrTags.pop()
                self.__removeInputAttr(attrTag=tag)
        else:
            for _ in range(dif):
                self.__addInputAttr()

        self._inputCount = data

    def __callbackCanvasSizeChange(self, _, data):
        self._canvas.width = data[0]
        self._canvas.height = data[1]
        self._canvas.createBackground()
        self._attrImageOutput.data = self._canvas.render()

    def __callbackCanvasColorChange(self, _, data):
        self._canvas.color = data
        self._canvas.createBackground()
        self._attrImageOutput.data = self._canvas.render()

    def __callbackLeftChange(self, _, data, user_data: CanvasImage):
        user_data.left = data
        self._attrImageOutput.data = self._canvas.render()

    def __callbackTopChange(self, _, data, user_data: CanvasImage):
        user_data.top = data
        self._attrImageOutput.data = self._canvas.render()

    def __callbackScaleChange(self, sender, data, user_data: CanvasImage):
        if user_data.src is None:
            dpg.set_value(item=sender, value=user_data.scale)
            return
        user_data.scale = data
        self._attrImageOutput.data = self._canvas.render()

    def __callbackRotationChange(self, sender, data, user_data: CanvasImage):
        if user_data.src is None:
            dpg.set_value(item=sender, value=user_data.rot)
            return
        user_data.rot = data
        self._attrImageOutput.data = self._canvas.render()

    def __callbackBlendModeChange(self, _, data, user_data: CanvasImage):
        user_data.blendMode = self._blendModeStringToEnum[data]
        self._attrImageOutput.data = self._canvas.render()

    def __callbackOpacityChange(self, _, data, user_data: CanvasImage):
        user_data.opacity = data
        self._attrImageOutput.data = self._canvas.render()
