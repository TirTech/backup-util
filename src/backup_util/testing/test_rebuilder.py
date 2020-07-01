import datetime
import logging
from random import randint

import pytest

from backup_util.managed import Rebuilder, MetaRecord
from backup_util.managed.records import record_ext, Record
from backup_util.testing.FileTree import FileTree

log = logging.getLogger(__name__)


@pytest.fixture()
def filetree(tmp_path):
    return FileTree(str(tmp_path))


def test_discover_dirs(filetree):
    dirs = ["Dir A", "Dir B", "Dir C"]
    for d in dirs:
        filetree.dir(d)
    filetree.build()
    log.info(f"Created:\t{dirs}")
    mr = MetaRecord.create_new(filetree.path)
    mr.save()
    rb = Rebuilder(mr)
    rbdirs = list(map(lambda x: x.folder, rb.records()))
    log.info(f"Found:  \t{rbdirs}")
    for d in rbdirs:
        assert d in dirs
        dirs.remove(d)
    assert len(dirs) == 0


def test_gen_records(filetree):
    dirs = ["Dir A", "Dir B", "Dir C"]
    for d in dirs:
        filetree \
            .dir(d) \
            .file(f"testfile-{randint(1, 100)}.txt") \
            .file(f"testfile-{randint(1, 100)}.txt")
    filetree.build()
    log.info(f"Created:\t{dirs}")
    mr = MetaRecord.create_new(filetree.path)
    mr.save()
    rb = Rebuilder(mr)
    for i, r in enumerate(rb.records()):
        ts = r.timestamp + datetime.timedelta(seconds=i * 10)
        date_safe = ts.strftime('%Y-%m-%d_%H-%M-%S')
        rb.configure_directory(r.folder, timestamp=ts, name=f"Backup for {date_safe}")
    rb.generate_records()
    rb.wait_for_completion()
    for r in rb.records():
        path = f"records/{r.name}{record_ext}"
        filetree.exists(path)
        loaded_rec = Record.load_from(filetree.path, r.name)
        assert loaded_rec == r
