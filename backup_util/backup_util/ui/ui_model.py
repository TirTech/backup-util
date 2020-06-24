from tkinter import StringVar, BooleanVar, Variable


class UIModel:
    def __init__(self):
        self.var_dest = StringVar()
        self.var_dest.set("")

        self.var_wrap = BooleanVar()
        self.var_wrap.set(True)

        self.lstvar_src = Variable()
        self.lstvar_src.set([])

        self.lstvar_exc = Variable()
        self.lstvar_exc.set([])

        self.var_managed = BooleanVar()
        self.var_managed.set(False)
