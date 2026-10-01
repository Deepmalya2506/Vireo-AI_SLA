from __future__ import annotations

from pathlib import Path
import sys
import pandas as pd


SLA_MINUTES = {
    "chat": 15,
    "voice": 120,
    "social": 240,
    "email": 480,
}

IST = "Asia/Kolkata"
SAMPLE_PER_CHANNEL = 8
RANDOM_STATE = 42


def find_project_root() -> Path:
    """
    Support both layouts:
        project/tests/validation.py
        project/vireo_sla/tests/validation.py
    """
    here = Path(__file__).resolve()
    candidates = [here.parent.parent, here.parent.parent.parent]

    for candidate in candidates:
        if (
            (candidate / "data").exists()
            and (candidate / "outputs").exists()
        ):
            return candidate

    raise FileNotFoundError(
        "Could not locate the project root. Expected data/ and outputs/ "
        "above tests/validation.py."
    )


def fail(message: str) -> None:
    raise AssertionError(message)


def get_shift(hour: int) -> str:
    """Independent reproduction of Vireo's IST shift rule."""
    if 6 <= hour < 14:
        return "Morning"
    if 14 <= hour < 22:
        return "Day"
    return "Night"


def canonicalize_independently(raw: pd.DataFrame) -> pd.DataFrame:
    """
    Independently reproduce the migration-deduplication rule:
    for duplicate ticket_ids, prefer the helpdesk copy.
    """
    out = raw.copy()

    priority = {"helpdesk": 0, "legacy_fd": 1}
    out["_priority"] = out["source_system"].map(priority)

    if out["_priority"].isna().any():
        fail("Unexpected source_system value found in raw tickets.")

    return (
        out.sort_values(["ticket_id", "_priority"])
        .drop_duplicates("ticket_id", keep="first")
        .drop(columns="_priority")
        .reset_index(drop=True)
    )


def compare_series(left: pd.Series, right: pd.Series) -> pd.Series:
    """
    Compare two Series safely.

    Important: pandas treats bool as a numeric dtype, so boolean values
    must NOT be compared using subtraction.
    """
    both_na = left.isna() & right.isna()

    if (
        pd.api.types.is_bool_dtype(left)
        or pd.api.types.is_bool_dtype(right)
    ):
        equal = left.eq(right)
        equal = equal | both_na
        return equal.fillna(False)

    if (
        pd.api.types.is_numeric_dtype(left)
        or pd.api.types.is_numeric_dtype(right)
    ):
        left_num = pd.to_numeric(left, errors="coerce")
        right_num = pd.to_numeric(right, errors="coerce")

        equal = (left_num - right_num).abs() <= 1e-9
        equal = equal | both_na
        return equal.fillna(False)

    equal = left.eq(right)
    equal = equal | both_na
    return equal.fillna(False)


