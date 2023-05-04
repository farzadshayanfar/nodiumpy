import cv2
import dearpygui.dearpygui as dpg
import numpy as np

from node_editor.connection_objects import NodeAttribute, AttributeType
from node_editor.editor import NodeEditor
from nodes.node import NodeBase


class Node(NodeBase):
    nodeLabel = "Image View"

    _settings = None

    def __init__(self,
                 tag: int,
                 pos: tuple[int, int],
                 editorHandle: NodeEditor):
        super().__init__(tag=tag, editor=editorHandle)
        self._baseWidth: int = self.settings.nodeWidth
        self._baseHeight: int = self.settings.nodeHeight
        self._currentWidth: int = self._baseWidth * 2
        self._currentHeight: int = self._baseHeight * 2

        self._currentImage: np.ndarray = np.zeros(shape=(2, 2))

        self._attrImageInput = NodeAttribute(tag=editorHandle.getUniqueTag(),
                                             parentNodeTag=self._tag,
                                             attrType=AttributeType.Image)

        self.inAttrs.append(self._attrImageInput)
        self._previewTextureTag: int = editorHandle.getUniqueTag()
        self._previewImageTag: int = editorHandle.getUniqueTag()
        self._smallSizeTag: int = editorHandle.getUniqueTag()
        self._mediumSizeTag: int = editorHandle.getUniqueTag()
        self._largeSizeTag: int = editorHandle.getUniqueTag()
        self._customSizeTag: int = editorHandle.getUniqueTag()
        self._saveImageTag: int = editorHandle.getUniqueTag()
        self._saveImageDialogTag: int = editorHandle.getUniqueTag()
        self._customSizeDialogTag: int = editorHandle.getUniqueTag()
        self._customWidthInputTag: int = editorHandle.getUniqueTag()
        self._customHeightInputTag: int = editorHandle.getUniqueTag()

        background = np.zeros(shape=(self._currentWidth, self._currentHeight, 4), dtype=np.float32)
        background[:, :, 3] = 1
        background = background.ravel()
        with dpg.texture_registry(show=False):
            dpg.add_raw_texture(width=self._currentWidth,
                                height=self._currentHeight,
                                default_value=background,
                                tag=self._previewTextureTag,
                                format=dpg.mvFormat_Float_rgba)

        editorHandle.createSaveImageDialog(tag=self._saveImageDialogTag,
                                           callback=self.__callbackSaveImage)

        with dpg.node(tag=self._tag,
                      parent=editorHandle.tag,
                      label=self.nodeLabel,
                      pos=pos):
            with dpg.node_attribute(tag=self._attrImageInput.tag,
                                    attribute_type=dpg.mvNode_Attr_Input,
                                    shape=dpg.mvNode_PinShape_QuadFilled):
                dpg.add_image(tag=self._previewImageTag, texture_tag=self._previewTextureTag)
                with dpg.popup(parent=self._previewImageTag):
                    dpg.add_text(default_value="image size", color=(232, 173, 9))
                    dpg.add_separator()
                    dpg.add_selectable(tag=self._smallSizeTag, width=120, label="small",
                                       callback=self.__callbackSmallSize)
                    dpg.add_selectable(tag=self._mediumSizeTag, width=120, label="medium", default_value=True,
                                       callback=self.__callbackMediumSize)
                    dpg.add_selectable(tag=self._largeSizeTag, width=120, label="large",
                                       callback=self.__callbackLargeSize)
                    dpg.add_selectable(tag=self._customSizeTag, width=120, label="custom",
                                       callback=self.__callbackCustomSize)
                    dpg.add_text(default_value="other", color=(232, 173, 9))
                    dpg.add_separator()
                    dpg.add_selectable(tag=self._saveImageTag, width=120, label="save image",
                                       callback=self.__callbackShowSaveFileDialog)

        with dpg.window(tag=self._customSizeDialogTag, no_title_bar=True, modal=True, no_resize=True,
                        show=False, no_scrollbar=True):
            dpg.add_text(default_value="custom size", color=(232, 173, 9))
            dpg.add_separator()
            with dpg.group(horizontal=True):
                dpg.add_text(default_value="width", indent=8)
                dpg.add_input_int(tag=self._customWidthInputTag,
                                  default_value=self._currentWidth,
                                  width=160)
            with dpg.group(horizontal=True):
                dpg.add_text(default_value="height")
                dpg.add_input_int(tag=self._customHeightInputTag,
                                  default_value=self._currentHeight,
                                  width=160)
            dpg.add_button(label="Okay",
                           indent=85,
                           callback=self.__callbackCustomSize2)

    def update(self):
        data = self._attrImageInput.data
        if data is None:
            return
        if np.array_equal(a1=data, a2=self._currentImage):
            return
        if self._editor.paused:
            return
        self._currentImage = data.copy()
        previewImg = cv2.resize(src=data, dsize=(self._currentWidth, self._currentHeight))
        dpg.set_value(item=self._previewTextureTag, value=previewImg.ravel())

    def close(self):
        dpg.delete_item(item=self._tag)
        del self

    def __callbackSmallSize(self):
        self._editor.pause()
        dpg.set_value(item=self._smallSizeTag, value=True)
        dpg.set_value(item=self._mediumSizeTag, value=False)
        dpg.set_value(item=self._largeSizeTag, value=False)
        dpg.set_value(item=self._customSizeTag, value=False)
        dpg.set_value(item=self._saveImageTag, value=False)
        self._currentWidth = self._baseWidth
        self._currentHeight = self._baseHeight
        self.__updateSize()

    def __callbackMediumSize(self):
        self._editor.pause()
        dpg.set_value(item=self._smallSizeTag, value=False)
        dpg.set_value(item=self._mediumSizeTag, value=True)
        dpg.set_value(item=self._largeSizeTag, value=False)
        dpg.set_value(item=self._customSizeTag, value=False)
        dpg.set_value(item=self._saveImageTag, value=False)
        self._currentWidth = self._baseWidth * 2
        self._currentHeight = self._baseHeight * 2
        self.__updateSize()

    def __callbackLargeSize(self):
        self._editor.pause()
        dpg.set_value(item=self._smallSizeTag, value=False)
        dpg.set_value(item=self._mediumSizeTag, value=False)
        dpg.set_value(item=self._largeSizeTag, value=True)
        dpg.set_value(item=self._customSizeTag, value=False)
        dpg.set_value(item=self._saveImageTag, value=False)
        self._currentWidth = self._baseWidth * 3
        self._currentHeight = self._baseHeight * 3
        self.__updateSize()

    def __callbackCustomSize(self):
        self._editor.pause()
        dpg.set_value(item=self._smallSizeTag, value=False)
        dpg.set_value(item=self._mediumSizeTag, value=False)
        dpg.set_value(item=self._largeSizeTag, value=False)
        dpg.set_value(item=self._customSizeTag, value=True)
        dpg.set_value(item=self._saveImageTag, value=False)
        dpg.set_value(item=self._customWidthInputTag, value=self._currentWidth)
        dpg.set_value(item=self._customHeightInputTag, value=self._currentHeight)
        dpg.show_item(item=self._customSizeDialogTag)

    def __callbackCustomSize2(self):
        dpg.hide_item(item=self._customSizeDialogTag)
        self._currentWidth = dpg.get_value(item=self._customWidthInputTag)
        self._currentHeight = dpg.get_value(item=self._customHeightInputTag)
        self.__updateSize()

    def __updateSize(self):
        dpg.set_item_width(item=self._previewImageTag, width=self._currentWidth)
        dpg.set_item_height(item=self._previewImageTag, height=self._currentHeight)
        dpg.delete_item(self._previewTextureTag)
        background = np.zeros(shape=(self._currentWidth, self._currentHeight, 4), dtype=np.float32)
        background[:, :, 3] = 1
        background = background.ravel()
        with dpg.texture_registry(show=False):
            dpg.add_raw_texture(width=self._currentWidth,
                                height=self._currentHeight,
                                default_value=background,
                                tag=self._previewTextureTag,
                                format=dpg.mvFormat_Float_rgba)
        dpg.configure_item(item=self._previewImageTag, texture_tag=self._previewTextureTag)
        if self._attrImageInput.data is None:
            self._editor.resume()
            return
        img = self._currentImage.copy()
        previewImg = cv2.resize(src=img, dsize=(self._currentWidth, self._currentHeight))
        dpg.set_value(item=self._previewTextureTag, value=previewImg.ravel())
        self._editor.resume()

    def __callbackShowSaveFileDialog(self):
        self._editor.pause()
        dpg.set_value(item=self._saveImageTag, value=False)
        dpg.show_item(item=self._saveImageDialogTag)

    def __callbackSaveImage(self, _, data):
        if self._currentImage is not None:
            img = (self._currentImage * 255).astype(np.uint8)
            if data["current_filter"] == ".jpg" or img.ndim != 4:
                img = cv2.cvtColor(src=img, code=cv2.COLOR_RGBA2BGR)
            else:
                img = cv2.cvtColor(src=img, code=cv2.COLOR_RGBA2BGRA)
            cv2.imwrite(filename=data["file_path_name"], img=img)
        dpg.hide_item(item=self._saveImageDialogTag)
        self._editor.resume()
