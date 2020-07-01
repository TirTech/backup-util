from tkinter import BOTTOM, X, TOP, RIGHT, filedialog as filedialog, BOTH
from tkinter.ttk import Frame, Button, LabelFrame

from backup_util.managed import MetaRecord
from .ui_model import ManageUIModel


class ManageActionFrame(LabelFrame):
    def __init__(self, root, model: ManageUIModel):
        super().__init__(root, text="Actions")
        self.pack(side=BOTTOM, fill=X)
        self.model: ManageUIModel = model

        self.frm_btns = Frame(self, padding=5)
        self.frm_btns.pack(side=BOTTOM, fill=BOTH)

        self.btn_run = Button(self.frm_btns, text="Choose Backup Folder", command=self.choose_folder)
        self.btn_run.pack(side=RIGHT)

    def choose_folder(self):
        dest = filedialog.askdirectory(title="Choose Destination")
        if dest is not None and MetaRecord.is_managed(dest):
            self.model.var_metarecord.set(MetaRecord.load_from(dest))
