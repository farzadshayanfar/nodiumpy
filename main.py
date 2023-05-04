import asyncio
import time

import cv2
import dearpygui.dearpygui as dpg

from Resources import AppIcon
from node_editor.editor import NodeEditor
from settings import AppSettings


def main():
    # initiating settings
    settings = AppSettings()

    # use opencv in optimized mode
    cv2.setUseOptimized(True)

    dpg.create_context()

    settings.addFonts()
    dpg.setup_dearpygui()

    dpg.create_viewport(title="NodiumPy",
                        small_icon=AppIcon,
                        large_icon=AppIcon,
                        width=settings.windowWidth,
                        height=settings.windowHeight,
                        vsync=False)
    
    menu_dict = {
        "Inputs": "inputs",
        "Adjustments": "adjustments",
        "Filters": "filters",
        "Viewers": "viewers",
        "Outputs": "outputs"
    }

    editor = NodeEditor(settings=settings,
                        menuDict=menu_dict,
                        nodeDir="./nodes")

    dpg.set_primary_window(window=editor.windowTag, value=True)
    dpg.bind_item_theme(item=editor.windowTag, theme=settings.createTheme())
    dpg.bind_theme(theme=settings.createDialogTheme())
    dpg.show_viewport()

    def asyncMain():
        editor.update()

    loop = asyncio.new_event_loop()
    loop.run_in_executor(None, asyncMain)

    while dpg.is_dearpygui_running():
        dpg.render_dearpygui_frame()
        time.sleep(0.033)

    editor.terminate()
    dpg.destroy_context()


if __name__ == '__main__':
    main()
