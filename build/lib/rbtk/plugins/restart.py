# TODO: remember which split pane each tab was in
import os
import pickle
import pkgutil

from rbtk import dirs, get_main_window, get_tab_manager
from rbtk.plugins import __path__ as plugin_paths

# setup() must be called after setting up everything else
setup_after = [
    name for finder, name, ispkg in pkgutil.iter_modules(plugin_paths)
    if 'rbtk.plugins.' + name != __name__
]

# TODO: figure out which file extension is best for pickled files
STATE_FILE = os.path.join(dirs.cachedir, 'restart_state.pickle')


def save_states(junk_event):
    states = []
    for tab in get_tab_manager().tabs:
        state = tab.get_state()
        if state is not None:
            states.append((type(tab), state))

    with open(STATE_FILE, 'wb') as file:
        pickle.dump(states, file)


def setup():
    # this must run even if loading tabs from states below fails
    get_main_window().bind('<<RBTKQuit>>', save_states, add=True)

    try:
        with open(STATE_FILE, 'rb') as file:
            states = pickle.load(file)
    except FileNotFoundError:
        states = []

    for tab_class, state in states:
        tab = tab_class.from_state(get_tab_manager(), state)
        get_tab_manager().add_tab(tab)
