from __future__ import annotations

import os
from datetime import datetime
from typing import List, Tuple


class FileTree:
    def __init__(self, path: str, parent: FileTree = None):
        self.path: str = path
        self.files: List[Tuple[str, str]] = []
        self.children: List[FileTree] = []
        self.parent: FileTree = parent

    def dir(self, name: str) -> FileTree:
        path = os.path.join(self.path, name)
        matched = next(filter(lambda x: x.path == path, self.children), None)
        if matched is not None:
            return matched
        nt = FileTree(path, self)
        self.children.append(nt)
        return nt

    def file(self, name: str, value: str = str(datetime.now())) -> FileTree:
        self.files.append((os.path.join(self.path,name), value))
        return self

    def up(self) -> FileTree:
        return self.parent

    def root(self) -> FileTree:
        return self if self.parent is None else self.parent.root()

    def build(self) -> FileTree:
        return self.root()._build()

    def _build(self) -> FileTree:
        if not os.path.exists(self.path):
            os.mkdir(self.path)
        for child in self.children:
            child._build()
        for file, data in self.files:
            if not os.path.exists(file):
                with open(file, "w+") as f:
                    f.write(data)
        return self
