import functools
import logging
import traceback
import webbrowser

import pygments.styles
import pygments.token

import rbtk
from rbtk import _dialogs, dirs, filetypes, menubar, settings, tabs, utils

log = logging.getLogger(__name__)

_main_window = None
_tab_manager = None

def init(main_window, tab_manager):
	global _main_window
	global _tab_manager

	assert _main_window is None and _tab_manager is None
	_main_window = main_window
	_tab_manager = tab_manager

def get_main_window():

	if _main_window is None:
		raise RuntimeError("RBTK is not running")

	return _main_window

def get_tab_manager():

	if _tab_manager is None:
		raise RuntimeError("RBTK is not running")

	return _tab_manager

def quit():

	for tab in _tab_manager.tabs:
		if not tab.can_be_closed():
			return

	_main_window.event_generate('<<RBTKQuit>>')

	for tab in _tab_manager.tabs.copy():
		_tab_manager.close_tab(tab)

	_main_window.destroy()

# CHECK FROM HERE

def setup_actions():
    def new_file():
        _tab_manager.add_tab(tabs.FileTab(_tab_manager))

    def open_files():
        for path in _dialogs.open_files():
            try:
                tab = tabs.FileTab.open_file(_tab_manager, path)
            except (UnicodeError, OSError) as e:
                log.exception("opening '%s' failed", path)
                utils.errordialog(type(e).__name__, "Opening failed!",
                                  traceback.format_exc())
                continue

            _tab_manager.add_tab(tab)

    def close_current_tab():
        if _tab_manager.current_tab.can_be_closed():
            _tab_manager.close_tab(_tab_manager.current_tab)

    add_action(new_file, "File/New File", ("Ctrl+N", '<Control-n>'))
    add_action(open_files, "File/Open", ("Ctrl+O", '<Control-o>'))
    add_action((lambda: _tab_manager.current_tab.save()),
               "File/Save", ("Ctrl+S", '<Control-s>'), tabtypes=[tabs.FileTab])
    add_action((lambda: _tab_manager.current_tab.save_as()),
               "File/Save As...", ("Ctrl+Shift+S", '<Control-S>'),
               tabtypes=[tabs.FileTab])
    menubar.get_menu("File").add_separator()

    # TODO: disable File/Quit when there are tabs, it's too easy to hit
    # Ctrl+Q accidentally
    add_action(close_current_tab, "File/Close", ("Ctrl+W", '<Control-w>'),
               tabtypes=[tabs.Tab])
    add_action(quit, "File/Quit", ("Ctrl+Q", '<Control-q>'))

    def textmethod(attribute):
        def result():
            textwidget = _tab_manager.current_tab.textwidget
            method = getattr(textwidget, attribute)
            method()
        return result

    # FIXME: bind these in a text widget only, not globally
    add_action(textmethod('undo'), "Edit/Undo", ("Ctrl+Z", '<Control-z>'),
               tabtypes=[tabs.FileTab])
    add_action(textmethod('redo'), "Edit/Redo", ("Ctrl+Y", '<Control-y>'),
               tabtypes=[tabs.FileTab])
    add_action(textmethod('cut'), "Edit/Cut", ("Ctrl+X", '<Control-x>'),
               tabtypes=[tabs.FileTab])
    add_action(textmethod('copy'), "Edit/Copy", ("Ctrl+C", '<Control-c>'),
               tabtypes=[tabs.FileTab])
    add_action(textmethod('paste'), "Edit/Paste", ("Ctrl+V", '<Control-v>'),
               tabtypes=[tabs.FileTab])
    add_action(textmethod('select_all'), "Edit/Select All",
               ("Ctrl+A", '<Control-a>'), tabtypes=[tabs.FileTab])
    menubar.get_menu("Edit").add_separator()

    # FIXME: this separator thing is a mess :(
    menubar.get_menu("Edit").add_separator()
    add_action(
        functools.partial(settings.show_dialog, rbtk.get_main_window()),
        "Edit/RBTK Settings...")

    # the font size stuff are bound by the textwidget itself, that's why
    # there are Nones everywhere
    add_action(
        (lambda: _tab_manager.current_tab.textwidget.on_wheel('up')),
        "View/Bigger Font", ("Ctrl+Plus", None), tabtypes=[tabs.FileTab])
    add_action(
        (lambda: _tab_manager.current_tab.textwidget.on_wheel('down')),
        "View/Smaller Font", ("Ctrl+Minus", None), tabtypes=[tabs.FileTab])
    add_action(
        (lambda: _tab_manager.current_tab.textwidget.on_wheel('reset')),
        "View/Reset Font Size", ("Ctrl+Zero", None), tabtypes=[tabs.FileTab])
    menubar.get_menu("View").add_separator()

    def add_link(menupath, url):
        add_action(functools.partial(webbrowser.open, url), menupath)

    # TODO: an about dialog that shows porcupine version, Python version
    #       and where porcupine is installed
    # TODO: porcupine starring button

    ## FIX LINKS
    add_link("Help/Free help chat",
             "http://webchat.freenode.net/?channels=%23%23learnpython")
    add_link("Help/My Python tutorial",
             "https://github.com/Akuli/python-tutorial/blob/master/README.md")
    add_link("Help/Official Python documentation",
             "https://docs.python.org/")
    menubar.get_menu("Help").add_separator()
    add_link("Help/Porcupine Wiki",
             "https://github.com/Akuli/porcupine/wiki")
    add_link("Help/Report a problem or request a feature",
             "https://github.com/Akuli/porcupine/issues/new")
    add_link("Help/Read Porcupine's code on GitHub",
             "https://github.com/Akuli/porcupine/tree/master/porcupine")

    # TODO: loading the styles takes a long time on startup... try to
    # make it asynchronous without writing too complicated code?
    config = settings.get_section('General')
    for name in sorted(pygments.styles.get_all_styles()):
        if name.islower():
            label = name.replace('-', ' ').replace('_', ' ').title()
        else:
            label = name

        options = {
            'label': label, 'value': name,
            'variable': config.get_var('pygments_style'),
        }

        style = pygments.styles.get_style_by_name(name)
        bg = style.background_color

        # styles have a style_for_token() method, but only iterating
        # is documented :( http://pygments.org/docs/formatterdevelopment/
        # i'm using iter() to make sure that dict() really treats
        # the style as an iterable of pairs instead of some other
        # metaprogramming fanciness
        fg = None
        style_infos = dict(iter(style))
        for token in [pygments.token.String, pygments.token.Text]:
            if style_infos[token]['color'] is not None:
                fg = '#' + style_infos[token]['color']
                break
        if fg is None:
            # do like textwidget.ThemedText._set_style does
            fg = (getattr(style, 'default_style', '') or
                  utils.invert_color(bg))

        options['foreground'] = options['activebackground'] = fg
        options['background'] = options['activeforeground'] = bg

       # menubar.get_menu("Color Themes").add_radiobutton(**options)

