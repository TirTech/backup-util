import logging
import os

import pytest

import testing.testutils as testutils
from Backup import Backup
from exception.ValidationException import ValidationException
from testing.FileTree import FileTree
from testing.testutils import test_file_dir, rel_path

log = logging.getLogger(__name__)


@pytest.fixture()
def filetree():
    return FileTree(test_file_dir)


def teardown_function(function):
    testutils.temp_cleanup(log)


def test_test():
    log.info('This is a test!')


def test_validation(filetree):
    b = Backup(True)
    with pytest.raises(ValidationException):  # No sources
        b.validate()
    b.add_source(rel_path("test"))
    with pytest.raises(ValidationException):  # Source does not exist
        b.validate()
    filetree.dir("test").file("testfile").build()
    b.set_destination("")
    with pytest.raises(ValidationException):  # Destination is blank
        b.validate()
    b.set_destination(rel_path("test2"))
    with pytest.raises(ValidationException):  # Destination does not exist
        b.validate()
    filetree.dir("test2").file("testfile2").build()
    b.validate()


def test_backup_simple(filetree):
    b = Backup(False)
    b.add_source(rel_path("testdir1"))
    filetree \
        .dir("testdir1") \
        .file("testfile1") \
        .up() \
        .dir("dest1") \
        .build()
    b.set_destination(rel_path("dest1"))
    b.execute()
    b.wait_for_completion()
    assert os.path.exists(rel_path("dest1/testdir1/testfile1"))
    log.info(f"Result in dest was \n{testutils.list_files(rel_path('dest1'))}")


def test_backup_with_wrapper(filetree):
    b = Backup(dry_run=False, use_wrapper=True)
    b.add_source(rel_path("testdir1"))
    filetree \
        .dir("testdir1") \
        .file("testfile1") \
        .up() \
        .dir("dest1") \
        .build()
    b.set_destination(rel_path("dest1"))
    b.execute()
    b.wait_for_completion()
    assert not os.path.exists(rel_path("dest1/testdir1/testfile1"))
    wrapper = os.listdir(rel_path("dest1"))[0]
    assert os.path.exists(rel_path(f"dest1/{wrapper}/testdir1/testfile1"))
    log.info(f"Result in dest was \n{testutils.list_files(rel_path('dest1'))}")


def test_backup_exclusions(filetree):
    b = Backup(False)
    b.add_source(rel_path("testdir1"))

    filetree \
        .dir("testdir1") \
        .file("testfile1") \
        .dir("testdir2") \
        .file("extestfile2") \
        .root() \
        .dir("dest1") \
        .build()

    b.add_exception("ex*")
    b.set_destination(rel_path("dest1"))
    b.execute()
    b.wait_for_completion()
    assert os.path.exists(rel_path("dest1/testdir1/testfile1"))
    assert not os.path.exists(rel_path("dest1/testdir1/testdir2/extestfile2"))
    log.info(f"Result in dest was \n{testutils.list_files(rel_path('dest1'))}")


def test_load_json_backup(filetree):
    data = '{"sources": ["_test_temp_\\\\testdir1","_test_temp_\\\\testdir2"],' \
           '"exceptions": ["ex*"],"destination": "_test_temp_\\\\dest1","dry_run": false}'
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
    src, exc, dest, dry, wrapped = Backup.load_from_json(rel_path("test.json"))
    b = Backup(dry_run=dry, use_wrapper=wrapped)
    b.set_destination(dest)
    for s in src:
        b.add_source(s)
    for e in exc:
        b.add_exception(e)
    log.info(f"Backup was loaded as {str(b)}")
    b.execute()
    b.wait_for_completion()
    assert os.path.exists(rel_path("dest1/testdir1/testfile1"))
    assert os.path.exists(rel_path("dest1/testdir2"))
    assert not os.path.exists(rel_path("dest1/testdir2/extestfile2"))
    log.info(f"Result in dest was \n{testutils.list_files(rel_path('dest1'))}")


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
