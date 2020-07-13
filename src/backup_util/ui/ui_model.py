from tkinter import StringVar, BooleanVar, Variable

from backup_util.utils.tkutils import WatchedVariable


class ConfigUIModel:
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


class ManageUIModel:
    def __init__(self):
        self.var_metarecord: WatchedVariable = WatchedVariable()
