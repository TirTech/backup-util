import logging
from datetime import datetime
from queue import Queue
from time import sleep
from typing import Union, Tuple

from exception.ValidationException import ValidationException
import os
import shutil
import json
from threading import Thread

log = logging.getLogger(__name__)


class Backup:

    def __init__(self, dry_run: bool = False, use_wrapper=False):
        self.dry_run: bool = dry_run
        self.use_wrapper = use_wrapper
        self.sources: list = []
        self.destination: str = ""
        self.exceptions: list = []
        self.thread: Union[Thread, None] = None

    def add_source(self, source: str) -> None:
        self.sources.append(source)

    def add_exception(self, rule: str) -> None:
        self.exceptions.append(rule)

    def set_destination(self, dest: str) -> None:
        self.destination = dest

    @staticmethod
    def save_to_json(path: str, src: list, exc: list, dest: str, dry: bool = False, wrap: bool = False) -> None:
        with open(path, "w+") as jfile:
            data = {
                "sources": src,
                "exceptions": exc,
                "destination": dest,
                "dry_run": dry,
                "use_wrapper": wrap
            }
            json.dump(data, jfile)

    @staticmethod
    def load_from_json(path: str) -> Tuple[list, list, str, bool, bool, bool]:
        with open(path, "r") as jfile:
            data = json.load(jfile)
            return (data["sources"],
                    data["exceptions"],
                    data["destination"],
                    data["dry_run"] if "dry_run" in data else False,
                    data["use_wrapper"] if "use_wrapper" in data else False,
                    data["managed"] if "managed" in data else False)

    def execute(self) -> Queue:
        self.validate()
        log.info(f"Starting tree copy of {self.sources} to {self.destination}")

        data_queue = Queue()
        if not self.dry_run:
            self.thread = Thread(target=self._backup_thread, args=[data_queue])
        else:
            self.thread = Thread(target=self._backup_thread_dry, args=[data_queue])

        self.thread.start()
        return data_queue

    def _backup_thread(self, data_queue: Queue) -> None:
        ignore_func = shutil.ignore_patterns(*self.exceptions)
        root_dest = self.destination
        if self.use_wrapper:
            root_dest = os.path.join(root_dest, datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
            os.mkdir(root_dest)

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

    def _backup_thread_dry(self, data_queue: Queue) -> None:
        for i in range(1, 11):
            data_queue.put(BackupUpdate("Update" + ("!" * i), i, 10))
            sleep(0.25)
            data_queue.put(BackupUpdate("Minor Update 1", minor=True))
            sleep(0.25)
            data_queue.put(BackupUpdate("Minor Update 2", minor=True))
            sleep(0.25)
            data_queue.put(BackupUpdate("Minor Update 3", minor=True))
            sleep(0.25)
            data_queue.put(BackupUpdate("Minor Update 4", minor=True))

    def is_running(self):
        return self.thread is not None and self.thread.is_alive()

    def wait_for_completion(self):
        if self.thread is not None and self.thread.is_alive():
            self.thread.join()

    def validate(self):
        """
        Validate the configuration of the backup. Raises a ValidationException if validation fails.
        """
        if self.destination is None or len(self.destination.strip()) == 0:
            raise ValidationException("Validation failed: No destination set")
        if not os.path.exists(self.destination):
            raise ValidationException(f"Validation failed: Destination {self.destination} does not exist")
        if len(self.sources) == 0:
            raise ValidationException("Validation failed: No sources set")
        for source in self.sources:
            if not os.path.exists(source):
                raise ValidationException(f"Validation failed: Source path {source} does not exist")

    def __str__(self):
        return f"Backup[dry_run={self.dry_run},sources={str(self.sources)},destination={str(self.destination)},exceptions={str(self.exceptions)}]"


class BackupUpdate:
    def __init__(self, message: str, progress: int = 1, progress_max: int = 1, minor: bool = False):
        self.progress = progress
        self.progress_max = progress_max
        self.message = message
        self.minor = minor

    def get_completion(self) -> float:
        return round(float(self.progress / self.progress_max) * 100, 2)

    def is_minor(self):
        return self.minor
