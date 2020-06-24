from tkinter import PhotoImage, Frame, TOP, BOTH, Tk

from icon import icon
from ui.action_frame import ActionFrame
from ui.destination_frame import DestinationFrame
from ui.exclusion_frame import ExclusionFrame
from ui.source_frame import SourceFrame
from ui.ui_model import UIModel


class GUI:
    def __init__(self):
        self.root = None

    def setup(self):
        self.root.title("Backup Utility")
        img = PhotoImage(data=icon)
        self.root.tk.call('wm', 'iconphoto', self.root._w, img)
        model = UIModel()

        frm_config = Frame(self.root, padx=10, pady=10)
        frm_config.pack(side=TOP, fill=BOTH, expand=True)

        SourceFrame(frm_config, model)
        ExclusionFrame(frm_config, model)
        DestinationFrame(frm_config, model)
        ActionFrame(self.root, model)

    def start(self):
        self.root = Tk()
        self.setup()
        self.root.mainloop()


_all_ = ["GUI"]
