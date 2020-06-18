from __future__ import annotations

import datetime
import json
import os
from typing import List, Tuple

import utils

record_ext = ".rec.json"
record_folder = "records"
metarecord_name = f"metarecord{record_ext}"


class FileData:
    def __init__(self, file: str, file_hash: str, source: str):
        self.file = file
        self.hash = file_hash
        self.source = source

    @classmethod
    def __objectify__(cls, data: dict):
        return cls(
            data["file"],
            data["hash"],
            data["source"])

    def __jsonify__(self):
        return {
            "file": self.file,
            "hash": self.hash,
            "source": self.source
        }


class MetaRecordEntry:
    def __init__(self, timestamp: datetime.datetime, name: str):
        self.timestamp: datetime.datetime = timestamp
        self.name: str = name

    @classmethod
    def __objectify__(cls, data: dict):
        return cls(
            datetime.datetime.fromisoformat(data["timestamp"]),
            data["name"]
        )

    def __jsonify__(self):
        return {
            "name": self.name,
            "timestamp": self.timestamp
        }


class MetaRecord:
    def __init__(self, data: dict, path: str):
        self.latest: MetaRecordEntry = MetaRecordEntry.__objectify__(data["latest"]) if "latest" in data else None
        self.records: List[MetaRecordEntry] = [MetaRecordEntry.__objectify__(r) for r in data["records"]]
        self.path = path

    @classmethod
    def load_from(cls, path: str) -> MetaRecord:
        abspath = os.path.join(path, record_folder, metarecord_name)
        if os.path.exists(abspath) and os.path.isfile(abspath):
            with open(abspath, "r") as file:
                data = json.load(file)
                return cls(data, path)

    @classmethod
    def create_new(cls, path: str):
        return cls({"records": []}, path)

    def load_latest_record(self) -> Record:
        if self.latest is not None:
            return Record.load_from(self.path, self.latest.name)
        else:
            raise NoRecordError("No records have been created for this MetaRecord")

    def save(self):
        if os.path.exists(self.path) and os.path.isdir(self.path):
            recpath = os.path.join(self.path, record_folder)
            if not os.path.exists(recpath):
                os.mkdir(recpath)
            with open(os.path.join(recpath, metarecord_name), "w+") as file:
                json.dump(self, file, cls=utils.CustomJSONEncoder)
        else:
            raise FileNotFoundError(f"The path {self.path} does not exist")

    def add_record(self, record: Record):
        mre = MetaRecordEntry(record.timestamp, record.name)
        self.records.append(mre)
        if self.latest is None or mre.timestamp > self.latest.timestamp:
            self.latest = mre

    def __jsonify__(self):
        data = {}
        if self.latest is not None:
            data["latest"] = self.latest
        data["records"] = self.records
        return data


class Record:
    def __init__(self, data: dict, path: str):
        self.name = data["name"]
        self.folder = data["folder"]
        self.timestamp = datetime.datetime.fromisoformat(data["timestamp"])
        self.files = [FileData.__objectify__(f) for f in data["files"]] if "files" in data else []
        self.path = path

    @classmethod
    def load_from(cls, path: str, name: str) -> Record:
        file_path = os.path.join(path, record_folder, f"{name}{record_ext}")
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            raise FileNotFoundError(f"The file {file_path} does not exist or is a directory")

        with open(file_path, "r") as file:
            data = json.load(file)
            return cls(data, path)

    @classmethod
    def create_new(cls, name: str, folder: str, path: str, date: datetime = datetime.datetime.now()) -> Record:
        """
        Create a new backup record for a managed folder

        :param name: the name of the backup
        :param folder: the name of the folder this backup's data is contained in
        :param path: the path to the managed folder (top level containing other backups and records)
        :param date: the date the backup occurred on, defaults to datetime.now()
        :return: a new Record
        """
        return cls({
            "name": name,
            "folder": folder,
            "timestamp": date.isoformat()
        }, path)

    def save(self, metarecord: MetaRecord = None) -> None:
        """
        Save this record to a record file and register it in the metarecord
        """
        mr = MetaRecord.load_from(self.path) if metarecord is None else metarecord
        mr.add_record(self)
        if os.path.exists(self.path) and os.path.isdir(self.path):
            recpath = os.path.join(self.path, record_folder)
            if not os.path.exists(recpath):
                os.mkdir(recpath)
            with open(os.path.join(recpath, f"{self.name}{record_ext}"), "w+") as file:
                json.dump(self, file, cls=utils.CustomJSONEncoder)
        else:
            raise NotADirectoryError(f"The path {self.path} does not exist or is not a directory")

    def add_file(self, abs_path: str, relative_path: str, source: str = None) -> None:
        file = FileData(relative_path, utils.hash_file(abs_path), source if source is not None else self.name)
        self.files.append(file)

    def data_path(self) -> str:
        return os.path.join(self.path, self.folder)

    def __jsonify__(self) -> dict:
        return {
            "name": self.name,
            "folder": self.folder,
            "timestamp": self.timestamp,
            "files": self.files
        }

    def file_diff(self, rec: Record) -> Tuple[List[FileData], List[FileData], List[FileData]]:
        """
        Returns the added, changed, and removed files as a tuple (in that order)
        between this record and the previous. A change is considered chronologically.
        I.e. if ``rec`` is older that ``self``, a file that exists in ``rec`` but not in ``self`` was *deleted*, whereas
        if ``rec`` is newer that same file was *created*.
        """
        removed = []
        changed = []
        sfiles = self.files.copy()
        recfiles = rec.files.copy()
        for i, f in enumerate(sfiles):
            p, v = utils.find_match(recfiles, lambda x: x.file == f.file)
            if p is None:
                removed.append(f)
            else:
                if v.hash != f.hash:
                    changed.append(f)
                recfiles.remove(v)
        added = recfiles

        # Considered self as oldest, confirm or swap created/deleted
        if self.timestamp < rec.timestamp:
            return added, changed, removed
        else:
            return removed, changed, added


class NoRecordError(Exception):
    def __init__(self, *args):
        super().__init__(*args)
