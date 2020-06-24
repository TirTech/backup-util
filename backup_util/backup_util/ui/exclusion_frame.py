from tkinter import LabelFrame, LEFT, NW, BOTH, Listbox, SINGLE, Frame, X, Button, RIGHT, \
    simpledialog as simpledialog
from .ui_model import UIModel


class ExclusionFrame(LabelFrame):
    def __init__(self, root, model: UIModel):
        super().__init__(root, text="Exclusions", pady=10, padx=10)
        self.pack(side=LEFT, anchor=NW, fill=BOTH, expand=True)
        self.model = model

        self.lstbx_exc = Listbox(self, listvariable=self.model.lstvar_exc, selectmode=SINGLE)
        self.lstbx_exc.pack(fill=BOTH, expand=True)

        self.frm_exc_btns = Frame(self, pady=5, padx=5)
        self.frm_exc_btns.pack(fill=X)

        self.btn_exc_add = Button(self.frm_exc_btns, text="Add", command=self.add_exc)
        self.btn_exc_add.pack(side=LEFT)
        self.btn_exc_rm = Button(self.frm_exc_btns, text="Remove", command=self.rm_exc)
        self.btn_exc_rm.pack(side=RIGHT)

    def add_exc(self):
        exc = simpledialog.askstring("Add Exclusion", "Enter glob format expression to exclude:")
        if exc is not None:
            lst = list(self.model.lstvar_exc.get())
            lst.append(exc)
            self.model.lstvar_exc.set(lst)

    def rm_exc(self):
        if len(self.lstbx_exc.curselection()) > 0:
            items = list(self.model.lstvar_exc.get())
            for i in self.lstbx_exc.curselection():
                del items[i]
            self.model.lstvar_exc.set(items)
