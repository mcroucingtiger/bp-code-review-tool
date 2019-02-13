# Object Settings
WARNING_PAGE_STAGES = 15
"""Warning point for number of stages that an Action page should have."""

MAX_PAGE_STAGES = 25
"""Maximum number of stages that an Action page should have."""

MAX_WIDTH = 400
"""Maximum pixel width of images stored in Data items."""

MAX_HEIGHT = 400
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

WARNING_DETAIL_LENGTH = 25
