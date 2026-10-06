import sqlite3

import pytest

import mylar
from mylar import Failed


@pytest.fixture
def failed_db(tmp_path, monkeypatch):
    monkeypatch.setattr(mylar, 'DATA_DIR', str(tmp_path))
    con = sqlite3.connect(tmp_path / 'mylar.db')
    con.execute('CREATE TABLE failed (ID TEXT, Status TEXT, ComicID TEXT, IssueID TEXT, Provider TEXT, '
                'ComicName TEXT, Issue_Number TEXT, NZBName TEXT, DateFailed TEXT)')
    con.execute("INSERT INTO failed VALUES ('download', 'Failed', '160294', '1073108', 'NZBgeek (Prowlarr)', "
                "'Absolute Batman', '1', 'Absolute.Batman.001', '2026-10-06 07:59:16')")
    con.execute("INSERT INTO failed VALUES ('legacy-id', 'Failed', NULL, NULL, 'Some Indexer', "
                "NULL, NULL, 'Legacy.Release', '2020-01-01 00:00:00')")
    con.commit()
    con.close()


def check(issueid, nzbid):
    return Failed.FailedProcessor(nzb_name='x', id=nzbid, issueid=issueid, prov='NZBgeek (Prowlarr)').failed_check()


@pytest.mark.unit
def test_failed_release_still_blocked_for_its_own_issue(failed_db):
    assert check('1073108', 'download') == 'Failed'


@pytest.mark.unit
def test_failed_release_does_not_block_other_issues(failed_db):
    assert check('999999', 'download') == 'Good'


@pytest.mark.unit
def test_rows_without_issueid_still_match(failed_db):
    assert check('999999', 'legacy-id') == 'Failed'


@pytest.mark.unit
def test_unscoped_check_when_issueid_unknown(failed_db):
    assert check(None, 'download') == 'Failed'
