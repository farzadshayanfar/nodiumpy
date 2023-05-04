from importlib.resources import path

import ResourcesPackage.Fonts
import ResourcesPackage.Icons

AppIcon: str = str(path(package=ResourcesPackage.Icons, resource="appIcon.ico").args[0])

class Fonts:
    JetBrainsMonoRegular: str = str(path(package=ResourcesPackage.Fonts, resource="JetBrainsMono-Regular.ttf").args[0])
    JetBrainsMonoMedium: str = str(path(package=ResourcesPackage.Fonts, resource="JetBrainsMono-Medium.ttf").args[0])
