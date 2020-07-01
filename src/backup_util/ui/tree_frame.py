from tkinter import X, LEFT, BOTH, TOP, N, END, PhotoImage
from tkinter.ttk import Frame, Button, LabelFrame, Treeview

from backup_util.managed import MetaRecord, Record
from .rebuild_dialog import RebuildDialog
from .ui_model import ManageUIModel
from backup_util.Backup import ThrowingThread
from backup_util import utils


class TreeFrame(LabelFrame):
    def __init__(self, root, model: ManageUIModel):
        super().__init__(root, text="Records", padding=10)
        self.pack(side=TOP, anchor=N, fill=BOTH, expand=True)
        self.model = model

        self._edit_img = utils.load_image("edit", width=16, color=(38, 158, 54))

        self.tree = Treeview(self, padding=5, columns=["timestamp", "source", "hash"])
        self.tree.heading("timestamp", text="Timestamp")
        self.tree.heading("source", text="Data Source")
        self.tree.heading("hash", text="Hash")
        self.tree.pack(fill=BOTH, expand=True)

        self.frm_src_btns = Frame(self, padding=5)
        self.frm_src_btns.pack(fill=X)

        def show_rebuilder():
            RebuildDialog.create_dialog(self.model.var_metarecord.get())

        self.btn_src_add = Button(self.frm_src_btns, text="Import Previous Backups", command=show_rebuilder)
        self.btn_src_add.pack(side=LEFT)

        self.model.var_metarecord.trace_add(self._metarecord_changed)

    def _metarecord_changed(self, var, oldval, newval):
        self.tree.delete(*self.tree.get_children())
        if newval is not None:
            self._setup_tree(newval)

    def _setup_tree(self, mr: MetaRecord):
        for r in mr.records:
            self.tree.insert("", END, text=r.name, values=[r.timestamp])
        self.thread = ThrowingThread(target=self._load_records_background, args=[mr])
        self.thread.start()

    def _load_records_background(self, mr: MetaRecord):
        for c in self.tree.get_children():
            name = self.tree.item(c, option='text')
            rec = Record.load_from(mr.path, name)
            for f in rec.files:
                self.tree.insert(c, END, text=f.file, values=["", f.source, f.hash], image=self._edit_img)
