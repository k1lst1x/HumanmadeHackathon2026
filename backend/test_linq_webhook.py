from app import extract_linq_message


def test_extract_linq_message_2026_payload():
    payload = {
        "event_type": "message.received",
        "data": {
            "chat": {"id": "chat_123"},
            "direction": "inbound",
            "sender_handle": {"handle": "+15551234567"},
            "parts": [{"type": "text", "value": "Need a seed deck, 10 slides"}],
        },
    }

    message = extract_linq_message(payload)

    assert message["thread_id"] == "chat_123"
    assert message["sender"] == "+15551234567"
    assert message["text"] == "Need a seed deck, 10 slides"


def test_extract_linq_message_2025_payload():
    payload = {
        "event_type": "message.received",
        "data": {
            "chat_id": "chat_456",
            "from": "+15557654321",
            "is_from_me": False,
            "message": {
                "parts": [{"type": "text", "value": "Can you build a pitch deck?"}],
            },
        },
    }

    message = extract_linq_message(payload)

    assert message["thread_id"] == "chat_456"
    assert message["sender"] == "+15557654321"
    assert message["text"] == "Can you build a pitch deck?"
