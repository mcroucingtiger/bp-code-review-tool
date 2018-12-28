from collections import namedtuple
"""List of All considerations used in reporting"""

Consideration = namedtuple('Consideration', 'value, max_score')
# General Considerations

# Process Considerations


# Object Considerations

CHECK_ACTIONS_USE_ATTACH = Consideration(value="Do all Actions use the Attach action?", max_score=10)

# Manual Considerations

