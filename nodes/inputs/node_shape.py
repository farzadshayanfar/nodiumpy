import dearpygui.dearpygui as dpg
import numpy as np
from PIL import Image, ImageDraw

from node_editor.connection_objects import NodeAttribute, AttributeType
from node_editor.editor import NodeEditor
from nodes.node import NodeBase


class Node(NodeBase):
    nodeLabel = "2D Shape"
    _shapes = ["circle", "ellipse", "rectangle", "line", "regular polygon", "polygon"]

    def __init__(self,
                 tag: int,
                 pos: tuple[int, int],
                 editorHandle: NodeEditor):
        super().__init__(tag=tag, editor=editorHandle)
        self._width: int = self._settings.nodeWidth
        self._shapeToTagMap: dict = {x: y for x, y in
                                     zip(self._shapes, [editorHandle.getUniqueTag() for _ in range(len(self._shapes))])}
        self._currentShape: str = self._shapes[0]

        self._strokeWidth: int = 1
        self._strokeColor: tuple[int, int, int, int] = (0, 0, 0, 255)

        self._fillColor: tuple[int, int, int, int] = (255, 0, 0, 255)
        self._fill: bool = True

        self._circleRadius: int = 100

        self._ellipseHorizontalDiameter: int = 200
        self._ellipseVerticalDiameter: int = 100

        self._rectangleWidth: int = 400
        self._rectangleHeight: int = 250

        self._lineGroupTag: int = editorHandle.getUniqueTag()
        self._lineLength: int = 200

        self._regularPolygonSidesN: int = 3
        self._regularPolygonBoundRadius: int = 100
        self._regularPolygonRotation: int = 0

        self._polygonPoints: list[tuple[int, int]] = list()

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
                dpg.add_combo(width=self._width,
                              items=self._shapes,
                              default_value=self._currentShape,
                              callback=self.__callbackShapeChange)

                with dpg.group(tag=self._shapeToTagMap["circle"],
                               horizontal=True,
                               indent=15):
                    dpg.add_text(default_value="radius")
                    dpg.add_input_int(width=128,
                                      default_value=self._circleRadius,
                                      callback=self.__callbackRadiusChange)

                with dpg.group(tag=self._shapeToTagMap["ellipse"],
                               indent=15,
                               show=False):
                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="width", indent=8)
                        dpg.add_input_int(width=128,
                                          default_value=self._ellipseHorizontalDiameter,
                                          callback=self.__callbackEllipseHDiameterChange)
                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="height")
                        dpg.add_input_int(width=128,
                                          default_value=self._ellipseVerticalDiameter,
                                          callback=self.__callbackEllipseVDiameterChange)

                with dpg.group(tag=self._shapeToTagMap["rectangle"],
                               indent=15,
                               show=False):
                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="width", indent=8)
                        dpg.add_input_int(width=128,
                                          default_value=self._rectangleWidth,
                                          callback=self.__callbackRectangleWidthChange)
                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="height")
                        dpg.add_input_int(width=128,
                                          default_value=self._rectangleHeight,
                                          callback=self.__callbackRectangleHeightChange)

                with dpg.group(tag=self._shapeToTagMap["line"],
                               horizontal=True,
                               indent=15, show=False):
                    dpg.add_text(default_value="length")
                    dpg.add_input_int(width=128,
                                      default_value=self._lineLength,
                                      callback=self.__callbackLineLengthChange)

                with dpg.group(tag=self._shapeToTagMap["regular polygon"],
                               indent=15,
                               show=False):
                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="radius")
                        dpg.add_input_int(width=128,
                                          default_value=self._regularPolygonBoundRadius,
                                          callback=self.__callbackRPolygonRadiusChange)
                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="sides", indent=8)
                        dpg.add_input_int(width=128,
                                          default_value=self._regularPolygonSidesN,
                                          min_value=3,
                                          min_clamped=True,
                                          callback=self.__callbackRPolygonSideNChange)
                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="rot", indent=23)
                        dpg.add_input_int(width=128,
                                          default_value=self._regularPolygonRotation,
                                          min_value=0,
                                          min_clamped=True,
                                          callback=self.__callbackRPolygonRotChange)

                with dpg.group(tag=self._shapeToTagMap["polygon"],
                               indent=15,
                               show=False):
                    dpg.add_button(label="set points", width=self._width - 100)
                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="points")
                        dpg.add_listbox(width=self._width - 108)

                with dpg.group(horizontal=True, indent=15):
                    dpg.add_text(default_value="stroke")
                    dpg.add_color_edit(no_inputs=True,
                                       alpha_bar=True,
                                       default_value=self._strokeColor,
                                       callback=self.__callbackStrokeColorChange)
                    dpg.add_drag_int(format="w %.2f",
                                     width=90,
                                     default_value=self._strokeWidth,
                                     callback=self.__callbackStrokeWidthChange)

                with dpg.group(horizontal=True, indent=15):
                    dpg.add_text(default_value="fill", indent=16)
                    dpg.add_color_edit(no_inputs=True,
                                       alpha_bar=True,
                                       default_value=self._fillColor,
                                       callback=self.__callbackFillColorChange)
                    dpg.add_checkbox(default_value=True,
                                     callback=self.__fillStateChange)

            dpg.add_node_attribute(tag=self._attrImageOutput.tag,
                                   attribute_type=dpg.mvNode_Attr_Output,
                                   shape=dpg.mvNode_PinShape_Triangle)
        self.__draw()

    def update(self):
        return None

    def __draw(self):
        if self._currentShape == "circle":
            length = self._circleRadius * 2
            img = Image.new(mode="RGBA", size=(length, length), color=(0, 0, 0, 0))
            draw = ImageDraw.Draw(im=img, mode="RGBA")
            draw.ellipse(xy=(0, 0, length, length),
                         fill=self._fillColor if self._fill else None,
                         outline=self._strokeColor,
                         width=self._strokeWidth)

        elif self._currentShape == "ellipse":
            img = Image.new(mode="RGBA",
                            size=(self._ellipseHorizontalDiameter, self._ellipseVerticalDiameter),
                            color=(0, 0, 0, 0))
            draw = ImageDraw.Draw(im=img, mode="RGBA")
            draw.ellipse(xy=(0, 0, self._ellipseHorizontalDiameter, self._ellipseVerticalDiameter),
                         fill=self._fillColor if self._fill else None,
                         outline=self._strokeColor,
                         width=self._strokeWidth)

        elif self._currentShape == "rectangle":
            width = self._rectangleWidth
            height = self._rectangleHeight
            img = Image.new(mode="RGBA", size=(width, height))
            draw = ImageDraw.Draw(im=img, mode="RGBA")
            draw.rectangle(xy=(0, 0, width, height),
                           fill=self._fillColor if self._fill else None,
                           outline=self._strokeColor,
                           width=self._strokeWidth)

        elif self._currentShape == "line":
            img = Image.new(mode="RGBA",
                            size=(self._lineLength, self._strokeWidth))
            draw = ImageDraw.Draw(im=img, mode="RGBA")
            draw.line(xy=(0, 0, self._lineLength, 0),
                      fill=self._strokeColor,
                      width=self._strokeWidth)

        elif self._currentShape == "regular polygon":
            length = self._regularPolygonBoundRadius * 2
            img = Image.new(mode="RGBA", size=(length, length), color=(0, 0, 0, 0))
            draw = ImageDraw.Draw(im=img, mode="RGBA")
            draw.regular_polygon(bounding_circle=(length // 2, length // 2, self._regularPolygonBoundRadius),
                                 n_sides=self._regularPolygonSidesN,
                                 rotation=self._regularPolygonRotation,
                                 fill=self._fillColor if self._fill else None,
                                 outline=self._strokeColor)

        elif self._currentShape == "polygon":
            pass

        img = (np.asarray(a=img) / 255).astype(np.float32)
        self._attrImageOutput.data = img

    def __callbackShapeChange(self, _, data):
        self._currentShape = data
        for shape, groupTag in self._shapeToTagMap.items():
            if shape == data:
                dpg.show_item(item=groupTag)
            else:
                dpg.hide_item(item=groupTag)
        self.__draw()

    def __callbackRadiusChange(self, _, data):
        self._circleRadius = data
        self.__draw()

    def __callbackEllipseHDiameterChange(self, _, data):
        self._ellipseHorizontalDiameter = data
        self.__draw()

    def __callbackEllipseVDiameterChange(self, _, data):
        self._ellipseVerticalDiameter = data
        self.__draw()

    def __callbackRectangleWidthChange(self, _, data):
        self._rectangleWidth = data
        self.__draw()

    def __callbackRectangleHeightChange(self, _, data):
        self._rectangleHeight = data
        self.__draw()

    def __callbackLineLengthChange(self, _, data):
        self._lineLength = data
        self.__draw()

    def __callbackRPolygonRadiusChange(self, _, data):
        self._regularPolygonBoundRadius = data
        self.__draw()

    def __callbackRPolygonSideNChange(self, _, data):
        self._regularPolygonSidesN = data
        self.__draw()

    def __callbackRPolygonRotChange(self, _, data):
        self._regularPolygonRotation = data
        self.__draw()

    def __callbackStrokeColorChange(self, _, data):
        self._strokeColor = tuple([int(x * 255) for x in data])
        self.__draw()

    def __callbackStrokeWidthChange(self, _, data):
        self._strokeWidth = data
        self.__draw()

    def __callbackFillColorChange(self, _, data):
        self._fillColor = tuple([int(x * 255) for x in data])
        self.__draw()

    def __fillStateChange(self, _, data):
        self._fill = data
        self.__draw()
