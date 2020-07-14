import queue
from queue import Queue
from tkinter import TOP, N, BOTH, Toplevel, END, BOTTOM, S, RIGHT, W, X
from tkinter.ttk import Frame, Treeview, Button

from backup_util.utils.threading import AsyncUpdate
from backup_util.managed import MetaRecord
from backup_util.managed import Rebuilder
from .status_frame import StatusFrame


class RebuildDialog(Frame):
    def __init__(self, root, mr: MetaRecord):
        super().__init__(root, padding=10)
        self.pack(side=TOP, anchor=N, fill=BOTH, expand=True)
        self.metarecord = mr

        self.tree = Treeview(self, padding=5, columns=["timestamp", "data_folder", "included"], selectmode="browse")
        self.tree.heading(0, text="Backup Name")
        self.tree.heading("timestamp", text="Timestamp")
        self.tree.heading("data_folder", text="Data Folder")
        self.tree.heading("included", text="Included?")
        self.tree.pack(fill=BOTH, expand=True)

        self.frm_btns = Frame(self, padding=5)
        self.frm_btns.pack(side=BOTTOM, anchor=S)

        self.btn_include = Button(self.frm_btns, text="Toggle Inclusion", command=self._toggle_include)
        self.btn_include.pack(side=RIGHT, anchor=W)

        self.btn_gen = Button(self.frm_btns, text="Generate Records", command=self._generate)
        self.btn_gen.pack(side=RIGHT, anchor=W)

        self.frm_status = StatusFrame(self)
        self.frm_status.pack(side=TOP, anchor=N, fill=X, expand=True)

        self.rebuilder = Rebuilder(mr)
        self._setup_tree()

    def _generate(self):
        queue = self.rebuilder.generate_records()
        self.listen_for_result(queue)

    def listen_for_result(self, data_queue: Queue):
        try:
            while not data_queue.empty():
                res: AsyncUpdate = data_queue.get_nowait()
                if not res.is_minor():
                    self.frm_status.set_major(f"[{res.get_completion()}%] {res.message}")
                    self.frm_status.set_progress(res.get_completion())
                else:
                    self.frm_status.set_minor(f"|> {res.message}")
        except queue.Empty:
            pass
        finally:
            if self.rebuilder.thread is not None and (self.rebuilder.thread.is_alive() or not data_queue.empty()):
                self.after(100, lambda: self.listen_for_result(data_queue))

    def _toggle_include(self):
        for item in self.tree.selection():
            ts, folder, inc = self.tree.item(item, option="values")
            inc = inc == 'False'
            self.rebuilder.configure_directory(folder, included=inc)
            self.tree.item(item, values=[ts, folder, inc])

    def _setup_tree(self):
        self.tree.delete(*self.tree.get_children())
        for r, i in self.rebuilder.directories:
            self.tree.insert("", END, text=r.name, values=[r.timestamp, r.folder, i])

    @staticmethod
    def create_dialog(mr: MetaRecord) -> Toplevel:
        window = Toplevel()
        RebuildDialog(window, mr)
        window.title("MetaRecord Rebuilder")
        return window