def main() -> int:
    root = find_project_root()
    data_dir = root / "data"
    output_dir = root / "outputs"

    raw_path = data_dir / "tickets.csv"
    prod_path = output_dir / "ticket_sla.csv"

    if not raw_path.exists():
        fail(f"Missing raw input: {raw_path}")

    if not prod_path.exists():
        fail(
            f"Missing derived output: {prod_path}. "
            "Run main.py first."
        )

    raw = pd.read_csv(raw_path)
    prod = pd.read_csv(prod_path)
    canonical = canonicalize_independently(raw)

    # ------------------------------------------------------------
    # 1. Independently recompute ticket-level deterministic fields
    # ------------------------------------------------------------
    for col in ["created_at", "first_response_at", "resolved_at"]:
        canonical[f"{col}_utc"] = pd.to_datetime(
            canonical[col], utc=True
        )

    canonical["created_at_ist_check"] = (
        canonical["created_at_utc"].dt.tz_convert(IST)
    )
    canonical["first_response_at_ist_check"] = (
        canonical["first_response_at_utc"].dt.tz_convert(IST)
    )
    canonical["resolved_at_ist_check"] = (
        canonical["resolved_at_utc"].dt.tz_convert(IST)
    )

    canonical["response_minutes_check"] = (
        canonical["first_response_at_utc"]
        - canonical["created_at_utc"]
    ).dt.total_seconds() / 60

    canonical["sla_target_minutes_check"] = (
        canonical["channel"].map(SLA_MINUTES)
    )

    canonical["breach_check"] = (
        canonical["response_minutes_check"]
        > canonical["sla_target_minutes_check"]
    )

    canonical["arrival_hour_check"] = (
        canonical["created_at_ist_check"].dt.hour
    )
    canonical["arrival_shift_check"] = (
        canonical["arrival_hour_check"].map(get_shift)
    )

    canonical["response_hour_check"] = (
        canonical["first_response_at_ist_check"].dt.hour
    )
    canonical["response_shift_check"] = (
        canonical["response_hour_check"].map(get_shift)
    )

    # ------------------------------------------------------------
    # 2. Structural checks
    # ------------------------------------------------------------
    checks: list[tuple[str, bool, str]] = []

    checks.append((
        "Raw row count is 11,816",
        len(raw) == 11816,
        f"got {len(raw):,}",
    ))

    checks.append((
        "Canonical ticket IDs are unique",
        canonical["ticket_id"].is_unique,
        "",
    ))

    checks.append((
        "Production ticket IDs are unique",
        prod["ticket_id"].is_unique,
        "",
    ))

    checks.append((
        "Canonical row count is 11,200",
        len(canonical) == 11200,
        f"got {len(canonical):,}",
    ))

    checks.append((
        "No negative response times",
        (canonical["response_minutes_check"] >= 0).all(),
        "",
    ))

    checks.append((
        "All channels have SLA targets",
        canonical["sla_target_minutes_check"].notna().all(),
        "",
    ))

    checks.append((
        "All tickets have an arrival shift",
        canonical["arrival_shift_check"].notna().all(),
        "",
    ))

    checks.append((
        "All tickets with a first response have a response shift",
        canonical.loc[
            canonical["first_response_at_utc"].notna(),
            "response_shift_check",
        ].notna().all(),
        "",
    ))

    # ------------------------------------------------------------
    # 3. Required production columns + full population comparison
    # ------------------------------------------------------------
    comparisons = {
        "response_minutes": "response_minutes_check",
        "sla_target_minutes": "sla_target_minutes_check",
        "breach": "breach_check",
        "arrival_hour": "arrival_hour_check",
        "arrival_shift": "arrival_shift_check",
        "response_hour": "response_hour_check",
        "response_shift": "response_shift_check",
    }

    missing_prod = [
        col for col in comparisons if col not in prod.columns
    ]

    checks.append((
        "Production output contains all validated fields",
        len(missing_prod) == 0,
        f"missing: {', '.join(missing_prod)}" if missing_prod else "",
    ))

    if set(canonical["ticket_id"]) != set(prod["ticket_id"]):
        fail(
            "Production output ticket IDs do not match the independently "
            "canonicalized raw dataset."
        )

    canonical_indexed = canonical.set_index("ticket_id")
    prod_indexed = prod.set_index("ticket_id")

    mismatch_counts: dict[str, int] = {}

    if not missing_prod:
        for production_col, independent_col in comparisons.items():
            left = prod_indexed[production_col]
            right = canonical_indexed[independent_col]

            equal = compare_series(left, right)
            mismatches = int((~equal).sum())
            mismatch_counts[production_col] = mismatches

            checks.append((
                f"Independent check: {production_col}",
                mismatches == 0,
                f"{mismatches} mismatches",
            ))

    # ------------------------------------------------------------
    # 4. Independent 32-ticket stratified audit
    # ------------------------------------------------------------
    sample = (
        canonical.groupby("channel", group_keys=False)
        .sample(
            n=SAMPLE_PER_CHANNEL,
            random_state=RANDOM_STATE,
        )
        .copy()
    )

    audit_mismatches = None
    audit = pd.DataFrame()

    if not missing_prod:
        sample_prod = (
            prod_indexed.loc[sample["ticket_id"]]
            .reset_index()
        )

        sample_independent = (
            sample.set_index("ticket_id")
            .loc[sample_prod["ticket_id"]]
            .reset_index()
        )

        audit = pd.DataFrame({
            "ticket_id": sample_prod["ticket_id"],
            "channel": sample_prod["channel"],

            "recomputed_response_minutes":
                sample_independent["response_minutes_check"],
            "production_response_minutes":
                sample_prod["response_minutes"],

            "recomputed_sla_target_minutes":
                sample_independent["sla_target_minutes_check"],
            "production_sla_target_minutes":
                sample_prod["sla_target_minutes"],

            "recomputed_breach":
                sample_independent["breach_check"].astype(bool),
            "production_breach":
                sample_prod["breach"].astype(bool),

            "recomputed_arrival_shift":
                sample_independent["arrival_shift_check"],
            "production_arrival_shift":
                sample_prod["arrival_shift"],

            "recomputed_response_shift":
                sample_independent["response_shift_check"],
            "production_response_shift":
                sample_prod["response_shift"],
        })

        checks_per_row = (
            ~compare_series(
                audit["recomputed_response_minutes"],
                audit["production_response_minutes"],
            )
        ) | (
            ~compare_series(
                audit["recomputed_sla_target_minutes"],
                audit["production_sla_target_minutes"],
            )
        ) | (
            ~compare_series(
                audit["recomputed_breach"],
                audit["production_breach"],
            )
        ) | (
            ~compare_series(
                audit["recomputed_arrival_shift"],
                audit["production_arrival_shift"],
            )
        ) | (
            ~compare_series(
                audit["recomputed_response_shift"],
                audit["production_response_shift"],
            )
        )

        audit["mismatch"] = checks_per_row
        audit_mismatches = int(audit["mismatch"].sum())

        checks.append((
            "32-ticket stratified independent audit",
            audit_mismatches == 0,
            f"{audit_mismatches}/32 mismatches",
        ))

    # ------------------------------------------------------------
    # 5. Boundary tests
    # Exactly at target = NOT breach.
    # One second beyond target = breach.
    # ------------------------------------------------------------
    boundary = pd.DataFrame({
        "channel": [
            "chat", "chat",
            "email", "email",
            "voice", "voice",
            "social", "social",
        ],
        "response_minutes": [
            15, 15 + 1 / 60,
            480, 480 + 1 / 60,
            120, 120 + 1 / 60,
            240, 240 + 1 / 60,
        ],
    })

    boundary["target"] = boundary["channel"].map(SLA_MINUTES)
    boundary["breach"] = (
        boundary["response_minutes"]
        > boundary["target"]
    )

    expected = [
        False, True,
        False, True,
        False, True,
        False, True,
    ]

    boundary_pass = boundary["breach"].tolist() == expected

    checks.append((
        "SLA boundary rule",
        boundary_pass,
        "exact target = no breach; target + 1 second = breach",
    ))

    # ------------------------------------------------------------
    # 6. Completed-ticket sanity check
    # ------------------------------------------------------------
    completed = canonical[
        canonical["status"].isin(["resolved", "closed"])
    ].copy()

    response_before_resolution = (
        completed["first_response_at_utc"]
        <= completed["resolved_at_utc"]
    ).all()

    checks.append((
        "Completed tickets have response at or before resolution",
        bool(response_before_resolution),
        "",
    ))

    # ------------------------------------------------------------
    # 7. Persist outputs
    # ------------------------------------------------------------
    checks_df = pd.DataFrame([
        {
            "check": name,
            "pass": bool(passed),
            "detail": detail,
        }
        for name, passed, detail in checks
    ])

    audit_path = output_dir / "independent_validation_sample.csv"
    checks_path = output_dir / "validation_checks_independent.csv"
    report_path = output_dir / "validation_report.txt"

    if not audit.empty:
        audit.to_csv(audit_path, index=False)

    checks_df.to_csv(checks_path, index=False)

    independent_breaches = int(
        canonical["breach_check"].sum()
    )
    independent_breach_rate = float(
        canonical["breach_check"].mean() * 100
    )

    breach_mismatches = mismatch_counts.get("breach", None)
    audit_rate = (
        audit_mismatches / 32 * 100
        if audit_mismatches is not None
        else None
    )

    report_lines = [
        "VIREO SLA — INDEPENDENT VALIDATION REPORT",
        "=" * 52,
        f"Project root: {root}",
        f"Raw ticket rows: {len(raw):,}",
        f"Canonical tickets: {len(canonical):,}",
        f"Independent breach count: {independent_breaches:,}",
        f"Independent breach rate: {independent_breach_rate:.2f}%",
        "",
        (
            "Full-population independent breach-flag mismatches: "
            + (
                str(breach_mismatches)
                if breach_mismatches is not None
                else "NOT RUN — missing production field(s)"
            )
        ),
        (
            "32-ticket stratified audit mismatches: "
            + (
                f"{audit_mismatches}/32"
                if audit_mismatches is not None
                else "NOT RUN — missing production field(s)"
            )
        ),
        (
            "32-ticket audit error rate: "
            + (
                f"{audit_rate:.2f}%"
                if audit_rate is not None
                else "N/A"
            )
        ),
        "",
        "Per-field mismatch counts:",
    ]

    for field in comparisons:
        report_lines.append(
            f"  {field}: {mismatch_counts.get(field, 'NOT RUN')}"
        )

    report_lines.extend([
        "",
        f"Boundary test passed: {boundary_pass}",
        (
            "Completed-ticket response-before-resolution check: "
            f"{bool(response_before_resolution)}"
        ),
        "",
        (
            "Result: PASS — all validation checks passed."
            if checks_df["pass"].all()
            else
            "Result: FAIL — inspect validation_checks_independent.csv "
            "and validation_report.txt."
        ),
    ])

    report_path.write_text(
        "\n".join(report_lines),
        encoding="utf-8",
    )

    print("\n".join(report_lines))

    return 0 if checks_df["pass"].all() else 1


if __name__ == "__main__":
    sys.exit(main())
