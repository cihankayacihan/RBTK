from tkinter import ttk

from rbtk import get_tab_manager, utils

# i have experimented with a logging handler that displays logging
# messages in the label, but it's not as good idea as it sounds like,
# not all INFO messages are something that users should see all the time


# this widget is kind of weird
class LabelWithEmptySpaceAtLeft(ttk.Label):

    def __init__(self, master):
        self._spacer = ttk.Frame(master)
        self._spacer.pack(side='left', expand=True)
        super().__init__(master)
        self.pack(side='left')

    def destroy(self):
        self._spacer.destroy()
        super().destroy()


class StatusBar(ttk.Frame):

    def __init__(self, master, tab):
        super().__init__(master)
        self.tab = tab
        # one label for each tab-separated thing
        self.labels = [ttk.Label(self)]
        self.labels[0].pack(side='left')

        tab.bind('<<StatusChanged>>', self.do_update, add=True)
        self.do_update()

    # this is do_update() because tkinter has a method called update()
    def do_update(self, junk=None):
        parts = self.tab.status.split('\t')

        # there's always at least one part, the label added in
        # __init__ is not destroyed here
        while len(self.labels) > len(parts):
            self.labels.pop().destroy()
        while len(self.labels) < len(parts):
            self.labels.append(LabelWithEmptySpaceAtLeft(self))

        for label, text in zip(self.labels, parts):
            label['text'] = text


def on_new_tab(event):
    tab = event.data_widget
    StatusBar(tab.bottom_frame, tab).pack(side='bottom', fill='x')


def setup():
    utils.bind_with_data(get_tab_manager(), '<<NewTab>>', on_new_tab, add=True)
