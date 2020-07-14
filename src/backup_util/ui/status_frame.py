from tkinter import StringVar, W, DoubleVar, X
from tkinter.ttk import Frame, Label, Progressbar


class StatusFrame(Frame):
    def __init__(self, root):
        super().__init__(root, padding=10)
        self.var_stat = StringVar()
        self.var_stat.set("Ready")
        self.lbl_stat = Label(self, textvariable=self.var_stat)
        self.lbl_stat.pack(anchor=W)

        self.var_statmin = StringVar()
        self.var_statmin.set("|> ")
        self.lbl_statmin = Label(self, textvariable=self.var_statmin)
        self.lbl_statmin.pack(anchor=W)

        self.var_prog = DoubleVar()
        self.var_prog.set(0)
        self.prog_stat = Progressbar(self, maximum=100, variable=self.var_prog)
        self.prog_stat.pack(fill=X, anchor=W)

    def set_minor(self, message):
        self.var_statmin.set(message)

    def set_major(self, message):
        self.var_stat.set(message)

    def set_progress(self, progress):
        self.var_prog.set(progress)
