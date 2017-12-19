import platform
import subprocess

import rbtk
from rbtk import tabs, utils


def run_autopep8(code):
    try:
        import autopep8     # noqa
    except ImportError:
        # this command is wrong in some cases, but most of the time
        # it's ok
        if platform.system() == 'Windows':
            command = "py -m pip install autopep8"
            app = 'command prompt or PowerShell'
        else:
            command = "python3 -m pip install --user autopep8"
            app = 'terminal'

        utils.errordialog(
            "Cannot find autopep8",
            "Looks like autopep8 is not installed.\n" +
            "You can install it by running this command on a %s:" % app,
            command)
        return None

    # autopep8's main() does some weird signal stuff, so we'll run it in
    # a subprocess just to make sure that the porcupine process is ok
    command = [utils.python_executable, '-m', 'autopep8', '-']
    process = subprocess.Popen(
        command, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (output, errors) = process.communicate(code.encode('utf-8'))

    if process.returncode != 0:
        utils.errordialog(
            "Running autopep8 failed",
            "autopep8 exited with status code %r." % process.returncode,
            errors.decode('utf-8', errors='replace'))
        return None

    return output.decode('utf-8')


def on_click():
    widget = rbtk.get_tab_manager().current_tab.textwidget
    before = widget.get('1.0', 'end - 1 char')
    after = run_autopep8(before)
    if after is None:
        # error
        return

    if before != after:
        widget['autoseparators'] = False
        widget.delete('1.0', 'end - 1 char')
        widget.insert('1.0', after)
        widget.edit_separator()
        widget['autoseparators'] = True


#def setup():
#    rbtk.add_action(on_click, "Tools/autopep8", tabtypes=[tabs.FileTab])
