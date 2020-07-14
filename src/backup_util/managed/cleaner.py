import os
from queue import Queue
from typing import Optional, List, Tuple

from backup_util.utils.threading import ThrowingThread, AsyncUpdate, Threadable, threaded_func
from backup_util.managed import MetaRecord, Record


class Cleaner(Threadable):
    def __init__(self, mr: MetaRecord):
        super().__init__()
        self.metarecord: MetaRecord = mr
        self.to_delete: List[Tuple[Record, List[str]]] = []

    def file_count(self) -> int:
        count = 0
        for rec, files in self.to_delete:
            count += len(files)
        return count

    @threaded_func()
    def perform_clean(self, data_queue: Queue):
        """
        Perform cleaning operations

        :param data_queue: the queue for posting updates
        """
        pmax = len(self.to_delete)
        for i, v in enumerate(self.to_delete):
            rec, files = v
            data_queue.put(AsyncUpdate(f"Cleaning {rec.name}", i, pmax))
            for file in files:
                data_queue.put(AsyncUpdate(file, minor=True))
                os.remove(os.path.join(rec.data_path(), file))
            rec.save()
        data_queue.put(AsyncUpdate("Complete", pmax, pmax))

    @threaded_func()
    def generate_diffs(self, data_queue: Queue):
        """
        Calculate the change history of all backups for the metarecord this class was created with. Redundant files are
        collected and saved in `self.to_delete`

        :param data_queue: the queue to post updates to
        """
        data_queue.put(AsyncUpdate("Loading Records...", 0, 1))
        recs = [Record.load_from(self.metarecord.path, r.name) for r in self.metarecord.records]
        recs.sort(key=lambda r: r.timestamp)
        for i in range(len(recs) - 1):
            add, chg, rm, uchg = recs[i].file_diff(recs[i + 1])
            if len(uchg) > 0:
                files = []
                for item in uchg:
                    files.append(item[1].file)
                    item[1].source = item[0].source
                self.to_delete.append((recs[i + 1], files))
        data_queue.put(AsyncUpdate("Diff complete!"))
