import queue
import sqlite3
from types import SimpleNamespace

import pytest

import mylar
from mylar import Failed

ISSUEID = '700001'
COMICID = '166619'
NZBNAME = 'Batman.007.2026.Digital.Pyrate-DCP.-xpost'
PROVIDER = 'Nzb.life (Prowlarr) [nzbhydra]'


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setattr(mylar, 'DATA_DIR', str(tmp_path))
    monkeypatch.setattr(mylar, 'CONFIG', SimpleNamespace(FAILED_AUTO=False), raising=False)
    con = sqlite3.connect(tmp_path / 'mylar.db')
    con.execute('CREATE TABLE nzblog (IssueID TEXT, NZBName TEXT, SARC TEXT, PROVIDER TEXT, ID TEXT, AltNZBName TEXT, OneOff TEXT)')
    con.execute('CREATE TABLE comics (ComicID TEXT, ComicYear TEXT)')
    con.execute('CREATE TABLE issues (IssueID TEXT, ComicID TEXT, ComicName TEXT, Issue_Number TEXT, Status TEXT)')
    con.execute('CREATE TABLE failed (ID TEXT, Status TEXT, ComicID TEXT, IssueID TEXT, Provider TEXT, '
                'ComicName TEXT, Issue_Number TEXT, NZBName TEXT, DateFailed TEXT)')
    con.execute('INSERT INTO nzblog VALUES (?, ?, NULL, ?, ?, NULL, NULL)', (ISSUEID, NZBNAME, PROVIDER, 'abc123'))
    con.execute('INSERT INTO comics VALUES (?, ?)', (COMICID, '2025'))
    con.execute("INSERT INTO issues VALUES (?, ?, 'Batman', '7', 'Snatched')", (ISSUEID, COMICID))
    con.commit()
    yield tmp_path / 'mylar.db'
    con.close()


def run(issueid):
    q = queue.Queue()
    # Completed-download handling reports the *file* name, which differs from the NZB name.
    Failed.FailedProcessor(nzb_name='Batman.007.(2026).(Digital).(Pyrate-DCP).cbz',
                           nzb_folder='/data/downloads/usenet/complete/' + NZBNAME,
                           queue=q, prov=PROVIDER, id='abc123',
                           issueid=issueid, comicid=COMICID).Process()
    return q.get_nowait()[0]


@pytest.mark.unit
def test_failed_download_found_by_issueid_when_names_differ(db):
    result = run(ISSUEID)
    assert result['mode'] == 'stop'  # FAILED_AUTO off: marked failed, no retry
    con = sqlite3.connect(db)
    assert con.execute('SELECT Status FROM issues WHERE IssueID=?', (ISSUEID,)).fetchone()[0] == 'Failed'
    assert con.execute('SELECT ID, Provider FROM failed WHERE IssueID=?', (ISSUEID,)).fetchone() == ('abc123', PROVIDER)


@pytest.mark.unit
def test_without_issueid_name_mismatch_still_aborts(db):
    assert run(None)['mode'] == 'stop'
    con = sqlite3.connect(db)
    assert con.execute('SELECT Status FROM issues WHERE IssueID=?', (ISSUEID,)).fetchone()[0] == 'Snatched'
