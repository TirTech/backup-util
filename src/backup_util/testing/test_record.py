import logging
import os
from time import sleep

import pytest

from backup_util.managed import MetaRecord, Record
from backup_util.managed.records import record_ext, record_folder, metarecord_name
from backup_util.testing.FileTree import FileTree

log = logging.getLogger(__name__)

mr_path = os.path.join(record_folder, metarecord_name)


@pytest.fixture()
def filetree(tmp_path):
    return FileTree(str(tmp_path))


def test_create_metarecord(filetree):
    mr = MetaRecord.create_new(filetree.path)
    mr.save()
    assert filetree.exists(mr_path)
    assert len(filetree.content(mr_path)) > 0


def test_load_metarecord(filetree):
    mr = MetaRecord.create_new(filetree.path)
    rec = Record(filetree.path, "Rec A", "Rec A Data")
    rec.save(mr)
    mr.save()
    newmr = MetaRecord.load_from(filetree.path)
    assert mr.path == newmr.path
    assert len(mr.records) == len(newmr.records)
    for i, r in enumerate(mr.records):
        assert r.name == newmr.records[i].name
        assert r.timestamp == newmr.records[i].timestamp


def test_create_record(filetree):
    mr = MetaRecord.create_new(filetree.path)
    new_rec_folder = "Rec A Data"
    new_rec_name = "Rec A"
    new_rec_full_path = os.path.join(record_folder, f"{new_rec_name}{record_ext}")
    rec = Record(filetree.path, new_rec_name, new_rec_folder)
    rec.save(mr)
    mr.save()
    assert filetree.exists(new_rec_full_path)
    assert len(filetree.content(new_rec_full_path)) > 0
    assert filetree.exists(mr_path)
    assert len(filetree.content(mr_path)) > 0


def test_load_record(filetree):
    filetree.dir("source_data").file("junkA").file("junkB").build()
    mr = MetaRecord.create_new(filetree.path)
    rec = Record(filetree.path, "Rec A", "Rec A Data")
    rec.add_file(filetree.relpath("source_data/junkA"), filetree.relpath("source_data/junkA"))
    rec.add_file(filetree.relpath("source_data/junkB"), filetree.relpath("source_data/junkB"))
    rec.save(mr)
    mr.save()
    newrec = Record.load_from(rec.path, rec.name)
    assert rec == newrec


def test_load_latest_record(filetree):
    # Records are timestamped on CREATION NOT SAVE. This test should reflect that the first to be *instantiated*
    # is the oldest, not the first to be saved!
    mr = MetaRecord.create_new(filetree.path)
    recA = Record(filetree.path, "Rec A", "Rec A Data")  # Oldest
    sleep(2)
    recB = Record(filetree.path, "Rec B", "Rec B Data")  # Newest
    recB.save(mr)
    recA.save(mr)
    mr.save()
    latest = mr.load_latest_record()
    assert latest == recB
    sleep(2)
    recC = Record(filetree.path, "Rec C", "Rec C Data")  # New Newest
    recC.save(mr)
    mr.save()
    latest = mr.load_latest_record()
    assert latest == recC


def test_diff_records(filetree):
    filetree.dir("source_data") \
        .file("junkA", deferred_content=["different things"]) \
        .file("junkB", deferred_content=["different things B"]) \
        .build()
    mr = MetaRecord.create_new(filetree.path)
    rec = Record(filetree.path, "Rec A", "Rec A Data")
    rec.add_file(filetree.relpath("source_data/junkA"), filetree.relpath("source_data/junkA"))
    rec.add_file(filetree.relpath("source_data/junkB"), filetree.relpath("source_data/junkB"))
    rec.save(mr)
    mr.save()
    filetree.root().do_deferred()
    rec2 = Record(filetree.path, "Rec A - 2", "Rec A Data")
    rec2.add_file(filetree.relpath("source_data/junkA"), filetree.relpath("source_data/junkA"))
    rec2.add_file(filetree.relpath("source_data/junkB"), filetree.relpath("source_data/junkB"))
    rec2.save(mr)
    mr.save()
    add, chg, rm = rec2.file_diff(rec)
    assert len(add) == 0
    assert len(chg) == 2
    assert len(rm) == 0
    assert chg[0] == rec2.files[0]
    assert chg[1] == rec2.files[1]
