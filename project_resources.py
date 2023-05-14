from importlib.resources import path

import res.Fonts
import res.Icons

AppIcon: str = str(path(package=res.Icons, resource="appIcon.ico").args[0])


class Fonts:
    JetBrainsMonoRegular: str = str(path(package=res.Fonts, resource="JetBrainsMono-Regular.ttf").args[0])
    JetBrainsMonoMedium: str = str(path(package=res.Fonts, resource="JetBrainsMono-Medium.ttf").args[0])
