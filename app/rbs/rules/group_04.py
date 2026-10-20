# ============================================================
# ROMANTIK AI API
# RBS — Rule Group 04
# ============================================================
#
# Rules:
# - R-V-14A
# - R-V-12
# - R-V-11
#
# Catatan:
# Rule dimigrasikan dari implementasi standalone notebook,
# tetapi dikelompokkan di sini untuk konsistensi struktur API.
# ============================================================

from __future__ import annotations

from typing import Any

from app.rbs.base import build_rule_result

from app.rbs.helpers import (
    GROUP_03_PATHS,
    normalize_label,
    read_alternatives,
    read_field,
    resolve_activity,
)

from decimal import Decimal

import re

# ============================================================
# RULE VERSIONS
# ============================================================

R_V_14A_VERSION = "rebuild_r_v_14a_v01"

R_V_12_VERSION = "rebuild_r_v_12_v01"


ERROR_TYPE_PATTERN = re.compile(
    r"\b(?:rse|cv|moe|alpha)\b|"
    r"\bmargin\s+of\s+error\b|α",
    flags=re.IGNORECASE,
)

R_V_11_VERSION = "rebuild_r_v_11_v01"

SAMPLING_LIMIT_PERCENT = Decimal("5")


_MEASURE_LABEL = (
    r"(?:rse|cv|moe|margin\s+of\s+error|alpha|α)"
)

_PERCENT_NUMBER = (
    r"(?P<percent>[0-9]+(?:[.,][0-9]+)?)"
)

_PERCENT_UNIT = (
    r"(?:%|persen|percent)"
)


SAMPLING_PERCENT_PATTERN = re.compile(
    rf"(?:{_MEASURE_LABEL}\s*[:=]?\s*)?"
    rf"{_PERCENT_NUMBER}\s*{_PERCENT_UNIT}"
    rf"(?:\s*\(\s*{_MEASURE_LABEL}\s*\))?",
    flags=re.IGNORECASE,
)

def parse_explicit_sampling_percent(
    raw_value: Any,
) -> dict[str, Any]:
    """
    Baca satu persentase eksplisit
    dengan pencocokan teks utuh.
    """

    if not isinstance(raw_value, str):

        return {
            "value": None,
            "reason": (
                "sampling_error_unit_or_"
                "format_unrecognized"
            ),
        }


    text = normalize_label(
        raw_value
    )


    if text in {
        "",
        "-",
        "–",
        "—",
    }:

        return {
            "value": None,
            "reason": (
                "sampling_error_empty_marker"
            ),
        }


    match = (
        SAMPLING_PERCENT_PATTERN
        .fullmatch(text)
    )


    if match is None:

        return {
            "value": None,
            "reason": (
                "sampling_error_percent_"
                "not_unambiguous"
            ),
        }


    percent = Decimal(
        match.group(
            "percent"
        ).replace(
            ",",
            ".",
        )
    )


    return {
        "value": percent,
        "reason": (
            "explicit_percent_recognized"
        ),
    }

# ============================================================
# R-V-14A
# ============================================================

UNIT_FIELD_PATHS = {
    "unit_sampel":
        "form.blok_v.unit_sampel",

    "unit_observasi":
        "form.blok_v.unit_observasi",

    "unit_analisis":
        "form.blok_vii.unit_analisis",
}


