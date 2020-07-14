import json
import logging
import os
import shutil
from datetime import datetime
from queue import Queue
from time import sleep
from typing import Tuple

from backup_util.exception.ValidationException import ValidationException
from backup_util.utils.threading import AsyncUpdate, Threadable, threaded_func

log = logging.getLogger(__name__)


class Backup(Threadable):

    def __init__(self, dry_run: bool = False, use_wrapper=False):
        super().__init__()
        self.dry_run: bool = dry_run
        self.use_wrapper = use_wrapper
        self.sources: list = []
        self.destination: str = ""
        self.exceptions: list = []

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
    def load_from_json(path: str) -> Tuple[list, list, str, bool, bool]:
        with open(path, "r") as jfile:
            data = json.load(jfile)
            return (data["sources"],
                    data["exceptions"],
                    data["destination"],
                    data["dry_run"] if "dry_run" in data else False,
                    data["use_wrapper"] if "use_wrapper" in data else False)

    def execute(self) -> Queue:
        self.validate()
        log.info(f"Starting tree copy of {self.sources} to {self.destination}")

        if not self.dry_run:
            return self._backup_thread()
        else:
            return self._backup_thread_dry()

    @threaded_func()
    def _backup_thread(self, data_queue: Queue):
        ignore_func = shutil.ignore_patterns(*self.exceptions)
        root_dest = self.destination
        if self.use_wrapper:
            root_dest = os.path.join(root_dest, datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
            os.mkdir(root_dest)

        def copy_func(src, dest):
            data_queue.put(AsyncUpdate(src, minor=True))
            shutil.copy2(src, dest)

        for index, source in enumerate(self.sources):
            destination = os.path.join(root_dest, os.path.basename(source))
            data_queue.put(AsyncUpdate(f"Copying {source} to {destination}", index, len(self.sources)))
            log.info(f"Copying {source} to {destination}")
            shutil.copytree(source, destination, False, ignore_func, copy_function=copy_func,
                            ignore_dangling_symlinks=True)
        data_queue.put(AsyncUpdate("Complete", len(self.sources), len(self.sources)))

    @threaded_func()
    def _backup_thread_dry(self, data_queue: Queue):
        for i in range(1, 11):
            data_queue.put(AsyncUpdate("Update" + ("!" * i), i, 10))
            sleep(0.25)
            data_queue.put(AsyncUpdate("Minor Update 1", minor=True))
            sleep(0.25)
            data_queue.put(AsyncUpdate("Minor Update 2", minor=True))
            sleep(0.25)
            data_queue.put(AsyncUpdate("Minor Update 3", minor=True))
            sleep(0.25)
            data_queue.put(AsyncUpdate("Minor Update 4", minor=True))

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
        return f"Backup[dry_run={self.dry_run}," \
               f"sources={str(self.sources)}," \
               f"destination={str(self.destination)}," \
               f"exceptions={str(self.exceptions)}]"
