from services.eventlog_parser import EventLogParser


def test_eventlog_parser_filters_patterns():
    html = """
    <html><body>
    <div>First line</div>
    <div>Error happened here</div>
    </body></html>
    """
    parser = EventLogParser(patterns=["error"])

    entries = parser.parse_entry(html, event_id=42)

    assert entries == [{"event_id": 42, "text": "Error happened here"}]


def test_eventlog_parser_returns_all_when_no_patterns():
    html = "<html><body><p>One</p><p>Two</p></body></html>"
    parser = EventLogParser(patterns=[])

    entries = parser.parse_entry(html, event_id=1)

    assert len(entries) == 2
    assert entries[0]["text"] == "One"