def add_action(callback, menupath=None, keyboard_shortcut=(None, None),
               tabtypes=(None, tabs.Tab)):
    """Add a keyboard binding and/or a menu item.

    If *menupath* is given, it will be split by the last ``/``. The
    first part will be used to get a menu with
    :meth:`porcupine.menubar.get_menu`, and the end will be used as the
    text of the menu item.

    Keyboard shortcuts can be added too. If given, *keyboard_shortcut*
    should be a two-tuple of a user-readable string and a tkinter
    keyboard binding; for example, ``('Ctrl+S', '<Control-s>')``.

    If defined, the *tabtypes* argument should be an iterable of
    :class:`porcupine.tabs.Tab` subclasses that item can work
    with. If you want to allow no tabs at all, add None to this list.
    The menuitem will be disabled and the binding won't do anything when
    the current tab is not of a compatible type.
    """
    tabtypes = tuple((
        # isinstance(None, type(None)) is True
        type(None) if cls is None else cls
        for cls in tabtypes
    ))
    accelerator, binding = keyboard_shortcut

    if menupath is not None:
        menupath, menulabel = menupath.rsplit('/', 1)
        menu = menubar.get_menu(menupath)
        menu.add_command(label=menulabel, command=callback,
                         accelerator=accelerator)
        menuindex = menu.index('end')

        def tab_changed(event):
            enable = isinstance(_tab_manager.current_tab, tabtypes)
            menu.entryconfig(
                menuindex, state=('normal' if enable else 'disabled'))

        tab_changed(_tab_manager.current_tab)
        _tab_manager.bind('<<CurrentTabChanged>>', tab_changed, add=True)

    if binding is not None:
        # TODO: check if it's already bound
        def bind_callback(event):
            if isinstance(_tab_manager.current_tab, tabtypes):
                callback()
                # try to allow binding keys that are used for other
                # things by default
                return 'break'

        _main_window.bind(binding, bind_callback)


