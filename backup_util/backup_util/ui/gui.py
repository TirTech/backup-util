from tkinter import PhotoImage, Frame, TOP, BOTH, Tk

from backup_util.icon import icon
from .action_frame import ActionFrame
from .destination_frame import DestinationFrame
from .exclusion_frame import ExclusionFrame
from .source_frame import SourceFrame
from .ui_model import UIModel


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
