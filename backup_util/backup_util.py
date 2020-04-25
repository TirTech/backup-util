import base64
import queue
from queue import Queue
from typing import Union

from Backup import Backup, BackupUpdate
from tkinter import *
import tkinter.ttk as ttk
import tkinter.filedialog as filedialog
import tkinter.simpledialog as simpledialog
import tkinter.font as tkfont

from exception.ValidationException import ValidationException
from icon import icon


class SourceFrame(LabelFrame):
    def __init__(self, root):
        super().__init__(root, text="Sources", pady=10, padx=10)
        self.pack(side=LEFT, anchor=NW, fill=BOTH, expand=True)

        self.lstvar_src = Variable()
        self.lstvar_src.set([])

        self.lstbx_src = Listbox(self, listvariable=self.lstvar_src, selectmode=SINGLE)
        self.lstbx_src.pack(fill=BOTH, expand=True)

        self.frm_src_btns = Frame(self, pady=5, padx=5)
        self.frm_src_btns.pack(fill=X)

        self.btn_src_add = Button(self.frm_src_btns, text="Add", command=self.add_src)
        self.btn_src_add.pack(side=LEFT)
        self.btn_src_rm = Button(self.frm_src_btns, text="Remove", command=self.rm_src)
        self.btn_src_rm.pack(side=RIGHT)

    def add_src(self):
        src = filedialog.askdirectory(title="Choose Source")
        if src is not None:
            lst = list(self.lstvar_src.get())
            lst.append(src)
            self.lstvar_src.set(lst)

    def rm_src(self):
        if len(self.lstbx_src.curselection()) > 0:
            items = list(self.lstvar_src.get())
            for i in self.lstbx_src.curselection():
                del items[i]
            self.lstvar_src.set(items)


class ExclusionFrame(LabelFrame):
    def __init__(self, root):
        super().__init__(root, text="Exclusions", pady=10, padx=10)
        self.pack(side=LEFT, anchor=NW, fill=BOTH, expand=True)

        self.lstvar_exc = Variable()
        self.lstvar_exc.set([])

        self.lstbx_exc = Listbox(self, listvariable=self.lstvar_exc, selectmode=SINGLE)
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
            lst = list(self.lstvar_exc.get())
            lst.append(exc)
            self.lstvar_exc.set(lst)

    def rm_exc(self):
        if len(self.lstbx_exc.curselection()) > 0:
            items = list(self.lstvar_exc.get())
            for i in self.lstbx_exc.curselection():
                del items[i]
            self.lstvar_exc.set(items)


class DestinationFrame(LabelFrame):
    def __init__(self, root):
        super().__init__(root, text="Destination", pady=10, padx=10)
        self.pack(side=LEFT, anchor=NW, fill=BOTH, expand=True)

        self.var_dest = StringVar()
        self.var_dest.set("")

        self.txt_dest = Entry(self, textvariable=self.var_dest)
        self.txt_dest.pack(fill=X)

        self.var_wrap = BooleanVar()
        self.var_wrap.set(True)
        self.chk_wrap = Checkbutton(self, text="Create Date Wrapper", variable=self.var_wrap, onvalue=True,
                                    offvalue=False)
        self.chk_wrap.pack()

        self.btn_dest_browse = Button(self, text="Browse", command=self.set_dest)
        self.btn_dest_browse.pack()

    def set_dest(self):
        dest = filedialog.askdirectory(title="Choose Destination")
        if dest is not None:
            self.var_dest.set(dest)


class ActionFrame(Frame):
    def __init__(self, root, frm_src: SourceFrame, frm_exc: ExclusionFrame, frm_dest: DestinationFrame):
        super().__init__(root, padx=10, pady=10)
        self.pack(side=BOTTOM, fill=X)

        self.config_src = frm_src
        self.config_exc = frm_exc
        self.config_dest = frm_dest

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
                list(frm_src.lstvar_src.get()),
                list(frm_exc.lstvar_exc.get()),
                frm_dest.var_dest.get())

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
            self.config_src.lstvar_src.set(src)
            self.config_exc.lstvar_exc.set(exc)
            self.config_dest.var_dest.set(dest)
            self.var_dry.set(dry)
            self.config_dest.var_wrap.set(wrap)

    def save_backup(self):
        file: str = filedialog.asksaveasfilename(title="Save Configuration",
                                                 filetypes=(("JSON files", "*.json"), ("All Files", "*.*")),
                                                 defaultextension=".json")
        if file is not None and len(file.strip()) > 0:
            Backup.save_to_json(file,
                                self.config_src.lstvar_src.get(),
                                self.config_exc.lstvar_exc.get(),
                                self.config_dest.var_dest.get(),
                                self.var_dry.get(),
                                self.config_dest.var_wrap.get())

    def run_backup(self, sources: list, exceptions: list, destination: str):
        self.var_prog.set(0)
        self.var_stat.set("Ready")
        self.bk = Backup(dry_run=self.var_dry.get(), use_wrapper=self.config_dest.var_wrap.get())
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


def setup(root: Tk):
    root.title("Backup Utility")
    img = PhotoImage(data=icon)
    root.tk.call('wm', 'iconphoto', root._w, img)

    frm_config = Frame(root, padx=10, pady=10)
    frm_config.pack(side=TOP, fill=BOTH, expand=True)

    frm_src = SourceFrame(frm_config)
    frm_exc = ExclusionFrame(frm_config)
    frm_dest = DestinationFrame(frm_config)

    frm_action = ActionFrame(root, frm_src, frm_exc, frm_dest)


def main():
    root = Tk()
    setup(root)
    root.mainloop()


if __name__ == "__main__":
    main()
