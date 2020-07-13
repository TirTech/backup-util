import logging
import os
from datetime import datetime
from queue import Queue
from typing import List, Optional, Union

from backup_util.managed import Record, MetaRecord, records
from backup_util.utils.datautils import find_match
from backup_util.utils.threading import AsyncUpdate, Threadable, threaded_func

log = logging.getLogger(__name__)


class Rebuilder(Threadable):
    def __init__(self, mr: MetaRecord = None):
        super().__init__()
        self.path = mr.path
        self.directories: List[List[Union[Record, bool]]] = []
        self.metarecord = mr
        self._discover_directories()

    def records(self) -> List[Record]:
        return list(map(lambda x: x[0], self.directories))

    def _discover_directories(self):
        if os.path.exists(self.path):
            for dir in os.listdir(self.path):
                if dir == records.record_folder or not os.path.isdir(os.path.join(self.path, dir)):
                    continue
                basename = dir.rstrip("/\\")
                ts = datetime.fromtimestamp(os.path.getctime(os.path.join(self.path, dir)))
                date_safe = ts.strftime('%Y-%m-%d_%H-%M-%S')
                self.directories.append([Record(self.path, f"Backup for {date_safe}", basename, ts), True])

    @threaded_func()
    def generate_records(self, data_queue: Queue):
        dirs: List[Record] = list(map(lambda d: d[0], filter(lambda d: d[1], self.directories)))
        for index, rec in enumerate(dirs):
            destination = os.path.join(self.path, rec.folder)
            data_queue.put(AsyncUpdate(f"Building {destination}", index, len(dirs)))
            log.info(f"Building {destination}")
            count = 0
            for dirpath, dirnames, filenames in os.walk(destination):
                for file in filenames:
                    count += 1
                    abspath = os.path.join(dirpath, file)
                    relpath = os.path.relpath(abspath, destination)
                    data_queue.put(AsyncUpdate(f"[{count}] {relpath}", minor=True))
                    rec.add_file(abspath, relpath)
            rec.save(self.metarecord)
        self.metarecord.save()
        data_queue.put(AsyncUpdate("Complete!", len(dirs), len(dirs)))

    def configure_directory(self, folder: str, name: Optional[str] = None, timestamp: Optional[datetime] = None,
                            included: Optional[bool] = None):
        i: int
        v: List[Union[Record, bool]]
        i, v = find_match(self.directories, lambda x: x[0].folder == folder)
        if v is not None:
            rec = v[0]
            if name is not None:
                rec.name = name
            if timestamp is not None:
                rec.timestamp = timestamp
            if included is not None:
                v[1] = included
