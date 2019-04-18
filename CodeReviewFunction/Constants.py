"""
This module should contain any process wide settings or constants consolidated into one file.
"""

# -------------------------------------------------- Object Settings

OBJECT_TYPES = {
    'base': 'Base Object',
    'surface auto base': 'Surface Automation Base Object',
    'wrapper': 'Wrapper Object'
}
"""The classification types for Blue Prism Objects."""

GLOBAL_NAV_STEPS = ['UIAMouseClick', 'UIAClickCentre', 'UIASendKeys',
                    'AAMouseClick', 'AAClickCentre', 'AASendKeys', 'TypeTextAlt', 'TypeText',
                    'MouseDoubleClick', 'MouseDoubleClickCentre', 'MouseClick', 'MouseClickCentre',
                    'RegionMouseClick', 'RegionMouseClickCentre', 'SendKeyEvents', 'SendKeys']
"""The step names for global Navigate stages."""

GLOBAL_READ_STEPS = ['ReadBitmap', 'GetText', 'ReadTextOCR', 'ReadChars']
"""The step names for Read stages that require the application window to be at the forefront of the desktop."""

WIN32_ELEMENT_TYPES = ['window', 'radiobutton', 'checkbox', 'button', 'edit', 'listbox', 'combobox',
                       'treeview', 'tabcontrol', 'trackbar', 'updown', 'datetimepicker',
                       'monthcalendarpicker', 'scrollbar', 'label', 'toolbar', 'datagrid', 'listview',
                       'datagridview']
"""Base types of elements that are spied in Win32."""

BLACKLIST_OBJECT_NAMES = [
    'Blue Prsim MAPIEx',
    'Calendars',
    'Data - OLEDB',
    'Data - SQL Server',
    'Email - POP3/SMTP',
    'MS Excel VBO',
    'MS Word VBO',
    'System - Active Directory',
    'Utility - Collection Manipulation',
    'Utility - Command Line Functions',
    'Utility - Date and Time Manipulation',
    'Utility - Encryption',
    'Utility - Environment',
    'Utility - File Management',
    'Utility - Foreground Locker',
    'Utility - General',
    'Utility - HTTP',
    'Utility - Image Manipulation',
    'Utility - Image Search',
    'Utility - JSON',
    'Utility - Locking',
    'Utility - Network',
    'Utility - Numeric Operations',
    'Utility - Strings',
    'Utility - WebServer',
    'Utility - Windows Explorer Functions',
    'Webservices - OAuth2.0',
    'Webservices - REST',
    'Utility - XML'
]

# -------------------------------------------------- Process Settings





