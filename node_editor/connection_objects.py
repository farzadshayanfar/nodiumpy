import enum
from typing import Union, Callable

import numpy as np


class AttributeType(enum.Enum):
    Image = 0
    InferenceResult = 1
    AnyArray = 2
    TorchModelFeatures = 3


class NodeAttribute:
    def __init__(self, *,
                 tag: int,
                 parentNodeTag: int,
                 attrType: AttributeType):
        self._tag: int = tag
        self._parentNodeTag: int = parentNodeTag
        self._blocked: bool = False
        self._attrType = attrType
        self._data: Union[np.ndarray, None] = None
        self._connections: list[Connection] = list()

    @property
    def tag(self):
        return self._tag

    @property
    def parentNodeTag(self):
        return self._parentNodeTag

    @property
    def data(self) -> Union[np.ndarray, None]:
        return self._data

    @data.setter
    def data(self, value: Union[np.ndarray, None]):
        if value is not None:
            self._data = value

    @property
    def blocked(self):
        return self._blocked

    @blocked.setter
    def blocked(self, value: bool):
        self._blocked = value

    @property
    def attrType(self):
        return self._attrType

    @property
    def connections(self):
        return self._connections


class TreeNode:
    def __init__(self,
                 tag: int,
                 inAttrs: list[NodeAttribute],
                 outAttrs: list[NodeAttribute],
                 updateFcn: Union[None, Callable] = None):
        self._tag = tag
        self._updateFcn: Union[None, Callable] = updateFcn
        self._connections: list[Connection] = list()
        self._inAttrs: list[NodeAttribute] = inAttrs
        self._outAttrs: list[NodeAttribute] = outAttrs

    @property
    def tag(self):
        return self._tag

    @property
    def updateFcn(self):
        return self._updateFcn

    @property
    def connections(self):
        return self._connections

    @property
    def inAttrs(self):
        return self._inAttrs

    @property
    def outAttrs(self):
        return self._outAttrs


class Connection:
    def __init__(self, *,
                 originNode: TreeNode,
                 originAttr: NodeAttribute,
                 targetNode: TreeNode,
                 targetAttr: NodeAttribute,
                 tag: int):
        self._originNode: TreeNode = originNode
        self._originAttr: NodeAttribute = originAttr
        self._targetNode: TreeNode = targetNode
        self._targetAttr: NodeAttribute = targetAttr
        self._tag: int = tag

    @property
    def originNode(self):
        return self._originNode

    @property
    def originAttr(self):
        return self._originAttr

    @property
    def targetNode(self):
        return self._targetNode

    @property
    def targetAttr(self):
        return self._targetAttr

    @property
    def tag(self):
        return self._tag


class Tree:
    def __init__(self):
        self._levels: list[list[TreeNode]] = list()  # levels of nodes
        self._nodes: list[TreeNode] = list()
        self._connections: list[Connection] = list()
        self._tagToEntityMap: dict = dict()

    @property
    def levels(self):
        return self._levels

    @property
    def nodes(self):
        return self._nodes

    @property
    def connections(self):
        return self._connections

    def updateLevels(self):
        if len(self._connections) == 0:
            return
        self._levels.clear()

        # first get the upstream nodes (output-only nodes)
        topLevel = list()
        for connection in self._connections:
            if not connection.originNode.inAttrs:
                topLevel.append(connection.originNode)
            else:
                checkList = list()
                for inAttr in connection.originNode.inAttrs:
                    checkList.append(False if inAttr.blocked else True)
                if np.all(a=np.array(checkList)):
                    topLevel.append(connection.originNode)

        aCounter = 0
        levelsDict = dict()
        levelsDict[aCounter] = topLevel
        for node in topLevel:
            self.__traceBranch(node=node, levelsDict=levelsDict, counter=aCounter)

        self._levels = [list(set(x)) for x in levelsDict.values()]

    def updateConnections(self):
        for level in self._levels:
            for node in level:
                for outAttr in node.outAttrs:
                    for connection in outAttr.connections:
                        connection.targetAttr.data = \
                            None if connection.originAttr.data is None else connection.originAttr.data.copy()

    def updateNodes(self):
        newLevels = list()
        self._levels.reverse()
        alreadyConsideredNodes = list()
        for level in self._levels:
            aLevel = list()
            for node in level:
                if node not in alreadyConsideredNodes:
                    aLevel.append(node)
                    alreadyConsideredNodes.append(node)
            newLevels.append(aLevel)
        newLevels.reverse()
        for level in newLevels:
            for node in level:
                node.updateFcn()

    def __traceBranch(self, node: TreeNode, levelsDict: dict, counter: int):
        counter += 1
        for connection in node.connections:
            if counter not in levelsDict:
                levelsDict[counter] = list()
            levelsDict[counter].append(connection.targetNode)

        for connection in node.connections:
            if connection.targetNode.outAttrs:
                for outAttr in connection.targetNode.outAttrs:
                    for outConnection in outAttr.connections:
                        self.__traceBranch(node=outConnection.targetNode, levelsDict=levelsDict, counter=counter)

    def addNode(self,
                node: TreeNode):
        self._nodes.append(node)
        self._tagToEntityMap[node.tag] = node

    def removeNodeByTag(self, tag: int):
        node = self._tagToEntityMap[tag]
        for connection in node.connections:
            self.removeConnectionByObject(connection=connection)
        self._nodes.remove(node)
        del self._tagToEntityMap[tag]

    def removeNodeByObject(self, node: TreeNode):
        for connection in node.connections:
            self.removeConnectionByObject(connection=connection)
        self._nodes.remove(node)
        del self._tagToEntityMap[node.tag]

    def getNodeByTag(self, tag: int) -> TreeNode:
        return self._tagToEntityMap[tag]

    def addConnection(self,
                      connection: Connection):
        connection.originAttr.connections.append(connection)
        connection.originNode.connections.append(connection)
        connection.targetAttr.blocked = True
        connection.targetAttr.connections.append(connection)
        connection.targetNode.connections.append(connection)
        self._connections.append(connection)
        self._tagToEntityMap[connection.tag] = connection

    def removeConnectionByTag(self, tag: int):
        connection = self._tagToEntityMap[tag]
        self.removeConnectionByObject(connection=connection)

    def removeConnectionByObject(self, connection: Connection):
        connection.originAttr.connections.remove(connection)
        connection.originNode.connections.remove(connection)
        connection.targetAttr.blocked = False
        connection.targetAttr.data = None
        connection.targetAttr.connections.remove(connection)
        connection.targetNode.connections.remove(connection)
        self._connections.remove(connection)
        del self._tagToEntityMap[connection.tag]

    def getConnectionByTag(self, tag: int) -> Union[Connection, None]:
        return self._tagToEntityMap[tag]

    def getAttrByTag(self, tag: int) -> Union[NodeAttribute, None]:
        for node in self._nodes:
            for outAttr in node.outAttrs:
                if outAttr.tag == tag:
                    return outAttr

            for inAttr in node.inAttrs:
                if inAttr.tag == tag:
                    return inAttr
