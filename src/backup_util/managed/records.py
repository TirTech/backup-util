from __future__ import annotations

import datetime
import json
import os
from functools import reduce
from typing import List, Tuple, Optional

from backup_util.utils.datautils import hash_file, find_match, CustomJSONEncoder

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

    def __eq__(self, other: FileData) -> bool:
        return self.file == other.file and self.hash == other.hash and self.source == other.source

    def __str__(self) -> str:
        return f"[file={self.file}, hash={self.hash}, source={self.source}]"


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
    def load_from(cls, path: str) -> Optional[MetaRecord]:
        abspath = os.path.join(path, record_folder, metarecord_name)
        if os.path.exists(abspath) and os.path.isfile(abspath):
            with open(abspath, "r") as file:
                data = json.load(file)
                return cls(data, path)
        else:
            return None

    @staticmethod
    def is_managed(path: str) -> bool:
        if path is None:
            return False
        abspath = os.path.join(path, record_folder, metarecord_name)
        return os.path.exists(abspath) and os.path.isfile(abspath)

    @classmethod
    def create_new(cls, path: str):
        return cls({"records": []}, path)

    def load_latest_record(self) -> Record:
        """
        Loads the latest record for this managed folder.

        :return: the latest record
        """
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
                json.dump(self, file, cls=CustomJSONEncoder)
        else:
            raise FileNotFoundError(f"The path {self.path} does not exist")

    def add_record(self, record: Record):
        mre = MetaRecordEntry(record.timestamp, record.name)
        self.records.append(mre)
        if self.latest is None or mre.timestamp >= self.latest.timestamp:
            self.latest = mre

    def __jsonify__(self):
        data = {}
        if self.latest is not None:
            data["latest"] = self.latest
        data["records"] = self.records
        return data


class Record:
    def __init__(self, path: str, name: str, folder: str, timestamp: Optional[datetime.datetime] = None,
                 files: Optional[List[FileData]] = None):
        self.name = name
        self.folder = folder
        self.timestamp = timestamp if timestamp is not None else datetime.datetime.now()
        self.files = files if files is not None else []
        self.path = path

    @staticmethod
    def load_from(path: str, name: str) -> Record:
        file_path = os.path.join(path, record_folder, f"{name}{record_ext}")
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            raise FileNotFoundError(f"The file {file_path} does not exist or is a directory")

        with open(file_path, "r") as file:
            data = json.load(file)
            return Record.__objectify__(data, path)

    @classmethod
    def __objectify__(cls, data: dict, path: str):
        return cls(
            path,
            data["name"],
            data["folder"],
            datetime.datetime.fromisoformat(data["timestamp"]),
            [FileData.__objectify__(f) for f in data["files"]] if "files" in data else None
        )

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
                json.dump(self, file, cls=CustomJSONEncoder)
        else:
            raise NotADirectoryError(f"The path {self.path} does not exist or is not a directory")

    def add_file(self, abs_path: str, relative_path: str, source: str = None) -> FileData:
        """
        Add a file to this record.

        :param abs_path: the absolute path to the file
        :param relative_path: the path to the file relative to the data folder it is contained in
        (e.g. Documents/file.txt not X:/backups/data/Documents/file.txt)
        :param source: the name of the backup where this file is located
        :return: a `FileData` object for the new file
        """
        file = FileData(relative_path, hash_file(abs_path), source if source is not None else self.name)
        self.files.append(file)
        return file

    def data_path(self) -> str:
        """
        Get the absolute path of the data folder for this record

        :return: the path to the data directory
        """
        return os.path.join(self.path, self.folder)

    def __jsonify__(self) -> dict:
        return {
            "name": self.name,
            "folder": self.folder,
            "timestamp": self.timestamp,
            "files": self.files
        }

    def file_diff(self, rec: Record) -> Tuple[
        List[FileData], List[Tuple[FileData, FileData]], List[FileData], List[Tuple[FileData, FileData]]]:
        """
        Returns the added, changed, removed, and unchanged files as a tuple (in that order)
        between this record and the previous. A change is considered with self being older

        :param rec: the record to diff against
        :return: the added, changed, removed, and unchanged FileData objects
        """
        removed = []
        changed = []
        unchanged = []
        sfiles = self.files.copy()
        recfiles = rec.files.copy()
        for i, f in enumerate(sfiles):
            p, v = find_match(recfiles, lambda x: x.file == f.file)
            if p is None:
                removed.append(f)
            else:
                if v.hash != f.hash:
                    changed.append((f, v))
                else:
                    unchanged.append((f, v))
                recfiles.remove(v)
        added = recfiles

        return added, changed, removed, unchanged

    def __eq__(self, other) -> bool:
        def file_reduce(acc, v):
            i, fd = v
            return acc and fd == other.files[i]

        return \
            isinstance(other, Record) and \
            self.name == other.name and \
            self.folder == other.folder and \
            self.path == other.path and \
            self.timestamp == other.timestamp and \
            len(self.files) == len(other.files) and \
            reduce(file_reduce, enumerate(self.files), True)


class NoRecordError(Exception):
    def __init__(self, *args):
        super().__init__(*args)
