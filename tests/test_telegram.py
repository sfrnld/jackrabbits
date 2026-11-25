import os, pytest
from tests.fake_telegram import FakeTelegram
from app import settings
from app.telegram import Telegram, TelegramError, split_text

def test_client_basics_and_photo_multipart():
    f = FakeTelegram(); tg = Telegram(f.token, client=f.client())
    assert tg.get_me()["username"] == "SalesStudioTestBot"
    tg.send_message(5, "halo"); tg.send_photo(5, b"\x89PNGfake", "cap")
    assert f.sent[0]["text"] == "halo" and f.sent[1]["method"] == "sendPhoto" and f.sent[1]["caption"] == "cap" and f.sent[1]["files"]["photo"] == b"\x89PNGfake"

def test_caption_is_capped_at_1024():
    f = FakeTelegram(); Telegram(f.token, client=f.client()).send_photo(5, b"x", "a" * 5000)
    assert len(f.sent[0]["caption"]) <= 1024

def test_media_group_for_several_charts():
    f = FakeTelegram(); Telegram(f.token, client=f.client()).send_media_group(5, [b"a", b"b"], "cap")
    assert f.sent[0]["method"] == "sendMediaGroup" and set(f.sent[0]["files"]) == {"p0", "p1"}

def test_split_text_respects_limit_and_lines():
    t = "\n".join(f"baris {i} " + "x" * 80 for i in range(100))
    parts = split_text(t, 1000); assert all(len(p) <= 1000 for p in parts) and "\n".join(parts) == t

def test_errors_are_clear_and_never_leak_the_token():
    f = FakeTelegram(fail_chats=[9]); tg = Telegram(f.token, client=f.client())
    with pytest.raises(TelegramError) as e: tg.send_message(9, "x")
    assert e.value.code == 403 and "blocked" in str(e.value).lower() and f.token not in str(e.value)
    off = FakeTelegram(offline=True)
    with pytest.raises(TelegramError) as e: Telegram(off.token, client=off.client()).get_me()
    assert e.value.offline is True and off.token not in str(e.value)
    with pytest.raises(TelegramError) as e: Telegram("0:WRONG", client=f.client()).get_me()
    assert e.value.code == 401 and "WRONG" not in str(e.value)

def test_env_roundtrip_keeps_other_lines(tmp_path, monkeypatch):
    env = tmp_path / ".env"; env.write_text("# keep\nOTHER=1\nTELEGRAM_BOT_TOKEN=old\n")
    monkeypatch.setenv("SALES_STUDIO_ENV", str(env)); monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    assert settings.get("TELEGRAM_BOT_TOKEN") == "old"
    settings.set_value("TELEGRAM_BOT_TOKEN", "new:tok")
    assert settings.get("TELEGRAM_BOT_TOKEN") == "new:tok" and "# keep" in env.read_text() and "OTHER=1" in env.read_text()
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
