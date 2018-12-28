from collections import namedtuple
"""List of All considerations used in reporting"""

Consideration = namedtuple('Consideration', 'value, max_score')
# General Considerations
CHECK_EXCEPTION_DETAILS = Consideration(value="Do all Exception stages have an exception detail? ", max_score=10)
# Process Considerations


# Object Considerations
CHECK_OBJ_HAS_ATTACH = Consideration(value="Does the Business Object have an 'Attach' Action that reads "
                                           "the connected status before Attaching?", max_score=10)
CHECK_ACTIONS_USE_ATTACH = Consideration(value="Do all Actions use the Attach action?", max_score=10)

# Manual Considerations

