import logging

import pytest

from time import sleep
from records import *
from testing.FileTree import FileTree
from testing.testutils import test_file_dir, temp_cleanup, rel_path

log = logging.getLogger(__name__)

mr_path = os.path.join(record_folder, metarecord_name)


def assert_records_same(recA: Record, recB: Record):
    assert recA.name == recB.name
    assert recA.folder == recB.folder
    assert recA.path == recB.path
    assert recA.timestamp == recB.timestamp
    assert len(recA.files) == len(recB.files)
    for i, r in enumerate(recA.files):
        assert r.file == recB.files[i].file
        assert r.hash == recB.files[i].hash
        assert r.source == recB.files[i].source


@pytest.fixture()
def filetree():
    return FileTree(test_file_dir)


def teardown_function(function):
    temp_cleanup(log)


def test_create_metarecord(filetree):
    mr = MetaRecord.create_new(test_file_dir)
    mr.save()
    assert filetree.exists(mr_path)
    assert len(filetree.content(mr_path)) > 0


def test_load_metarecord(filetree):
    mr = MetaRecord.create_new(test_file_dir)
    rec = Record.create_new("Rec A", "Rec A Data", test_file_dir)
    rec.save(mr)
    mr.save()
    newmr = MetaRecord.load_from(test_file_dir)
    assert mr.path == newmr.path
    assert len(mr.records) == len(newmr.records)
    for i, r in enumerate(mr.records):
        assert r.name == newmr.records[i].name
        assert r.timestamp == newmr.records[i].timestamp


def test_create_record(filetree):
    mr = MetaRecord.create_new(test_file_dir)
    new_rec_folder = "Rec A Data"
    new_rec_name = "Rec A"
    new_rec_full_path = os.path.join(record_folder, f"{new_rec_name}{record_ext}")
    rec = Record.create_new(new_rec_name, new_rec_folder, test_file_dir)
    rec.save(mr)
    mr.save()
    assert filetree.exists(new_rec_full_path)
    assert len(filetree.content(new_rec_full_path)) > 0
    assert filetree.exists(mr_path)
    assert len(filetree.content(mr_path)) > 0


def test_load_record(filetree):
    filetree.dir("source_data").file("junkA").file("junkB").build()
    mr = MetaRecord.create_new(test_file_dir)
    rec = Record.create_new("Rec A", "Rec A Data", test_file_dir)
    rec.add_file(rel_path("source_data/junkA"), rel_path("source_data/junkA"))
    rec.add_file(rel_path("source_data/junkB"), rel_path("source_data/junkB"))
    rec.save(mr)
    mr.save()
    newrec = Record.load_from(rec.path, rec.name)
    assert_records_same(rec, newrec)


def test_load_latest_record(filetree):
    # Records are timestamped on CREATION NOT SAVE. This test should reflect that the first to be *instantiated*
    # is the oldest, not the first to be saved!
    mr = MetaRecord.create_new(test_file_dir)
    recA = Record.create_new("Rec A", "Rec A Data", test_file_dir)  # Oldest
    sleep(2)
    recB = Record.create_new("Rec B", "Rec B Data", test_file_dir)  # Newest
    recB.save(mr)
    recA.save(mr)
    mr.save()
    latest = mr.load_latest_record()
    assert_records_same(latest, recB)
    sleep(2)
    recC = Record.create_new("Rec C", "Rec C Data", test_file_dir)  # New Newest
    recC.save(mr)
    mr.save()
    latest = mr.load_latest_record()
    assert_records_same(latest, recC)


def test_diff_records(filetree):
    filetree.dir("source_data")\
        .file("junkA", deferred_content=["different things"])\
        .file("junkB", deferred_content=["different things B"])\
        .build()
    mr = MetaRecord.create_new(test_file_dir)
    rec = Record.create_new("Rec A", "Rec A Data", test_file_dir)
    rec.add_file(rel_path("source_data/junkA"), rel_path("source_data/junkA"))
    rec.add_file(rel_path("source_data/junkB"), rel_path("source_data/junkB"))
    rec.save(mr)
    mr.save()
    filetree.root().do_deferred()
    rec2 = Record.create_new("Rec A - 2", "Rec A Data", test_file_dir)
    rec2.add_file(rel_path("source_data/junkA"), rel_path("source_data/junkA"))
    rec2.add_file(rel_path("source_data/junkB"), rel_path("source_data/junkB"))
    rec2.save(mr)
    mr.save()
    add, chg, rm = rec2.file_diff(rec)
    assert len(add) == 0
    assert len(chg) == 2
    assert len(rm) == 0
    assert chg[0] == rec2.files[0]
    assert chg[1] == rec2.files[1]
