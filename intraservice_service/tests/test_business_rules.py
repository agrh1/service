import fakeredis

from tasks import _sync_reference


def test_sync_reference_tracks_additions_and_removals():
    client = fakeredis.FakeRedis()
    # seed existing
    client.sadd('intraservice:categories', 1, 2)

    result = _sync_reference(
        'intraservice:categories',
        items=[{"id": 2}, {"id": 3}],
        client=client,
    )

    assert result["added"] == {3}
    assert result["removed"] == {1}
    assert client.smembers('intraservice:categories') == {b'2', b'3'}
