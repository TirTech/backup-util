import logging
import os
from datetime import datetime
from queue import Queue
from typing import List, Optional, Tuple, Union

from backup_util import utils
from backup_util.Backup import ThrowingThread, AsyncUpdate
from backup_util.managed import Record, MetaRecord, records

log = logging.getLogger(__name__)


class Rebuilder:
    def __init__(self, src: Union[MetaRecord, str] = None):
        self.path = src.path if isinstance(src, MetaRecord) else src
        self.directories: List[Tuple[Record, bool]] = []
        self.metarecord = src if isinstance(src, MetaRecord) else MetaRecord.load_from(src)
        self.thread: Optional[ThrowingThread] = None
        self._discover_directories()

    def records(self) -> List[Record]:
        return list(map(lambda x: x[0], self.directories))

    def _discover_directories(self):
        if os.path.exists(self.path):
            for dir in os.listdir(self.path):
                if dir == records.record_folder:
                    continue
                basename = dir.rstrip("/\\")
                ts = datetime.fromtimestamp(os.path.getctime(os.path.join(self.path, dir)))
                date_safe = ts.strftime('%Y-%m-%d_%H-%M-%S')
                self.directories.append((Record(self.path, f"Backup for {date_safe}", basename, ts), True))

    def generate_records(self) -> Queue:
        data_queue = Queue()
        self.thread = ThrowingThread(target=self._generate_records, args=[data_queue])

        self.thread.start()
        return data_queue

    def _generate_records(self, data_queue: Queue):
        dirs: List[Record] = list(map(lambda d: d[0], filter(lambda d: d[1], self.directories)))
        for index, rec in enumerate(dirs):
            destination = os.path.join(self.path, rec.folder)
            data_queue.put(AsyncUpdate(f"Building {destination}", index, len(dirs)))
            log.info(f"Building {destination}")
            for dirpath, dirnames, filenames in os.walk(destination):
                for file in filenames:
                    abspath = os.path.join(dirpath, file)
                    rec.add_file(abspath, os.path.relpath(abspath, destination))
            rec.save(self.metarecord)
        self.metarecord.save()

    def wait_for_completion(self):
        if self.thread is not None:
            self.thread.join()

    def configure_directory(self, folder: str, name: Optional[str] = None, timestamp: Optional[datetime] = None,
                            included: Optional[bool] = None):
        i: int
        v: Tuple[Record, bool]
        i, v = utils.find_match(self.directories, lambda x: x[0].folder == folder)
        if v is not None:
            rec = v[0]
            if name is not None:
                rec.name = name
            if timestamp is not None:
                rec.timestamp = timestamp
            if included is not None:
                rec.included = included
