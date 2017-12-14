"""Porcupine's plugins.

Porcupine comes with many handy plugins, and you can read them to
get an idea of how everything works. You can find them like this:

    >>> import porcupine.plugins
    >>> porcupine.plugins.__path__
    ['/home/akuli/.config/porcupine/plugins',
     '/bla/bla/bla/porcupine/plugins']
    >>>

You can add your own plugins to the first directory and Porcupine's
default plugins are installed in the second directory.

Plugins are just Python files that Porcupine imports on startup, so
their names need to be valid module names. The files should import
porcupine and call porcupine.plugins.add_plugin(). You can read the
default plugins for examples.

Some notes about writing plugins:

  - If you don't like a default plugin you can disable that by creating
    an empty file with the same name in your own plugin directory.

  - Use the add keyword argument to bind() when binding widgets that
    Porcupine created. See the help, e.g. help('tkinter.Label.bind').
    This way other plugins can bind the same event too. If you need to
    return 'break' from a bind callback the all argument does nothing
    and you just need to hope for the best.

  - Sometimes multiple plugins need to bind something and return
    'break', or multiple plugins need to calculate the same thing in the
    bind() callback. Porcupine often uses lists of callbacks in these
    cases. For example, <<Modified>> needs to be handled in one place
    only so porcupine.textwidget.Text has an on_modified callback list.
    But it offers other handy callback lists too. For example, the
    statusbar needs to be updated when the cursor moves so there's an
    on_cursor_move callback list.

When you have added a plugin file, run Porcupine from a terminal,
command prompt or PowerShell so you'll see any errors messages that your
plugin might produce. Note that there's nothing wrong with running
multiple Porcupines at the same time, so if you are writing the plugin
in a Porcupine you don't need to restart that Porcupine at all.
"""
# TODO: update the docstring

import os

from rbtk import dirs

# simple hack to allow user-wide plugins
__path__.insert(0, os.path.join(dirs.configdir, 'plugins'))
