import logging
import os

import pytest

from backup_util.Backup import Backup
from backup_util.exception.ValidationException import ValidationException
from backup_util.testing.FileTree import FileTree
from backup_util.testing.testutils import list_files

log = logging.getLogger(__name__)


@pytest.fixture()
def filetree(tmp_path):
    return FileTree(str(tmp_path))


def test_validation(filetree):
    b = Backup(True)
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
    b = Backup(False)
    b.add_source(filetree.relpath("testdir1"))
    filetree \
        .dir("testdir1") \
        .file("testfile1") \
        .up() \
        .dir("dest1") \
        .build()
    b.set_destination(filetree.relpath("dest1"))
    b.execute()
    b.wait_for_completion()
    assert os.path.exists(filetree.relpath("dest1/testdir1/testfile1"))
    log.info(f"Result in dest was \n{list_files(filetree.relpath('dest1'))}")


def test_backup_with_wrapper(filetree):
    b = Backup(dry_run=False, use_wrapper=True)
    b.add_source(filetree.relpath("testdir1"))
    filetree \
        .dir("testdir1") \
        .file("testfile1") \
        .up() \
        .dir("dest1") \
        .build()
    b.set_destination(filetree.relpath("dest1"))
    b.execute()
    b.wait_for_completion()
    assert not os.path.exists(filetree.relpath("dest1/testdir1/testfile1"))
    wrapper = os.listdir(filetree.relpath("dest1"))[0]
    assert os.path.exists(filetree.relpath(f"dest1/{wrapper}/testdir1/testfile1"))
    log.info(f"Result in dest was \n{list_files(filetree.relpath('dest1'))}")


def test_backup_exclusions(filetree):
    b = Backup(False)
    b.add_source(filetree.relpath("testdir1"))

    filetree \
        .dir("testdir1") \
        .file("testfile1") \
        .dir("testdir2") \
        .file("extestfile2") \
        .root() \
        .dir("dest1") \
        .build()

    b.add_exception("ex*")
    b.set_destination(filetree.relpath("dest1"))
    b.execute()
    b.wait_for_completion()
    assert os.path.exists(filetree.relpath("dest1/testdir1/testfile1"))
    assert not os.path.exists(filetree.relpath("dest1/testdir1/testdir2/extestfile2"))
    log.info(f"Result in dest was \n{list_files(filetree.relpath('dest1'))}")


def test_load_json_backup(filetree):
    data = f'{{"sources": ["{filetree.path}/testdir1","{filetree.path}/testdir2"],' \
           f'"exceptions": ["ex*"],"destination": "{filetree.path}/dest1","dry_run": false}}'
    filetree \
        .file("test.json", data) \
        .dir("testdir1") \
        .file("testfile1") \
        .up() \
        .dir("testdir2") \
        .file("extestfile2") \
        .up() \
        .dir("dest1") \
        .build()
    src, exc, dest, dry, wrapped = Backup.load_from_json(filetree.relpath("test.json"))
    b = Backup(dry_run=dry, use_wrapper=wrapped)
    b.set_destination(dest)
    for s in src:
        b.add_source(s)
    for e in exc:
        b.add_exception(e)
    log.info(f"Backup was loaded as {str(b)}")
    b.execute()
    b.wait_for_completion()
    assert os.path.exists(filetree.relpath("dest1/testdir1/testfile1"))
    assert os.path.exists(filetree.relpath("dest1/testdir2"))
    assert not os.path.exists(filetree.relpath("dest1/testdir2/extestfile2"))
    log.info(f"Result in dest was \n{list_files(filetree.relpath('dest1'))}")


def test_file_tree(filetree):
    filetree \
        .dir("A") \
        .dir("A1") \
        .file("A1_F1") \
        .up() \
        .dir("A2") \
        .file("A2_F1") \
        .file("A2_F2") \
        .build()
