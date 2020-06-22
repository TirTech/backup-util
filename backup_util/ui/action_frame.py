import queue
from queue import Queue
from tkinter import Frame, BOTTOM, X, TOP, StringVar, Label, W, DoubleVar, ttk as ttk, Button, RIGHT, BooleanVar, \
    Checkbutton, LEFT, filedialog as filedialog
from typing import Union

from ManagedBackup import ManagedBackup
from Backup import Backup, BackupUpdate
from exception.ValidationException import ValidationException
from records import MetaRecord
from ui.ui_model import UIModel


class ActionFrame(Frame):
    def __init__(self, root, model: UIModel):
        super().__init__(root, padx=10, pady=10)
        self.pack(side=BOTTOM, fill=X)
        self.model = model

        self.frm_prog = Frame(self, padx=10, pady=10)
        self.frm_prog.pack(side=TOP, fill=X, expand=True)

        self.var_stat = StringVar()
        self.var_stat.set("Ready")
        self.lbl_stat = Label(self.frm_prog, textvariable=self.var_stat)
        self.lbl_stat.pack(anchor=W)

        self.var_statmin = StringVar()
        self.var_statmin.set("|> ")
        self.lbl_statmin = Label(self.frm_prog, textvariable=self.var_statmin)
        self.lbl_statmin.pack(anchor=W)

        self.var_prog = DoubleVar()
        self.var_prog.set(0)
        self.prog_stat = ttk.Progressbar(self.frm_prog, maximum=100, variable=self.var_prog)
        self.prog_stat.pack(fill=X, anchor=W)

        def do_backup():
            self.run_backup(
                list(self.model.lstvar_src.get()),
                list(self.model.lstvar_exc.get()),
                self.model.var_dest.get(),
                self.model.var_managed.get())

        self.frm_btns = Frame(self, padx=10, pady=10)
        self.frm_btns.pack(side=TOP, fill=X)

        self.btn_run = Button(self.frm_btns, text="Run", command=do_backup)
        self.btn_run.pack(side=RIGHT)

        self.var_dry = BooleanVar()
        self.var_dry.set(True)
        self.chk_dry = Checkbutton(self.frm_btns, text="Dry Run", variable=self.var_dry, onvalue=True, offvalue=False)
        self.chk_dry.pack(side=RIGHT)

        self.btn_run = Button(self.frm_btns, text="Load", command=self.load_backup)
        self.btn_run.pack(side=LEFT)

        self.btn_run = Button(self.frm_btns, text="Save", command=self.save_backup)
        self.btn_run.pack(side=LEFT)

        self.bk: Union[Backup, None] = None

    def load_backup(self):
        file: str = filedialog.askopenfilename(title="Save Configuration",
                                               filetypes=(("JSON files", "*.json"), ("All Files", "*.*")))
        if file is not None and len(file.strip()) > 0:
            src, exc, dest, dry, wrap = Backup.load_from_json(file)
            self.model.lstvar_src.set(src)
            self.model.lstvar_exc.set(exc)
            self.model.var_dest.set(dest)
            self.var_dry.set(dry)
            self.model.var_wrap.set(wrap)
            self.model.var_managed.set(MetaRecord.is_managed(dest))

    def save_backup(self):
        file: str = filedialog.asksaveasfilename(title="Save Configuration",
                                                 filetypes=(("JSON files", "*.json"), ("All Files", "*.*")),
                                                 defaultextension=".json")
        if file is not None and len(file.strip()) > 0:
            Backup.save_to_json(file,
                                self.model.lstvar_src.get(),
                                self.model.lstvar_exc.get(),
                                self.model.var_dest.get(),
                                self.var_dry.get(),
                                self.model.var_wrap.get())

    def run_backup(self, sources: list, exceptions: list, destination: str, managed: bool):
        self.var_prog.set(0)
        self.var_stat.set("Ready")
        self.bk = \
            Backup(dry_run=self.var_dry.get(), use_wrapper=self.model.var_wrap.get()) if not managed else \
            ManagedBackup(dry_run=self.var_dry.get())
        for s in sources:
            self.bk.add_source(s)
        for e in exceptions:
            self.bk.add_exception(e)
        self.bk.set_destination(destination)
        try:
            data_queue = self.bk.execute()
            self.listen_for_result(data_queue)
        except ValidationException as e:
            self.var_stat.set(e.args[0])

    def listen_for_result(self, data_queue: Queue):
        try:
            while not data_queue.empty():
                res: BackupUpdate = data_queue.get_nowait()
                if not res.is_minor():
                    self.var_stat.set(f"[{res.get_completion()}%] {res.message}")
                    self.var_prog.set(res.get_completion())
                else:
                    self.var_statmin.set(f"|> {res.message}")
        except queue.Empty:
            pass
        finally:
            if self.bk.is_running():
                self.after(100, lambda: self.listen_for_result(data_queue))
            else:
                self.bk = None