def rule_r_v_14a(
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    Periksa kelengkapan unit sampel,
    unit observasi, dan unit analisis
    untuk kegiatan survei.

    Kebijakan missing value:
    - explicit empty -> violation
    - null / absent -> not_evaluable
    """

    activity = resolve_activity(
        record
    )

    readings = {
        concept: read_field(
            record,
            path,
        )
        for concept, path
        in UNIT_FIELD_PATHS.items()
    }

    evidence = {
        "activity": activity,

        "activity_source": [
            read_field(
                record,
                path,
            )
            for path in activity.get(
                "evidence_paths",
                [],
            )
        ],

        "units": readings,
    }

    message = None


    # --------------------------------------------------------
    # Activity tidak dapat ditentukan
    # --------------------------------------------------------

    if activity["value"] is None:

        status = "not_evaluable"
        applicability = "unknown"
        reason = (
            "activity_type_unavailable"
        )


    # --------------------------------------------------------
    # Rule hanya berlaku pada survei
    # --------------------------------------------------------

    elif activity["value"] != "survei":

        status = "pass"

        applicability = (
            "not_applicable"
        )

        reason = (
            "non_survey_activity"
        )


    # --------------------------------------------------------
    # Survei
    # --------------------------------------------------------

    else:

        applicability = "applicable"

        empty_units = [
            concept
            for concept, reading
            in readings.items()
            if reading["state"] in {
                "empty_string",
                "empty_list",
                "empty_object",
            }
        ]

        unavailable_units = [
            concept
            for concept, reading
            in readings.items()
            if reading["state"] not in {
                "populated",
                "empty_string",
                "empty_list",
                "empty_object",
            }
        ]

        evidence[
            "explicitly_empty_units"
        ] = empty_units

        evidence[
            "unavailable_units"
        ] = unavailable_units


        if empty_units:

            status = "violation"

            reason = (
                "required_units_"
                "explicitly_empty"
            )

            message = (
                "Isian unit berikut masih kosong: "
                + ", ".join(empty_units)
                + ". Lengkapi unit sampel, "
                "unit observasi, dan unit analisis "
                "sesuai rancangan kegiatan."
            )


        elif unavailable_units:

            status = "not_evaluable"

            reason = (
                "required_units_unavailable"
            )


        else:

            status = "pass"

            reason = (
                "required_units_present"
            )


    result = build_rule_result(
        rule_id="R-V-14A",
        status=status,
        applicability=applicability,
        reason=reason,
        evidence=evidence,
        message=message,
    )

    result["rule_version"] = (
        R_V_14A_VERSION
    )

    return result

def rule_r_v_12(
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    Periksa penyebutan jenis ukuran
    pada isian sampling error.

    Scope:
    hanya mendeteksi penyebutan jenis ukuran,
    bukan memvalidasi nilai sampling error.
    """

    activity = resolve_activity(
        record
    )

    reading = read_alternatives(
        record,
        GROUP_03_PATHS[
            "sampling_error"
        ],
    )

    evidence = {
        "activity": activity,

        "activity_source": [
            read_field(
                record,
                path,
            )
            for path in activity.get(
                "evidence_paths",
                [],
            )
        ],

        "sampling_error": reading,
    }


    def finish(
        status: str,
        applicability: str,
        reason: str,
        message: str | None = None,
    ) -> dict[str, Any]:

        result = build_rule_result(
            rule_id="R-V-12",
            status=status,
            applicability=applicability,
            reason=reason,
            evidence=evidence,
            message=message,
        )

        result["rule_version"] = (
            R_V_12_VERSION
        )

        return result


    if activity["value"] is None:

        return finish(
            "not_evaluable",
            "unknown",
            "activity_type_unavailable",
        )


    if activity["value"] != "survei":

        return finish(
            "pass",
            "not_applicable",
            "non_survey_activity",
        )


    if reading["status"] != "selected":

        return finish(
            "not_evaluable",
            "applicable",
            "sampling_error_unavailable_or_conflicting",
        )


    raw_value = reading[
        "raw_value"
    ]


    if (
        isinstance(
            raw_value,
            bool,
        )
        or not isinstance(
            raw_value,
            (str, int, float),
        )
    ):

        return finish(
            "not_evaluable",
            "applicable",
            "sampling_error_format_unrecognized",
        )


    text = normalize_label(
        str(raw_value)
    )


    if text in {
        "",
        "-",
        "–",
        "—",
    }:

        return finish(
            "not_evaluable",
            "applicable",
            "sampling_error_empty_marker",
        )


    matches = sorted({
        match.group(0)
        for match
        in ERROR_TYPE_PATTERN.finditer(
            text
        )
    })

    evidence[
        "matched_measure_labels"
    ] = matches


    if matches:

        return finish(
            "pass",
            "applicable",
            "sampling_error_measure_mentioned",
        )


    return finish(
        "violation",
        "applicable",
        "sampling_error_measure_not_mentioned",
        (
            "Isian sampling error belum "
            "mencantumkan jenis ukuran yang "
            "dikenali aturan. Jelaskan jenis "
            "ukuran yang digunakan sesuai "
            "rancangan kegiatan."
        ),
    )

def rule_r_v_11(
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    Bandingkan persentase sampling error
    dengan ambang 5 persen.
    """

    activity = resolve_activity(
        record
    )

    reading = read_alternatives(
        record,
        GROUP_03_PATHS[
            "sampling_error"
        ],
    )


    evidence = {
        "activity": activity,

        "activity_source": [
            read_field(
                record,
                path,
            )
            for path in activity.get(
                "evidence_paths",
                [],
            )
        ],

        "sampling_error": reading,

        "threshold_percent": float(
            SAMPLING_LIMIT_PERCENT
        ),
    }


    def finish(
        status: str,
        applicability: str,
        reason: str,
        message: str | None = None,
    ) -> dict[str, Any]:

        result = build_rule_result(
            rule_id="R-V-11",
            status=status,
            applicability=applicability,
            reason=reason,
            evidence=evidence,
            message=message,
        )

        result["rule_version"] = (
            R_V_11_VERSION
        )

        return result


    if activity["value"] is None:

        return finish(
            "not_evaluable",
            "unknown",
            "activity_type_unavailable",
        )


    if activity["value"] != "survei":

        return finish(
            "pass",
            "not_applicable",
            "non_survey_activity",
        )


    if reading["status"] != "selected":

        return finish(
            "not_evaluable",
            "applicable",
            (
                "sampling_error_unavailable_"
                "or_conflicting"
            ),
        )


    parsed = (
        parse_explicit_sampling_percent(
            reading["raw_value"]
        )
    )

    evidence[
        "parsing_reason"
    ] = parsed["reason"]


    if parsed["value"] is None:

        return finish(
            "not_evaluable",
            "applicable",
            parsed["reason"],
        )


    percent = parsed[
        "value"
    ]

    evidence[
        "parsed_percent"
    ] = float(percent)


    if percent > SAMPLING_LIMIT_PERCENT:

        return finish(
            "violation",
            "applicable",
            "sampling_error_above_threshold",
            (
                "Nilai sampling error yang "
                "tercantum lebih dari 5%. "
                "Tinjau kembali sesuai jenis "
                "ukuran dan rancangan kegiatan."
            ),
        )


    return finish(
        "pass",
        "applicable",
        "sampling_error_within_threshold",
    )

# ============================================================
# GROUP REGISTRY
# ============================================================

GROUP_04_RULES = {
    "R-V-14A": rule_r_v_14a,
    "R-V-12": rule_r_v_12,
    "R-V-11": rule_r_v_11,
}