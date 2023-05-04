from typing import Union

import cv2
import dearpygui.dearpygui as dpg
import numpy as np

from node_editor.connection_objects import NodeAttribute, AttributeType
from node_editor.editor import NodeEditor
from nodes.node import NodeBase


class Node(NodeBase):
    nodeLabel = "Rotate"

    def __init__(self,
                 tag: int,
                 pos: tuple[int, int],
                 editorHandle: NodeEditor):
        super().__init__(tag=tag, editor=editorHandle)
        self._width: int = self._settings.nodeWidth
        self._currentImage: Union[np.ndarray, None] = None

        self._desiredRotationInputTag: int = editorHandle.getUniqueTag()
        self._desiredAngle: float = 0
        self._reshape: bool = True

        self._inputImageSizeLabelTag: int = editorHandle.getUniqueTag()
        self._outputImageSizeLabelTag: int = editorHandle.getUniqueTag()

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
                with dpg.group(horizontal=True, indent=10):
                    dpg.add_text(default_value="angle")
                    dpg.add_input_float(tag=self._desiredRotationInputTag,
                                        width=self._width - 80,
                                        default_value=self._desiredAngle,
                                        max_value=360,
                                        min_value=-360,
                                        min_clamped=True,
                                        max_clamped=True,
                                        callback=self.__callbackDesiredRotationChange)

                dpg.add_checkbox(label="reshape",
                                 default_value=self._reshape,
                                 indent=10,
                                 callback=self.__callbackReshapeChange)
                dpg.add_spacer(width=self._width)

            with dpg.node_attribute(tag=self._attrImageOutput.tag,
                                    attribute_type=dpg.mvNode_Attr_Output,
                                    shape=dpg.mvNode_PinShape_Triangle):
                dpg.add_text(tag=self._outputImageSizeLabelTag, indent=self._width - 85)

    def update(self):
        data = self._attrImageInput.data
        if data is None:
            return
        if np.array_equal(data, self._currentImage):
            return
        dpg.set_value(item=self._inputImageSizeLabelTag, value=data.shape[:2])
        self._currentImage = data
        self.__rotate()

    def __rotate(self):
        if self._currentImage is None:
            return
        img = self._currentImage.copy()
        shape = img.shape
        pivot = (shape[1] // 2, shape[0] // 2)
        if self._reshape:
            img = self.__rotateAndReshape(mat=img, angle=self._desiredAngle)
        else:
            rotMat = cv2.getRotationMatrix2D(center=pivot, angle=self._desiredAngle, scale=1)
            img = cv2.warpAffine(src=img, M=rotMat, dsize=(shape[1], shape[0]))

        dpg.set_value(item=self._outputImageSizeLabelTag, value=img.shape[:2])
        self._attrImageOutput.data = img

    def __callbackDesiredRotationChange(self, _, data):
        self._desiredAngle = data
        self.__rotate()

    def __callbackReshapeChange(self, _, data):
        self._reshape = data
        self.__rotate()

    def __rotateAndReshape(self, mat, angle):
        """
        Rotates an image (angle in degrees) and expands image to avoid cropping
        """

        height, width = mat.shape[:2]
        image_center = (width / 2,
                        height / 2)

        rotation_mat = cv2.getRotationMatrix2D(center=image_center, angle=angle, scale=1)

        # rotation calculates the cos and sin, taking absolutes of those.
        abs_cos = abs(rotation_mat[0, 0])
        abs_sin = abs(rotation_mat[0, 1])

        # find the new width and height bounds
        bound_w = int(height * abs_sin + width * abs_cos)
        bound_h = int(height * abs_cos + width * abs_sin)

        # subtract old image center (bringing image back to origo) and adding the new image center coordinates
        rotation_mat[0, 2] += bound_w / 2 - image_center[0]
        rotation_mat[1, 2] += bound_h / 2 - image_center[1]

        # rotate image with the new bounds and translated rotation matrix
        rotated_mat = cv2.warpAffine(src=mat, M=rotation_mat, dsize=(bound_w, bound_h), borderValue=0)
        return rotated_mat
