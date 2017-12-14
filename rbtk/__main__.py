"""Run Porcupine."""

import argparse
import logging
import os
import platform
from queue import Empty         # queue is a handy variable name
import sys
import tkinter

import rbtk
from rbtk import (_ipc, _logs, _pluginloader, _session,
                       dirs, filetypes, menubar, settings, tabs, utils)

log = logging.getLogger(__name__)

def _iter_queue(queue):
    while True:
        try:
            yield queue.get(block=False)
        except Empty:
            break


def open_file(path, content, tabmanager):
    if (path, content) != (None, None):
        tabmanager.add_tab(tabs.FileTab(tabmanager, content, path))


def queue_opener(queue, main_window, tabmanager):
    gonna_focus = False
    for path, content in _iter_queue(queue):
        # if porcupine is running and the user runs it again without any
        # arguments, then path and content are None and we just focus
        # the editor window
        gonna_focus = True
        open_file(path, content, tabmanager)

    if gonna_focus:
        if main_window.tk.call('tk', 'windowingsystem') == 'win32':
            main_window.deiconify()
        else:
            # this isn't as easy as you might think it is... focus_force
            # focuses the window but doesn't move it to the front, and
            # the -topmost wm attribute only works for lifting the
            # window temporarily
            # if you know how to do this without flashing the window
            # like this then please let me know
            geometry = main_window.geometry()
            main_window.withdraw()
            main_window.deiconify()
            main_window.geometry(geometry)

    main_window.after(200, queue_opener, queue, main_window, tabmanager)


# these actions are based on argparse's source code

class _PrintPlugindirAction(argparse.Action):

    def __init__(self, option_strings, dest=argparse.SUPPRESS,
                 default=argparse.SUPPRESS, help=None):
        super().__init__(option_strings=option_strings, dest=dest,
                         default=default, nargs=0, help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        print("You can install plugins here:\n\n    %s\n"
              % rbtk.plugins.__path__[0])
        parser.exit()


# "porcupine -n a b c -n" works, but unfortunately "porcupine a -n b" doesn't
class _ExtendAction(argparse.Action):

    def __init__(self, option_strings, dest, nargs=None, const=None,
                 default=None, type=None, choices=None, required=False,
                 help=None, metavar=None):
        assert nargs != 0 and (const is None or nargs == argparse.OPTIONAL)
        super().__init__(option_strings=option_strings, dest=dest, nargs=nargs,
                         const=const, default=default, type=type,
                         choices=choices, required=required, help=help,
                         metavar=metavar)

    def __call__(self, parser, namespace, values, option_string=None):
        if getattr(namespace, self.dest) is None:
            setattr(namespace, self.dest, [])
        getattr(namespace, self.dest).extend(values)


_EPILOG = r"""
Examples:
  %(prog)s                    # run Porcupine normally
  %(prog)s file1.py file2.js  # open the given files on startup
  %(prog)s -nnn               # create 3 new files
  %(prog)s --no-plugins       # understand the power of plugins
  %(prog)s --verbose          # produce lots of nerdy output
"""


def main():
    parser = argparse.ArgumentParser(
        prog=('%s -m rbtk' % utils.short_python_command),
        epilog=_EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument(
        '-v', '--version', action='version',
        version=("RBTK %s" % rbtk.__version__),
        help="display the RBTK version number and exit")
    parser.add_argument(
        '--print-plugindir', action=_PrintPlugindirAction,
        help="find out where to install custom plugins")
    parser.add_argument(
        'files', metavar='FILES', action=_ExtendAction,
        nargs=argparse.ZERO_OR_MORE, type=argparse.FileType("r"),
        help="open these files when RBTK starts, - means stdin")
    parser.add_argument(
        '-n', '--new-file', dest='files', action='append_const', const=None,
        help='create a "New File" tab; may be specified multiple times')

    plugingroup = parser.add_mutually_exclusive_group()
    plugingroup.add_argument(
        '--no-plugins', action='store_false', dest='yes_plugins',
        help=("don't load the plugins, this is useful for "
              "understanding how much can be done with plugins"))
    plugingroup.add_argument(
        '--shuffle-plugins', action='store_true',
        help=("respect setup_before and setup_after, but otherwise setup the "
              "plugins in a random order instead of sorting by name "
              "alphabetically"))

    loggroup = parser.add_mutually_exclusive_group()
    loggroup.add_argument(
        '--logfile', type=argparse.FileType('w'),
        help=("write information about what Porcupine is doing to this file, "
              "defaults to a .txt file in %s" % dirs.cachedir))
    loggroup.add_argument(
        '--verbose', dest='logfile', action='store_const', const=sys.stderr,
        help="use stderr as the log file")

    args = parser.parse_args()

    filelist = []
    for file in args.files:
        if file is sys.stdin:
            # don't close stdin so it's possible to do this:
            #
            #   $ porcupine - -
            #   bla bla bla
            #   ^D
            #   bla bla
            #   ^D
            filelist.append((None, file.read()))
        elif file is None:
            # -n or --new-file was used
            filelist.append((None, ''))
        else:
            with file:
                filelist.append((os.path.abspath(file.name), file.read()))

    try:
        if filelist:
            _ipc.send(filelist)
            print("The", ("file" if len(filelist) == 1 else "files"),
                  "will be opened in the already running RBTK.")
        else:
            # see queue_opener()
            _ipc.send([(None, None)])
            print("RBTK is already running.")
        return
    except ConnectionRefusedError:
        # not running yet, become the Porcupine that other Porcupines
        # connect to
        pass

    dirs.makedirs()
    _logs.setup(args.logfile)
    log.info("starting RBTK %s on %s", rbtk.__version__,
             platform.platform().replace('-', ' '))
    log.info("running on Python %d.%d.%d from %s",
             *(list(sys.version_info[:3]) + [sys.executable]))

    root = tkinter.Tk()
    root.title("RBTK")
    root.protocol('WM_DELETE_WINDOW', _session.quit)

    filetypes.init()
    utils._init_images()
    root['menu'] = menubar._init()

    tabmanager = tabs.TabManager(root)
    tabmanager.pack(fill='both', expand=True)
    for binding, callback in tabmanager.bindings:
        root.bind(binding, callback, add=True)

    _session.init(root, tabmanager)
    _session.setup_actions()

    if args.yes_plugins:
        _pluginloader.load(shuffle=args.shuffle_plugins)

    # see queue_opener()
    for path, content in filelist:
        open_file(path, content, tabmanager)

    # the user can change the settings only if we get here, so there's
    # no need to wrap the whole thing in try/with/finally/whatever
    with _ipc.session() as queue:
        root.after_idle(queue_opener, queue, root, tabmanager)
        try:
            root.mainloop()
        finally:
            settings.save()

    log.info("exiting RBTK successfully")


if __name__ == '__main__':
    main()
