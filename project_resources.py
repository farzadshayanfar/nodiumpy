from importlib.abc import Traversable
from importlib.resources import files

import res.icons
import res.fonts

icons_paths: Traversable = files(package=res.icons)
AppIconPath: str = str(icons_paths.joinpath("app_icon.ico"))

fonts_paths: Traversable = files(package=res.fonts)
JetBrainsMonoRegularPath: str = str(fonts_paths.joinpath("JetBrainsMono-Regular.ttf"))
JetBrainsMonoMediumPath: str = str(fonts_paths.joinpath("JetBrainsMono-Medium.ttf"))
