from tkinter import LabelFrame, LEFT, NW, BOTH, Entry, X, Checkbutton, Button, filedialog as filedialog, BOTTOM

from backup_util.records import MetaRecord
from .ui_model import UIModel


class DestinationFrame(LabelFrame):
    def __init__(self, root, model: UIModel):
        super().__init__(root, text="Destination", pady=10, padx=10)
        self.pack(side=LEFT, anchor=NW, fill=BOTH, expand=True)
        self.model = model

        self.txt_dest = Entry(self, textvariable=self.model.var_dest)
        self.txt_dest.pack(fill=X)

        self.chk_wrap = Checkbutton(self, text="Create Date Wrapper", variable=self.model.var_wrap, onvalue=True,
                                    offvalue=False)
        self.chk_wrap.pack()

        self.btn_dest_browse = Button(self, text="Browse", command=self.set_dest)
        self.btn_dest_browse.pack()

        def manage():
            self.model.var_managed.set(True)

        self.btn_make_managed = Button(self, text="Manage This Folder", command=manage)
        self.btn_make_managed.pack(side=BOTTOM)

        self.model.var_managed.trace_add("write", self.managed_changed)

    def managed_changed(self, *args):
        val = self.model.var_managed.get()
        if val:
            self.chk_wrap.configure(state="disabled")
            self.btn_make_managed.configure(text="Already Managed", state="disabled")
        else:
            self.chk_wrap.configure(state="normal")
            self.btn_make_managed.configure(text="Manage This Folder", state="normal")

    def set_dest(self):
        dest = filedialog.askdirectory(title="Choose Destination")
        if dest is not None:
            self.model.var_dest.set(dest)
            self.model.var_managed.set(MetaRecord.is_managed(dest))
