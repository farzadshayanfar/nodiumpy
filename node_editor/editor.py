import time
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

import dearpygui.dearpygui as dpg

from node_editor.connection_objects import TreeNode, Connection, Tree
from settings import AppSettings


class NodeEditor(object):
    def __init__(self,
                 settings: AppSettings,
                 menuDict: dict,
                 nodeDir: str):
        self._tree: Tree = Tree()
        self._updateInterval: float = settings.treeUpdateInterval
        self._updateT1: float = 0
        self._updateT2: float = 0
        self._nodeTagToNodeMap: dict = dict()
        self._counter: int = 9999
        self._terminated: bool = False
        self._settings: AppSettings = settings
        self._tag: int = self.getUniqueTag()
        self._windowTag: int = self.getUniqueTag()
        self._lastPos: tuple = (0, 0)
        self._paused: bool = False
        self._nodesPlannedToBeClosed: list = list()

        self._editorContextMenuTag: int = self.getUniqueTag()

        # creating the window
        with dpg.window(tag=self._windowTag,
                        width=settings.windowWidth,
                        height=settings.windowHeight,
                        menubar=True,
                        no_title_bar=True,
                        no_close=True,
                        no_collapse=True):

            # adding menubar
            with dpg.menu_bar(label="MenuBar"):
                with dpg.menu(label="Options"):
                    dpg.add_menu_item(label="Toggle Full Screen", callback=dpg.toggle_viewport_fullscreen)
                for menuName, itemName in menuDict.items():
                    with dpg.menu(label=menuName):
                        dirPath = Path(nodeDir).joinpath(itemName)
                        nodePaths = dirPath.glob(pattern="*.py")
                        for nodePath in nodePaths:
                            if nodePath.name.startswith('__init__'):
                                continue
                            spec = spec_from_file_location(name=nodePath.stem, location=nodePath)
                            module = module_from_spec(spec=spec)
                            spec.loader.exec_module(module=module)

                            node = module.Node
                            dpg.add_menu_item(tag=self.getUniqueTag(),
                                              label=node.nodeLabel,
                                              callback=self.__callbackAddNode,
                                              user_data=node)

            # adding the actual node editor
            dpg.add_node_editor(tag=self._tag,
                                callback=self.__callbackAddLink,
                                delink_callback=self.callbackRemoveLink,
                                minimap=True,
                                minimap_location=dpg.mvNodeMiniMap_Location_BottomRight)

            with dpg.handler_registry():
                dpg.add_mouse_click_handler(button=0, callback=self.__callbackLeftMouseClick)
                dpg.add_key_press_handler(key=dpg.mvKey_Delete, callback=self.__callbackRemoveNode)

    def __callbackLeftMouseClick(self):
        selectedNodesTags = dpg.get_selected_nodes(node_editor=self.tag)
        if selectedNodesTags:
            lastSelectedNodeTag = selectedNodesTags[0]
            self._lastPos = dpg.get_item_pos(item=lastSelectedNodeTag)

    @property
    def tag(self):
        return self._tag

    @property
    def windowTag(self):
        return self._windowTag

    @property
    def settings(self):
        return self._settings

    @property
    def terminated(self):
        return self._terminated

    @property
    def paused(self):
        return self._paused

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def terminate(self):
        self._paused = True
        self._nodesPlannedToBeClosed.extend(list(self._nodeTagToNodeMap.values()))
        self._terminated = True

    def __callbackAddNode(self, sender, data, user_data):
        # user_data is a node constructor
        tag = self.getUniqueTag()
        self._lastPos = (self._lastPos[0] + 30, self._lastPos[1] + 30)
        nodeobj = user_data(tag=tag,
                            pos=self._lastPos,
                            editorHandle=self)
        aTreeNode = TreeNode(tag=tag, inAttrs=nodeobj.inAttrs, outAttrs=nodeobj.outAttrs, updateFcn=nodeobj.update)
        self._tree.addNode(node=aTreeNode)
        self._nodeTagToNodeMap[tag] = nodeobj

    def __callbackRemoveNode(self):
        selectedLinksTags = dpg.get_selected_links(node_editor=self.tag)
        selectedNodesTags = dpg.get_selected_nodes(node_editor=self.tag)
        if selectedNodesTags:
            self._nodesPlannedToBeClosed.extend(selectedNodesTags)
        elif selectedLinksTags:
            for linkTag in selectedLinksTags:
                self.callbackRemoveLink(None, linkTag)

    def __removeNodes(self):
        for nodeTag in self._nodesPlannedToBeClosed:
            node = self._tree.getNodeByTag(tag=nodeTag)
            del self._nodeTagToNodeMap[nodeTag]
            dpg.delete_item(item=node.tag)
            self._tree.removeNodeByObject(node=node)
        self._nodesPlannedToBeClosed.clear()

    def __callbackAddLink(self, _, data):
        # data is (outAttrTag, inAttrTag)
        # remember that the link is directed: from outAttr of one node to inAttr of another
        outAttrTag, inAttrTag = data
        originAttr = self._tree.getAttrByTag(tag=outAttrTag)
        originNode = self._tree.getNodeByTag(tag=originAttr.parentNodeTag)
        targetAttr = self._tree.getAttrByTag(tag=inAttrTag)
        targetNode = self._tree.getNodeByTag(tag=targetAttr.parentNodeTag)
        if targetAttr.blocked and originAttr.attrType != targetAttr.attrType:
            return
        linkTag = self.getUniqueTag()
        aConnection = Connection(tag=linkTag,
                                 originNode=originNode,
                                 originAttr=originAttr,
                                 targetNode=targetNode,
                                 targetAttr=targetAttr)
        self._tree.addConnection(connection=aConnection)
        dpg.add_node_link(attr_1=outAttrTag, attr_2=inAttrTag, parent=self.tag, tag=linkTag)

    def callbackRemoveLink(self, sender, data):
        # data is linkTag
        # remember that the link is directed: from outAttr of one node to inAttr of another
        self._tree.removeConnectionByTag(tag=data)
        dpg.delete_item(item=data)

    def update(self):
        while not self._terminated:
            if self._paused:
                time.sleep(0.3)
                continue
            if self._nodesPlannedToBeClosed:
                self.__removeNodes()
            if self._tree.connections:

                self._tree.updateLevels()
                if not self._tree.levels:
                    continue
                self._tree.updateConnections()
                self._tree.updateNodes()
            else:
                time.sleep(0.3)
        if self._nodesPlannedToBeClosed:
            self.__removeNodes()

    def getUniqueTag(self):
        tag = self._counter
        self._counter += 1
        return tag

    def createImageFileSelectionDialog(self, tag, callback):
        with dpg.file_dialog(tag=tag,
                             directory_selector=False,
                             default_path=self._settings.HomeDir,
                             show=False,
                             modal=True,
                             width=int(self._settings.nodeWidth * 2.5),
                             height=self._settings.nodeHeight * 3 + 100,
                             callback=callback):
            dpg.add_file_extension(extension="Image (*.bmp *.jpg *.png *.gif){.bmp,.jpg,.png,.gif}")
            dpg.add_file_extension(extension="", color=(255, 182, 158))

    def createVideoFileSelectionDialog(self, tag, callback):
        with dpg.file_dialog(tag=tag,
                             default_path=self._settings.HomeDir,
                             directory_selector=False,
                             show=False,
                             modal=True,
                             width=int(self._settings.nodeWidth * 2.5),
                             height=self._settings.nodeHeight * 3 + 100,
                             callback=callback):
            dpg.add_file_extension("Movie (*.mp4 *.avi){.mp4,.avi}")
            dpg.add_file_extension("", color=(255, 182, 158))

    def createFolderSelectionDialog(self, tag, callback):
        dpg.add_file_dialog(tag=tag,
                            default_path=self._settings.HomeDir,
                            directory_selector=True,
                            show=False,
                            modal=True,
                            width=int(self._settings.nodeWidth * 2.5),
                            height=self._settings.nodeHeight * 3 + 100,
                            callback=callback)

    def createSaveImageDialog(self, tag, callback):
        with dpg.file_dialog(tag=tag,
                             directory_selector=False,
                             default_path=self._settings.HomeDir,
                             default_filename="output",
                             show=False,
                             modal=True,
                             width=int(self._settings.nodeWidth * 2.5),
                             height=self._settings.nodeHeight * 3 + 100,
                             callback=callback):
            dpg.add_file_extension(extension=".jpg,.png")
            dpg.add_file_extension(extension="", color=(255, 182, 158))
