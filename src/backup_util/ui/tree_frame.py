from tkinter import X, LEFT, BOTH, TOP, N, END
from tkinter.ttk import Frame, Button, LabelFrame, Treeview

from backup_util.utils.tkutils import load_image
from backup_util.managed import MetaRecord
from .clean_dialog import CleanDialog
from .rebuild_dialog import RebuildDialog
from .ui_model import ManageUIModel


class TreeFrame(LabelFrame):
    def __init__(self, root, model: ManageUIModel):
        super().__init__(root, text="Records", padding=10)
        self.model = model
        self.packed = False

        self._edit_img = load_image("edit", width=16, color=(38, 158, 54))

        cols = ["timestamp"]
        # cols=["timestamp", "source", "hash"]

        self.tree = Treeview(self, padding=5, columns=cols)
        self.tree.heading("timestamp", text="Timestamp")
        # self.tree.heading("source", text="Data Source")
        # self.tree.heading("hash", text="Hash")
        self.tree.pack(fill=BOTH, expand=True)

        self.frm_src_btns = Frame(self, padding=5)
        self.frm_src_btns.pack(fill=X)

        def show_rebuilder():
            RebuildDialog.create_dialog(self.model.var_metarecord.get())

        self.btn_src_add = Button(self.frm_src_btns, text="Import Previous Backups", command=show_rebuilder)
        self.btn_src_add.pack(side=LEFT)

        def show_clean():
            CleanDialog.create_dialog(self.model.var_metarecord.get())

        self.btn_src_add = Button(self.frm_src_btns, text="Remove Redundant Files", command=show_clean)
        self.btn_src_add.pack(side=LEFT)

        self.model.var_metarecord.trace_add(self._metarecord_changed)

    def do_pack(self):
        if not self.packed:
            self.pack(side=TOP, anchor=N, fill=BOTH, expand=True)
            self.packed = True

    def do_unpack(self):
        if self.packed:
            self.pack_forget()
            self.packed = False

    def _metarecord_changed(self, var, oldval, newval):
        self.tree.delete(*self.tree.get_children())
        if newval is not None:
            self._setup_tree(newval)
            self.do_pack()
        else:
            self.do_unpack()

    def _setup_tree(self, mr: MetaRecord):
        for r in mr.records:
            val = self.tree.insert("", END, text=r.name, values=[r.timestamp])
            # self._load_record(mr.path, val)

    # def _load_record(self, path: str, parent):
    #     name = self.tree.item(parent, option='text')
    #     rec = Record.load_from(path, name)
    #     for f in rec.files:
    #         self.tree.insert(parent, END, text=f.file, values=["", f.source, f.hash])
