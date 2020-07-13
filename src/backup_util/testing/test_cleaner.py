import logging
import os

import pytest

from backup_util.managed import MetaRecord, Record
from backup_util.managed.cleaner import Cleaner
from backup_util.testing.FileTree import FileTree

log = logging.getLogger(__name__)


@pytest.fixture()
def filetree(tmp_path):
    return FileTree(str(tmp_path))


def test_generate_diffs(filetree):
    filetree \
        .dir("rec_a_data") \
        .dir("Dir A") \
        .file("tfa_1.txt", value="testfile_data_1") \
        .file("tfa_2.txt", value="testfile_data_1") \
        .up() \
        .dir("Dir B") \
        .file("tfb_1.txt", value="testfile_data_2") \
        .root() \
        .dir("rec_b_data") \
        .dir("Dir A") \
        .file("tfa_1.txt", value="testfile_data_1_chg") \
        .file("tfa_2.txt", value="testfile_data_1") \
        .up() \
        .dir("Dir B") \
        .file("tfb_1.txt", value="testfile_data_2_chg") \
        .build()
    mr = MetaRecord.create_new(filetree.path)
    recA = Record(filetree.path, "Rec A", "rec_a_data")
    recA.add_file(filetree.relpath("rec_a_data/Dir A/tfa_1.txt"), "Dir A/tfa_1.txt")
    recA.add_file(filetree.relpath("rec_a_data/Dir A/tfa_2.txt"), "Dir A/tfa_2.txt")
    recA.add_file(filetree.relpath("rec_a_data/Dir B/tfb_1.txt"), "Dir B/tfb_1.txt")
    recA.save(mr)
    recB = Record(filetree.path, "Rec B", "rec_b_data")
    recB.add_file(filetree.relpath("rec_b_data/Dir A/tfa_1.txt"), "Dir A/tfa_1.txt")
    recB.add_file(filetree.relpath("rec_b_data/Dir A/tfa_2.txt"), "Dir A/tfa_2.txt")
    recB.add_file(filetree.relpath("rec_b_data/Dir B/tfb_1.txt"), "Dir B/tfb_1.txt")
    recB.save(mr)
    mr.save()
    cln = Cleaner(mr)
    cln.generate_diffs()
    cln.wait_for_completion()
    diffs = cln.to_delete
    assert len(diffs) == 1
    diff_rec, files = diffs[0]
    assert diff_rec.name == recB.name
    assert len(files) == 1
    assert files[0] == "Dir A/tfa_2.txt"


def test_delete(filetree):
    filetree \
        .dir("rec_a_data") \
        .dir("Dir A") \
        .file("tfa_1.txt", value="testfile_data_1") \
        .file("tfa_2.txt", value="testfile_data_1") \
        .up() \
        .dir("Dir B") \
        .file("tfb_1.txt", value="testfile_data_2") \
        .root() \
        .dir("rec_b_data") \
        .dir("Dir A") \
        .file("tfa_1.txt", value="testfile_data_1_chg") \
        .file("tfa_2.txt", value="testfile_data_1") \
        .up() \
        .dir("Dir B") \
        .file("tfb_1.txt", value="testfile_data_2") \
        .build()
    mr = MetaRecord.create_new(filetree.path)
    recA = Record(filetree.path, "Rec A", "rec_a_data")
    recA.add_file(filetree.relpath("rec_a_data/Dir A/tfa_1.txt"), "Dir A/tfa_1.txt")
    recA.add_file(filetree.relpath("rec_a_data/Dir A/tfa_2.txt"), "Dir A/tfa_2.txt")
    recA.add_file(filetree.relpath("rec_a_data/Dir B/tfb_1.txt"), "Dir B/tfb_1.txt")
    recA.save(mr)
    recB = Record(filetree.path, "Rec B", "rec_b_data")
    recB.add_file(filetree.relpath("rec_b_data/Dir A/tfa_1.txt"), "Dir A/tfa_1.txt")
    recB.add_file(filetree.relpath("rec_b_data/Dir A/tfa_2.txt"), "Dir A/tfa_2.txt")
    recB.add_file(filetree.relpath("rec_b_data/Dir B/tfb_1.txt"), "Dir B/tfb_1.txt")
    recB.save(mr)
    mr.save()
    cln = Cleaner(mr)
    cln.generate_diffs()
    cln.wait_for_completion()
    cln.perform_clean()
    cln.wait_for_completion()
    assert os.path.exists(filetree.relpath("rec_a_data/Dir A/tfa_1.txt"))
    assert os.path.exists(filetree.relpath("rec_a_data/Dir A/tfa_2.txt"))
    assert os.path.exists(filetree.relpath("rec_a_data/Dir B/tfb_1.txt"))
    assert os.path.exists(filetree.relpath("rec_b_data/Dir A/tfa_1.txt"))
    assert not os.path.exists(filetree.relpath("rec_b_data/Dir A/tfa_2.txt"))
    assert not os.path.exists(filetree.relpath("rec_b_data/Dir B/tfb_1.txt"))
