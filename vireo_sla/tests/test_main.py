import pandas as pd

from main import SLA_MINUTES, canonicalize_tickets, get_shift


def test_shift_boundaries():
    assert get_shift(5) == "Night"
    assert get_shift(6) == "Morning"
    assert get_shift(13) == "Morning"
    assert get_shift(14) == "Day"
    assert get_shift(21) == "Day"
    assert get_shift(22) == "Night"
    assert get_shift(23) == "Night"


def test_sla_boundaries():
    df = pd.DataFrame(
        {
            "channel": ["chat", "chat", "chat", "email", "email", "email"],
            "response_minutes": [14, 15, 16, 479, 480, 481],
        }
    )
    targets = df["channel"].map(SLA_MINUTES)
    breach = df["response_minutes"] > targets
    assert breach.tolist() == [False, False, True, False, False, True]


def test_canonicalize_prefers_helpdesk():
    df = pd.DataFrame(
        {
            "ticket_id": ["T1", "T1", "T2"],
            "source_system": ["legacy_fd", "helpdesk", "helpdesk"],
            "csat_score": [0.0, 4.0, 5.0],
        }
    )
    out = canonicalize_tickets(df)
    assert out["ticket_id"].is_unique
    assert out.loc[out["ticket_id"] == "T1", "source_system"].iloc[0] == "helpdesk"
