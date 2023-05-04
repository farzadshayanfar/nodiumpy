import json
import sys
from pathlib import Path

import dearpygui.dearpygui as dpg

from Resources import Fonts


class AppSettings:
    HomeDir: str = str(Path.home().resolve())
    AppRootPath: Path = Path(__file__).parent
    CacheDirPath: Path = Path.home().joinpath(".cache/nodium")
    SettingsFilePath: Path = Path.home().joinpath(".cache/nodium").joinpath("nodium.json")

    def __init__(self):
        sys.path.insert(0, str(self.AppRootPath.resolve()))

        self.CacheDirPath.mkdir(parents=True, exist_ok=True)
        self.SettingsFilePath.touch(exist_ok=True)

        self._windowWidth: int = 1280
        self._windowHeight: int = 720
        self._webcamHeight: int = 720
        self._webcamWidth: int = 1280
        self._useWebcam: bool = False
        self._deviceNoList: list[int] = list()
        self._videoCaptureList: list = list()
        self._useSerial: bool = False
        self._serialDeviceNoList: list[str] = list()
        self._serialConnectionList: list = list()
        self._nodeWidth: int = 250
        self._nodeHeight: int = 141
        self._videoWriterFPS: int = 30
        self._usePrefCounter: bool = True
        self._drawInfoOnResult: bool = True
        self._outputDirPath: Path = self.CacheDirPath.joinpath("viewers")
        self._outputDirPath.mkdir(parents=True, exist_ok=True)
        self._treeUpdateInterval: float = 0.1

    @property
    def windowWidth(self):
        return self._windowWidth

    @property
    def windowHeight(self):
        return self._windowHeight

    @property
    def useWebcam(self):
        return self._useWebcam

    @useWebcam.setter
    def useWebcam(self, value: bool):
        self._useWebcam = value

    @property
    def webcamWidth(self):
        return self._webcamWidth

    @property
    def webcamHeight(self):
        return self._webcamHeight

    @property
    def deviceNoList(self):
        return self._deviceNoList

    @deviceNoList.setter
    def deviceNoList(self, value: list[int]):
        self._deviceNoList = value

    @property
    def videoCaptureList(self):
        return self._videoCaptureList

    @videoCaptureList.setter
    def videoCaptureList(self, value: list):
        self._videoCaptureList = value

    @property
    def useSerial(self):
        return self._useSerial

    @useSerial.setter
    def useSerial(self, value: bool):
        self._useSerial = value

    @property
    def serialDeviceNoList(self):
        return self._serialDeviceNoList

    @serialDeviceNoList.setter
    def serialDeviceNoList(self, value: list[str]):
        self._serialDeviceNoList = value

    @property
    def serialConnectionList(self):
        return self._serialConnectionList

    @serialConnectionList.setter
    def serialConnectionList(self, value: list):
        self._serialConnectionList = value

    @property
    def nodeWidth(self):
        return self._nodeWidth

    @nodeWidth.setter
    def nodeWidth(self, value: int):
        self._nodeWidth = value

    @property
    def nodeHeight(self):
        return self._nodeHeight

    @nodeHeight.setter
    def nodeHeight(self, value: int):
        self._nodeHeight = value

    @property
    def videoWriterFPS(self):
        return self._videoWriterFPS

    @videoWriterFPS.setter
    def videoWriterFPS(self, value: int):
        self._videoWriterFPS = value

    @property
    def usePrefCounter(self):
        return self._usePrefCounter

    @usePrefCounter.setter
    def usePrefCounter(self, value: bool):
        self._usePrefCounter = value

    @property
    def drawInfoOnResult(self):
        return self._drawInfoOnResult

    @drawInfoOnResult.setter
    def drawInfoOnResult(self, value: bool):
        self._drawInfoOnResult = value

    @property
    def useGPU(self):
        return self._useGPU

    @useGPU.setter
    def useGPU(self, value: bool):
        self._useGPU = value

    @property
    def treeUpdateInterval(self):
        return self._treeUpdateInterval

    @treeUpdateInterval.setter
    def treeUpdateInterval(self, value: float):
        self._treeUpdateInterval = value

    @property
    def outputDirPath(self):
        return self._outputDirPath

    @outputDirPath.setter
    def outputDirPath(self, value: Path):
        self._outputDirPath = value

    def __loadFromSettingsFile(self) -> None:
        contents = self.SettingsFilePath.read_text(encoding="utf-8")
        if contents:
            data = json.loads(self.SettingsFilePath.read_text())
        else:
            data = dict()
        if not data:
            return
        try:
            self._windowWidth = data["windowWidth"]
            self._windowHeight = data["windowHeight"]
            self._useWebcam = data["useWebcam"]
            self._webcamWidth = data["webcamWidth"]
            self._webcamHeight = data["webcamHeight"]
            self._useSerial = data["useSerial"]
            self._nodeWidth = data["nodeWidth"]
            self._nodeHeight = data["nodeHeight"]
            self._videoWriterFPS = data["videoWriterFPS"]
            self._usePrefCounter = data["usePrefCounter"]
            self._drawInfoOnResult = data["drawInfoOnResult"]
            self._outputDirPath = Path(data["outputDirPath"])

        except KeyError:
            self.updateSettingsFile()
            self.__loadFromSettingsFile()

    def updateSettingsFile(self):
        data = dict(windowWidth=self._windowWidth,
                    windowHeight=self._windowHeight,
                    useWebcam=self._useWebcam,
                    webcamWidth=self._webcamWidth,
                    webcamHeight=self._webcamHeight,
                    useSerial=self._useSerial,
                    inputWindowWidth=self._nodeWidth,
                    inputWindowHeight=self._nodeWidth,
                    videoWriterFPS=self._videoWriterFPS,
                    usePrefCounter=self._usePrefCounter,
                    drawInfoOnResult=self._drawInfoOnResult,
                    outputDirPath=str(self._outputDirPath.resolve()))
        jstring = json.dumps(data, ensure_ascii=False, indent=4)
        self.SettingsFilePath.write_text(data=jstring, encoding="utf-8")

    @staticmethod
    def createTheme() -> int:
        with dpg.theme() as themeTag:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(target=dpg.mvStyleVar_WindowPadding, x=5, y=5, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_WindowBorderSize, x=0, y=0, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_FramePadding, x=12, y=16, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_FrameRounding, x=6, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_FrameBorderSize, x=0, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_ItemSpacing, x=8, y=9, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_ItemInnerSpacing, x=5, y=9, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_CellPadding, x=5, y=9, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_PopupBorderSize, x=2, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_PopupRounding, x=3, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_ScrollbarRounding, x=10, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_GrabMinSize, x=16, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_GrabRounding, x=5, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(target=dpg.mvThemeCol_FrameBgHovered, value=(40, 40, 40),
                                    category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(target=dpg.mvThemeCol_FrameBgActive, value=(30, 30, 30),
                                    category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(target=dpg.mvThemeCol_ButtonHovered, value=(40, 40, 40),
                                    category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(target=dpg.mvThemeCol_ButtonActive, value=(30, 30, 30),
                                    category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(target=dpg.mvThemeCol_WindowBg, value=(30, 30, 30), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(target=dpg.mvThemeCol_MenuBarBg, value=(33, 38, 99), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(target=dpg.mvThemeCol_Border, value=(0, 0, 0), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(target=dpg.mvThemeCol_BorderShadow, value=(0, 0, 0), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(target=dpg.mvThemeCol_SliderGrab, value=(25, 107, 52), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(target=dpg.mvThemeCol_SliderGrabActive, value=(44, 150, 79),
                                    category=dpg.mvThemeCat_Core)

                dpg.add_theme_style(target=dpg.mvNodeStyleVar_NodeCornerRounding, x=9, category=dpg.mvThemeCat_Nodes)
                dpg.add_theme_style(target=dpg.mvNodeStyleVar_NodePadding, x=11, y=10, category=dpg.mvThemeCat_Nodes)
                dpg.add_theme_style(target=dpg.mvNodeStyleVar_NodeBorderThickness, x=2, category=dpg.mvThemeCat_Nodes)
                dpg.add_theme_style(target=dpg.mvNodeStyleVar_PinQuadSideLength, x=8, category=dpg.mvThemeCat_Nodes)
                dpg.add_theme_style(target=dpg.mvNodeStyleVar_PinTriangleSideLength, x=8, category=dpg.mvThemeCat_Nodes)
                dpg.add_theme_style(target=dpg.mvNodeStyleVar_PinCircleRadius, x=4, category=dpg.mvThemeCat_Nodes)
                dpg.add_theme_style(target=dpg.mvNodeStyleVar_PinOffset, x=-1, category=dpg.mvThemeCat_Nodes)
                dpg.add_theme_style(target=dpg.mvNodeStyleVar_LinkThickness, x=2, category=dpg.mvThemeCat_Nodes)
                dpg.add_theme_style(target=dpg.mvNodeStyleVar_LinkLineSegmentsPerLength, x=2,
                                    category=dpg.mvThemeCat_Nodes)
                dpg.add_theme_style(target=dpg.mvNodesStyleVar_MiniMapPadding, x=1, y=1, category=dpg.mvThemeCat_Nodes)
                dpg.add_theme_style(target=dpg.mvNodeStyleVar_GridSpacing, x=40, y=40, category=dpg.mvThemeCat_Nodes)
                dpg.add_theme_color(target=dpg.mvNodeCol_NodeOutline, value=(0, 0, 0),
                                    category=dpg.mvThemeCat_Nodes)
                dpg.add_theme_color(target=dpg.mvNodeCol_TitleBar, value=(80, 40, 60), category=dpg.mvThemeCat_Nodes)
                dpg.add_theme_color(target=dpg.mvNodeCol_TitleBarHovered, value=(100, 60, 80),
                                    category=dpg.mvThemeCat_Nodes)
                dpg.add_theme_color(target=dpg.mvNodeCol_TitleBarSelected, value=(120, 80, 100),
                                    category=dpg.mvThemeCat_Nodes)
                dpg.add_theme_color(target=dpg.mvNodeCol_NodeBackground, value=(82, 82, 82),
                                    category=dpg.mvThemeCat_Nodes)
                dpg.add_theme_color(target=dpg.mvNodeCol_Pin, value=(252, 197, 119),
                                    category=dpg.mvThemeCat_Nodes)
                dpg.add_theme_color(target=dpg.mvNodeCol_PinHovered, value=(252, 186, 93),
                                    category=dpg.mvThemeCat_Nodes)
                dpg.add_theme_color(target=dpg.mvNodeCol_Link, value=(252, 197, 119),
                                    category=dpg.mvThemeCat_Nodes)
                dpg.add_theme_color(target=dpg.mvNodeCol_GridLine, value=(30, 30, 30, 255),
                                    category=dpg.mvThemeCat_Nodes)
                dpg.add_theme_color(target=dpg.mvNodeCol_GridBackground, value=(50, 50, 50, 255),
                                    category=dpg.mvThemeCat_Nodes)
                dpg.add_theme_color(target=dpg.mvNodesCol_MiniMapOutline, value=(0, 0, 0),
                                    category=dpg.mvThemeCat_Nodes)
                # dpg.add_theme_color(target=dpg.mvNodesCol_MiniMapCanvas, value=(0, 0, 0, 50),
                #                     category=dpg.mvThemeCat_Nodes)
                dpg.add_theme_color(target=dpg.mvNodesCol_MiniMapCanvasOutline, value=(0, 0, 0),
                                    category=dpg.mvThemeCat_Nodes)
                # dpg.add_theme_color(target=dpg.mvNodesCol_MiniMapBackground, value=(0, 0, 0, 120),
                #                     category=dpg.mvThemeCat_Nodes)
                # dpg.add_theme_color(target=dpg.mvNodesCol_MiniMapNodeBackground, value=(128, 128, 128, 50),
                #                     category=dpg.mvThemeCat_Nodes)

            with dpg.theme_component(dpg.mvMenu):
                dpg.add_theme_style(target=dpg.mvStyleVar_WindowPadding, x=12, y=12, category=dpg.mvThemeCat_Core)
                # dpg.add_theme_style(target=dpg.mvStyleVar_FramePadding, x=12, y=12, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(target=dpg.mvThemeCol_Border, value=(40, 136, 101), category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_ItemSpacing, x=15, y=15, category=dpg.mvThemeCat_Core)

            with dpg.theme_component(dpg.mvCombo):
                dpg.add_theme_style(target=dpg.mvStyleVar_FramePadding, x=6, y=6, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_FrameRounding, x=6, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_WindowPadding, x=14, y=14, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_PopupBorderSize, x=2, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_PopupRounding, x=10, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(target=dpg.mvThemeCol_Border, value=(40, 136, 101), category=dpg.mvThemeCat_Core)

            with dpg.theme_component(dpg.mvInputInt):
                dpg.add_theme_style(target=dpg.mvStyleVar_FramePadding, x=6, y=6, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_FrameRounding, x=6, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_WindowPadding, x=6, y=6, category=dpg.mvThemeCat_Core)

            with dpg.theme_component(dpg.mvInputIntMulti):
                dpg.add_theme_style(target=dpg.mvStyleVar_FramePadding, x=6, y=6, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_FrameRounding, x=6, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_WindowPadding, x=6, y=6, category=dpg.mvThemeCat_Core)

            with dpg.theme_component(dpg.mvInputFloatMulti):
                dpg.add_theme_style(target=dpg.mvStyleVar_FramePadding, x=6, y=6, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_FrameRounding, x=6, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_WindowPadding, x=6, y=6, category=dpg.mvThemeCat_Core)

            with dpg.theme_component(dpg.mvDragInt):
                dpg.add_theme_style(target=dpg.mvStyleVar_FramePadding, x=6, y=6, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_FrameRounding, x=6, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_WindowPadding, x=6, y=6, category=dpg.mvThemeCat_Core)

            with dpg.theme_component(dpg.mvDragIntMulti):
                dpg.add_theme_style(target=dpg.mvStyleVar_FramePadding, x=6, y=6, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_FrameRounding, x=6, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_WindowPadding, x=6, y=6, category=dpg.mvThemeCat_Core)

            with dpg.theme_component(dpg.mvDragFloat):
                dpg.add_theme_style(target=dpg.mvStyleVar_FramePadding, x=6, y=6, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_FrameRounding, x=6, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_WindowPadding, x=6, y=6, category=dpg.mvThemeCat_Core)

            with dpg.theme_component(dpg.mvDragFloatMulti):
                dpg.add_theme_style(target=dpg.mvStyleVar_FramePadding, x=6, y=6, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_FrameRounding, x=6, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_WindowPadding, x=6, y=6, category=dpg.mvThemeCat_Core)

            with dpg.theme_component(dpg.mvInputText):
                dpg.add_theme_style(target=dpg.mvStyleVar_FramePadding, x=6, y=6, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_FrameRounding, x=6, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_WindowPadding, x=6, y=6, category=dpg.mvThemeCat_Core)

            with dpg.theme_component(dpg.mvText):
                dpg.add_theme_style(target=dpg.mvStyleVar_FramePadding, x=6, y=6, category=dpg.mvThemeCat_Core)

            with dpg.theme_component(dpg.mvInputFloat):
                dpg.add_theme_style(target=dpg.mvStyleVar_FramePadding, x=6, y=6, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_FrameRounding, x=8, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_WindowPadding, x=6, y=6, category=dpg.mvThemeCat_Core)

            with dpg.theme_component(dpg.mvColorEdit):
                dpg.add_theme_style(target=dpg.mvStyleVar_FramePadding, x=6, y=6, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_FrameRounding, x=8, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_WindowPadding, x=6, y=6, category=dpg.mvThemeCat_Core)

            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_style(target=dpg.mvStyleVar_FramePadding, x=6, y=6, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_FrameRounding, x=9, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_WindowPadding, x=6, y=6, category=dpg.mvThemeCat_Core)

            with dpg.theme_component(dpg.mvCheckbox):
                dpg.add_theme_style(target=dpg.mvStyleVar_FramePadding, x=4, y=4, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(target=dpg.mvThemeCol_CheckMark, value=(201, 99, 30), category=dpg.mvThemeCat_Core)

            with dpg.theme_component(dpg.mvSliderInt):
                dpg.add_theme_style(target=dpg.mvStyleVar_FrameRounding, x=5, category=dpg.mvThemeCat_Core)

            with dpg.theme_component(dpg.mvSliderFloat):
                dpg.add_theme_style(target=dpg.mvStyleVar_FrameRounding, x=5, category=dpg.mvThemeCat_Core)

        return themeTag

    @staticmethod
    def createDialogTheme() -> int:
        with dpg.theme() as themeTag:
            with dpg.theme_component(item_type=dpg.mvAll):
                dpg.add_theme_style(target=dpg.mvStyleVar_WindowPadding, x=10, y=10, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_WindowRounding, x=7, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_FramePadding, x=7, y=7, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_FrameRounding, x=9, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_WindowBorderSize, x=2, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_CellPadding, x=3, y=7, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_ItemSpacing, x=7, y=7, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(target=dpg.mvStyleVar_ItemInnerSpacing, x=7, y=7, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(target=dpg.mvThemeCol_TitleBgActive, value=(89, 42, 67),
                                    category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(target=dpg.mvThemeCol_Border, value=(0, 0, 0),
                                    category=dpg.mvThemeCat_Core)
        return themeTag

    @staticmethod
    def addFonts() -> None:
        with dpg.font_registry():
            dpg.add_font(tag="JetBrains_mono_regular", file=Fonts.JetBrainsMonoRegular, size=17)
            dpg.add_font(tag="JetBrains_mono_medium", file=Fonts.JetBrainsMonoMedium, size=17)
        dpg.bind_font(font="JetBrains_mono_medium")
