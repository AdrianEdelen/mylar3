import pytest

from mylar import search

PROWLARR_NZB = 'http://prowlarr:9696/6/download?apikey=KEY&link=TElOSzE&file=Absolute+Batman+001+(2024)+(Digital)'
PROWLARR_NZB_OTHER = 'http://prowlarr:9696/6/download?apikey=KEY&link=TElOSzI&file=Absolute+Batman+002+(2024)+(Digital)'
PROWLARR_TORRENT = 'http://prowlarr:9696/3/download?apikey=KEY&link=TElOSzM&file=Batman+2025+%2302'
JACKETT_TORRENT = 'http://jackett:9117/dl/mam/?jackett_apikey=KEY&path=UEFUSA&file=Batman+002+(2025)'


@pytest.mark.unit
def test_proxy_newznab_ids_are_per_release():
    first = search.generate_id('newznab', PROWLARR_NZB, 'Absolute Batman')
    second = search.generate_id('newznab', PROWLARR_NZB_OTHER, 'Absolute Batman')
    assert first != 'download'
    assert first != second


@pytest.mark.unit
def test_proxy_ids_are_stable_for_the_same_release():
    assert search.generate_id('newznab', PROWLARR_NZB, 'Absolute Batman') == \
        search.generate_id('newznab', PROWLARR_NZB, 'Absolute Batman')


@pytest.mark.unit
@pytest.mark.parametrize('link', [PROWLARR_TORRENT, JACKETT_TORRENT])
def test_proxy_torznab_ids_use_release_name(link):
    nzbid = search.generate_id('torznab', link, 'Batman')
    assert nzbid.startswith('proxy-')
    assert 'apikey' not in nzbid


@pytest.mark.unit
def test_provider_stat_dict_is_accepted():
    assert search.generate_id({'type': 'newznab'}, PROWLARR_NZB, 'Absolute Batman') == \
        search.generate_id('newznab', PROWLARR_NZB, 'Absolute Batman')


@pytest.mark.unit
@pytest.mark.parametrize('guid,expected', [
    ('https://www.myanonamouse.net/t/123456', '123456'),
    ('https://www.torrentleech.org/torrent/241234', '241234'),
])
def test_torznab_guid_uses_release_id_not_section(guid, expected):
    assert search.generate_id('torznab', guid, 'Batman') == expected


@pytest.mark.unit
@pytest.mark.parametrize('link,expected', [
    ('https://api.nzbgeek.info/api?t=get&id=4f3c2a1b9e8d&apikey=KEY', '4f3c2a1b9e8d'),
    ('https://api.nzb.life/getnzb/9a8b7c6d5e4f.nzb&i=123&r=KEY', '9a8b7c6d5e4f'),
])
def test_direct_newznab_ids_unchanged(link, expected):
    assert search.generate_id('newznab', link, 'Absolute Batman') == expected
