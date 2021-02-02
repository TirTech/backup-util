import logging
import os
from time import sleep

import pytest

from backup_util.exception.ValidationException import ValidationException
from backup_util.managed import ManagedBackup
from backup_util.testing.FileTree import FileTree
from backup_util.testing.testutils import list_files

log = logging.getLogger(__name__)


@pytest.fixture()
def filetree(tmp_path):
    return FileTree(str(tmp_path))


def test_validation(filetree):
    b = ManagedBackup(True)
    with pytest.raises(ValidationException):  # No sources
        b.validate()
    b.add_source(filetree.relpath("test"))
    with pytest.raises(ValidationException):  # Source does not exist
        b.validate()
    filetree.dir("test").file("testfile").build()
    b.set_destination("")
    with pytest.raises(ValidationException):  # Destination is blank
        b.validate()
    b.set_destination(filetree.relpath("test2"))
    with pytest.raises(ValidationException):  # Destination does not exist
        b.validate()
    filetree.dir("test2").file("testfile2").build()
    b.validate()


def test_backup_simple(filetree):
    b = ManagedBackup(dry_run=False)
    b.add_source(filetree.relpath("testdir1"))
    filetree.dir("testdir1").file("testfile1").up().dir("dest1").build()
    b.set_destination(filetree.relpath("dest1"))
    b.execute()
    b.wait_for_completion()
    assert not os.path.exists(filetree.relpath("dest1/testdir1/testfile1"))
    wrapper = next(
        filter(lambda x: x.startswith("data"), os.listdir(filetree.relpath("dest1")))
    )
    assert os.path.exists(filetree.relpath(f"dest1/{wrapper}/testdir1/testfile1"))
    log.info(f"Result in dest was \n{list_files(filetree.relpath('dest1'))}")


def test_backup_exclusions(filetree):
    b = ManagedBackup(False)
    b.add_source(filetree.relpath("testdir1"))

    filetree.dir("testdir1").file("testfile1").dir("testdir2").file(
        "extestfile2"
    ).root().dir("dest1").build()

    b.add_exception("ex*")
    b.set_destination(filetree.relpath("dest1"))
    b.execute()
    b.wait_for_completion()
    wrapper = next(
        filter(lambda x: x.startswith("data"), os.listdir(filetree.relpath("dest1")))
    )
    assert os.path.exists(filetree.relpath(f"dest1/{wrapper}/testdir1/testfile1"))
    assert not os.path.exists(
        filetree.relpath(f"dest1/{wrapper}/testdir1/testdir2/extestfile2")
    )
    log.info(f"Result in dest was \n{list_files(filetree.relpath('dest1'))}")


def test_load_json_backup(filetree):
    data = (
        f'{{"sources": ["{filetree.path}/testdir1","{filetree.path}/testdir2"],'
        f'"exceptions": ["ex*"],"destination": "{filetree.path}/dest1","dry_run": false}}'
    )
    filetree.file("test.json", data).dir("testdir1").file("testfile1").up().dir(
        "testdir2"
    ).file("extestfile2").up().dir("dest1").build()
    src, exc, dest, dry, wrapped = ManagedBackup.load_from_json(
        filetree.relpath("test.json")
    )
    b = ManagedBackup(dry_run=dry)
    b.set_destination(dest)
    for s in src:
        b.add_source(s)
    for e in exc:
        b.add_exception(e)
    log.info(f"Backup was loaded as {str(b)}")
    b.execute()
    b.wait_for_completion()
    wrapper = next(
        filter(lambda x: x.startswith("data"), os.listdir(filetree.relpath("dest1")))
    )
    assert os.path.exists(filetree.relpath(f"dest1/{wrapper}/testdir1/testfile1"))
    assert os.path.exists(filetree.relpath(f"dest1/{wrapper}/testdir2"))
    assert not os.path.exists(filetree.relpath(f"dest1/{wrapper}/testdir2/extestfile2"))
    log.info(f"Result in dest was \n{list_files(filetree.relpath('dest1'))}")


def test_backup_twice_nochange(filetree):
    b = ManagedBackup(dry_run=False)
    b.add_source(filetree.relpath("testdir1"))
    filetree.dir("testdir1").file("testfile1").up().dir("dest1").build()
    b.set_destination(filetree.relpath("dest1"))
    b.execute()
    b.wait_for_completion()
    assert not os.path.exists(filetree.relpath("dest1/testdir1/testfile1"))
    wrapper = next(
        filter(lambda x: x.startswith("data"), os.listdir(filetree.relpath("dest1")))
    )
    assert os.path.exists(filetree.relpath(f"dest1/{wrapper}/testdir1/testfile1"))
    log.info(f"Result in dest was \n{list_files(filetree.relpath('dest1'))}")
    log.info("Sleeping for 5 seconds")
    sleep(5)
    log.info("Performing second backup")
    b = ManagedBackup(dry_run=False)
    b.add_source(filetree.relpath("testdir1"))
    filetree.dir("testdir1").file("testfile1").up().dir("dest1").build()
    b.set_destination(filetree.relpath("dest1"))
    b.execute()
    b.wait_for_completion()
    log.info(f"Result in dest was \n{list_files(filetree.relpath('dest1'))}")
    rec = b.last_record
    assert os.path.exists(filetree.relpath("dest1", rec.folder))
    assert len(rec.files) == 1
    assert rec.files[0].source != rec.name
    assert not os.path.exists(filetree.relpath("dest1", rec.folder, rec.files[0].file))
    print("BREAK")
