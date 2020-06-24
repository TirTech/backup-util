import logging
import os
import shutil
from datetime import datetime
from queue import Queue
from typing import Optional

from backup_util import utils
from backup_util.Backup import Backup, BackupUpdate
from backup_util.records import Record, MetaRecord, NoRecordError

log = logging.getLogger(__name__)
record_folder = ".records"

code_check = "[#]"
code_copy_new = "[+]"
code_copy_changed = "[~]"


class ManagedBackup(Backup):
    def __init__(self, dry_run: bool = False):
        super().__init__(dry_run, True)
        self.last_record: Optional[Record] = None

    def _backup_thread(self, data_queue: Queue) -> None:
        self.last_record = None
        ignore_func = shutil.ignore_patterns(*self.exceptions)
        date = datetime.now()
        date_safe = date.strftime('%Y-%m-%d_%H-%M-%S')

        mr = MetaRecord.load_from(self.destination)
        if mr is None:
            mr = MetaRecord.create_new(self.destination)
        try:
            latest_record = mr.load_latest_record()
        except NoRecordError:
            latest_record = None
        rec = Record.create_new(f"Backup for {date_safe}", f"data_{date_safe}", self.destination, date)

        # Gen new backup folder
        root_dest = rec.data_path()
        os.mkdir(root_dest)

        # TODO rewrite to check files and conditionally copy
        def copy_func(src, dest):
            data_queue.put(BackupUpdate(f"{code_check} {src}", minor=True))
            fd = rec.add_file(src, utils.path_common_suffix(src, dest))

            i, f = utils.find_match(latest_record.files,
                                    lambda x: x.file == fd.file) if latest_record is not None else (None, None)
            if i is None:  # Not in past record.
                shutil.copy2(src, dest)
                data_queue.put(BackupUpdate(f"{code_copy_new} {src}", minor=True))
            else:  # In past record
                if f.hash != fd.hash:  # Different contents
                    shutil.copy2(src, dest)
                    data_queue.put(BackupUpdate(f"{code_copy_changed} {src}", minor=True))
                else:  # Same contents
                    fd.source = f.source

        for index, source in enumerate(self.sources):
            destination = os.path.join(root_dest, os.path.basename(source))
            data_queue.put(BackupUpdate(f"Copying {source} to {destination}", index, len(self.sources)))
            log.info(f"Copying {source} to {destination}")
            try:
                shutil.copytree(source, destination, False, ignore_func, copy_function=copy_func,
                                ignore_dangling_symlinks=True)
            except BaseException as e:
                log.error(f"Error during copy: {str(e)}")
        rec.save(mr)
        mr.save()
        self.last_record = rec
        data_queue.put(BackupUpdate("Complete", len(self.sources), len(self.sources)))
