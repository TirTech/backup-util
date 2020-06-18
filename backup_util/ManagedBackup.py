import logging
import os
import shutil
from datetime import datetime
from queue import Queue

from Backup import Backup, BackupUpdate
from records import Record

log = logging.getLogger(__name__)
record_folder = ".records"


class ManagedBackup(Backup):
    def __init__(self, dry_run: bool = False):
        super().__init__(dry_run, True)

    def _backup_thread(self, data_queue: Queue) -> None:
        ignore_func = shutil.ignore_patterns(*self.exceptions)
        date = datetime.now()
        date_safe = date.strftime('%Y-%m-%d_%H-%M-%S')

        # Create a record for this backup. Will hold all the needed information
        rec = Record.create_new(f"Backup for {date.isoformat()}", f"data_{date_safe}", self.destination, date)

        # Gen new backup folder
        root_dest = rec.data_path()
        os.mkdir(root_dest)

        # TODO rewrite to check files and conditionally copy
        def copy_func(src, dest):
            data_queue.put(BackupUpdate(src, minor=True))
            shutil.copy2(src, dest)

        for index, source in enumerate(self.sources):
            destination = os.path.join(root_dest, os.path.basename(source))
            data_queue.put(BackupUpdate(f"Copying {source} to {destination}", index, len(self.sources)))
            log.info(f"Copying {source} to {destination}")
            shutil.copytree(source, destination, False, ignore_func, copy_function=copy_func,
                            ignore_dangling_symlinks=True)
        data_queue.put(BackupUpdate("Complete", len(self.sources), len(self.sources)))
