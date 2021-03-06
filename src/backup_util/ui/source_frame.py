from tkinter import X, RIGHT, LEFT, filedialog as filedialog, NW, \
    BOTH, Listbox, SINGLE
from tkinter.ttk import Frame, Button, LabelFrame

from .ui_model import ConfigUIModel


class SourceFrame(LabelFrame):
    def __init__(self, root, model: ConfigUIModel):
        super().__init__(root, text="Sources", padding=10)
        self.pack(side=LEFT, anchor=NW, fill=BOTH, expand=True)
        self.model = model

        self.lstbx_src = Listbox(self, listvariable=self.model.lstvar_src, selectmode=SINGLE)
        self.lstbx_src.pack(fill=BOTH, expand=True)

        self.frm_src_btns = Frame(self, padding=5)
        self.frm_src_btns.pack(fill=X)

        self.btn_src_add = Button(self.frm_src_btns, text="Add", command=self.add_src)
        self.btn_src_add.pack(side=LEFT)
        self.btn_src_rm = Button(self.frm_src_btns, text="Remove", command=self.rm_src)
        self.btn_src_rm.pack(side=RIGHT)

    def add_src(self):
        src = filedialog.askdirectory(title="Choose Source")
        if src is not None:
            lst = list(self.model.lstvar_src.get())
            lst.append(src)
            self.model.lstvar_src.set(lst)

    def rm_src(self):
        if len(self.lstbx_src.curselection()) > 0:
            items = list(self.model.lstvar_src.get())
            for i in self.lstbx_src.curselection():
                del items[i]
            self.model.lstvar_src.set(items)
