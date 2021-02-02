import logging
import os
from datetime import datetime
from queue import Queue
from typing import List, Optional, Union, Tuple
import shutil

from backup_util.managed import Record, MetaRecord, records
from backup_util.utils.datautils import find_match
from backup_util.utils.threading import AsyncUpdate, Threadable, threaded_func

log = logging.getLogger(__name__)


class Restorer(Threadable):
    def __init__(self, mr: MetaRecord = None):
        super().__init__()
        self.path = mr.path
        self.metarecord = mr
        self.dest = None

    def set_destination(self, dest: str) -> None:
        if os.path.exists(dest):
            self.dest = dest

    @threaded_func()
    def perform_restore(self, data_queue: Queue):
        data_queue.put(AsyncUpdate("Loading records..."))
        lrec: Record = self.metarecord.load_latest_record()
        recs = [Record.load_from(self.metarecord.path, x.name) for x in self.metarecord.records]
        data_queue.put(AsyncUpdate("Prepping file pairs..."))
        filepairs: List[Tuple[str, str]] = []
        for i, fd in enumerate(lrec.files):
            item: Tuple[str, str]
            data_queue.put(AsyncUpdate(f"[{fd.source}] {fd.file}",i,len(lrec.files)))
            if fd.source == lrec.name:
                item = (os.path.join(lrec.data_path(), fd.file).replace("\\","/"), os.path.join(self.dest, fd.file).replace("\\","/"))
            else:
                ri, r = find_match(recs, lambda x: x.name == fd.source)
                item = (os.path.join(r.data_path(), fd.file).replace("\\","/"), os.path.join(self.dest, fd.file).replace("\\","/"))
            data_queue.put(AsyncUpdate(f"{item[0]}, {item[1]}", minor=True))
            filepairs.append(item)
        data_queue.put(AsyncUpdate("Records Loaded. Copying..."))
        for i, item in enumerate(filepairs):
            data_queue.put(AsyncUpdate(f"[{item[0]}] {item[1]}",i,len(filepairs)))
            if os.path.exists(item[1]):
                continue
            if not os.path.exists(item[0]):
                data_queue.put(AsyncUpdate(f"[FILE MISSING] {item[0]} -> {item[1]}",i,len(filepairs)))
                continue
            ddir = os.path.dirname(item[1])
            if not os.path.exists(ddir):
                os.makedirs(ddir)
            shutil.copy2(item[0],item[1])
        data_queue.put(AsyncUpdate("Restore Complete!"))

    @staticmethod
    def quick_restore(src: str, dest: str, log: str):
        # Setup
        rst = Restorer(MetaRecord.load_from(src))
        rst.set_destination(dest)
        data_queue = rst.perform_restore()
        # Listen
        with open(log, "w+") as l:
            while rst.thread is not None and (rst.thread.is_alive() or not data_queue.empty()):
                try:
                    while not data_queue.empty():
                        res: AsyncUpdate = data_queue.get_nowait()
                        if not res.is_minor():
                            print(f"[{res.get_completion()}%] {res.message}")
                            l.write(f"[{res.get_completion()}%] {res.message}\n")
                        else:
                            print(f"|> {res.message}")
                            l.write(f"|> {res.message}\n")
                except queue.Empty:
                    pass
            print(f"Error state was: {rst.get_error()}")