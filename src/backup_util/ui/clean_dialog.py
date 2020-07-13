from queue import Queue, Empty
from tkinter import TOP, N, BOTH, Toplevel, END, BOTTOM, S, RIGHT, W, X, N
from tkinter.messagebox import askyesno, showinfo
from tkinter.ttk import Frame, Treeview, Button
from typing import Optional, Callable

from backup_util.managed import MetaRecord
from backup_util.utils.threading import AsyncUpdate
from .status_frame import StatusFrame
from ..managed.cleaner import Cleaner


class CleanDialog(Frame):
    def __init__(self, root, mr: MetaRecord):
        super().__init__(root, padding=10)
        self.pack(side=TOP, anchor=N, fill=BOTH, expand=True)
        self.metarecord = mr

        self.tree = Treeview(self, padding=5, selectmode="browse")
        self.tree.heading("#0", text="Files")
        self.tree.pack(fill=BOTH, expand=True)

        self.frm_btns = Frame(self, padding=5)
        self.frm_btns.pack(side=BOTTOM, anchor=S)

        self.btn_include = Button(self.frm_btns, text="Perform Clean", command=self._perform_clean)
        self.btn_include.pack(side=RIGHT, anchor=W)

        self.frm_status = StatusFrame(self)
        self.frm_status.pack(side=TOP, anchor=N, fill=X, expand=True)

        self.cleaner = Cleaner(mr)
        self._setup_tree()

    def _perform_clean(self):
        res = askyesno("Folder Manager - Clean", f"Perform clean on {self.cleaner.file_count()} files?")
        if res:
            queue = self.cleaner.perform_clean()
            self.listen_for_result(queue)
        else:
            showinfo("Folder Manager - Clean", "Aborting cleanup")

    def listen_for_result(self, data_queue: Queue, on_complete: Optional[Callable] = None):
        try:
            while not data_queue.empty():
                res: AsyncUpdate = data_queue.get_nowait()
                if not res.is_minor():
                    self.frm_status.set_major(f"[{res.get_completion()}%] {res.message}")
                    self.frm_status.set_progress(res.get_completion())
                else:
                    self.frm_status.set_minor(f"|> {res.message}")
        except Empty:
            pass
        finally:
            if self.cleaner.thread is not None and (self.cleaner.thread.is_alive() or not data_queue.empty()):
                self.after(100, lambda: self.listen_for_result(data_queue, on_complete))
            elif on_complete is not None:
                on_complete()

    def _setup_tree(self):
        queue = self.cleaner.generate_diffs()

        def update_table():
            for r, files in self.cleaner.to_delete:
                parent = self.tree.insert("", END, text=r.name)
                for f in files:
                    self.tree.insert(parent, END, text=f)

        self.listen_for_result(queue, update_table)

    @staticmethod
    def create_dialog(mr: MetaRecord) -> Toplevel:
        window = Toplevel()
        CleanDialog(window, mr)
        window.title("MetaRecord Rebuilder")
        return window
