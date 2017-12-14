"""RBTK is a simple rule-based modeling editor. 

"""

version_info = (0, 0, 1)        # this is updated with bump.py
__version__ = '%d.%d.%d' % version_info
__author__ = 'Cihan Kaya'
__copyright__ = 'Copyright (c) 2017 RuleWorld'
#__license__ = 'MIT'

from rbtk._session import (quit, add_action,
                                get_main_window, get_tab_manager)
