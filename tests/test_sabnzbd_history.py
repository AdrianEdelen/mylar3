from types import SimpleNamespace

import pytest
import requests

import mylar
from mylar import sabnzbd

NZO = 'SABnzbd_nzo_abc123'
NZBINFO = {'nzo_id': NZO, 'issueid': '700011', 'comicid': '160860',
           'download_info': {'provider': 'NZBgeek (Prowlarr)', 'id': 'proxy-x'}}


def history_slot(stage_log, storage=None, fail_message='Aborted, cannot be completed'):
    return {'nzo_id': NZO, 'status': 'Failed', 'nzb_name': 'Absolute.Superman.013.2025.Digital.Shan-Empire.nzb',
            'storage': storage, 'stage_log': stage_log, 'fail_message': fail_message, 'script': None}


@pytest.fixture
def sab(monkeypatch):
    def configure(slot, failed_handling=True):
        monkeypatch.setattr(mylar, 'CONFIG', SimpleNamespace(
            SAB_HOST='http://sabnzbd:8080', SAB_APIKEY='KEY', SAB_CATEGORY='comics', SAB_VERSION='5.1.3',
            FAILED_DOWNLOAD_HANDLING=failed_handling, SAB_REMOVE_FAILED=False, SAB_REMOVE_COMPLETED=False,
            SAB_MOVING_DELAY=0), raising=False)
        response = SimpleNamespace(json=lambda: {'history': {'slots': [slot]}})
        monkeypatch.setattr(requests, 'get', lambda *a, **k: response)
        return sabnzbd.SABnzbd(params=None).historycheck(dict(NZBINFO))
    return configure


@pytest.mark.unit
def test_download_stage_abort_is_a_failed_download(sab):
    # missing articles: SABnzbd aborts in the Download stage, no Unpack/Repair entry
    result = sab(history_slot([{'name': 'Download', 'actions': ['Aborted, cannot be completed']}]))
    assert result['status'] is True
    assert result['failed'] is True
    assert result['issueid'] == '700011'
    assert result['location'] is None


@pytest.mark.unit
def test_repair_failure_is_a_failed_download(sab):
    result = sab(history_slot([{'name': 'Repair', 'actions': ['Repair failed, not enough repair blocks']}],
                              storage='/data/downloads/usenet/complete/_FAILED_x/x.cbz'))
    assert result['failed'] is True
    assert result['location'] == '/data/downloads/usenet/complete/_FAILED_x'


@pytest.mark.unit
def test_failed_handling_disabled_keeps_old_behaviour(sab):
    result = sab(history_slot([{'name': 'Download', 'actions': ['Aborted']}]), failed_handling=False)
    assert result == {'status': 'failed_in_sab', 'failed': False}
