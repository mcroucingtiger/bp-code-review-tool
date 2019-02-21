# Object Settings
WARNING_STAGES_PER_PAGE = 15
"""Warning point for number of stages that an Action page should have."""

MAX_STAGES_PER_PAGE = 25
"""Maximum number of stages that an Action page should have."""

WARNING_IMAGE_WIDTH = 180
"""Warning pixel width of images stored in Data items."""

WARNING_IMAGE_HEIGHT = 180
"""Warning pixel height of images stored in Data items."""

MAX_IMAGE_WIDTH = 250
"""Maximum pixel width of images stored in Data items."""

MAX_IMAGE_HEIGHT = 250
"""Maximum pixel height of images stored in Data items."""

GLOBAL_NAV_STEPS = ['UIAMouseClick', 'UIAClickCentre', 'UIASendKeys',
                'AAMouseClick', 'AAClickCentre', 'AASendKeys', 'TypeTextAlt', 'TypeText',
                'MouseDoubleClick', 'MouseDoubleClickCentre', 'MouseClick', 'MouseClickCentre',
                'RegionMouseClick', 'RegionMouseClickCentre', 'SendKeyEvents', 'SendKeys']
"""The step names for global Navigate stages."""

GLOBAL_READ_STEPS = ['ReadBitmap', 'GetText', 'ReadTextOCR', 'ReadChars']
"""The step names for Read stages that require the application window to be at the forefront of the desktop."""

OBJECT_TYPES = {
    'base': 'Base Object',
    'surface auto base': 'Surface Automation Base Object',
    'wrapper': 'Wrapper Object'
}
"""The classification types for Blue Prism Objects."""

MIN_DETAIL_LENGTH = 10
"""Minimum length for an Exception detail."""

WARNING_DETAIL_LENGTH = 25
"""Warning length for an Exception detail."""

MAX_ELEMENT_COUNT = 250
"""Maximum number of spied elements an App Model can contain."""

WARNING_ELEMENT_COUNT = 130
"""Warning number of spied elements an App Model can contain."""

WARNING_ELEMENT_MINIMUM = 10
"""Warning if a flat App Model is found but there are less than this many elements."""
ACTIONS_PER_PAGE_WRAPPER_RATIO = 3
"Ratio of how many Action stages to a sub-sheet (i.e. per Action page) to suggest that the Object is a wrapper. "
WARNING_ELEMENT_TYPE_LENGTH = 16

def checker_test(expression: str):
    return re.sub('\[.*?\]', '[]', expression)
