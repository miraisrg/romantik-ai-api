# ============================================================
# ROMANTIK AI API
# RBS — Rule Group 11
# ============================================================
#
# Rules:
# - R-ID-02A
# - R-ID-03
# - R-ID-04A
# - R-ID-05A
#
# Final notebook version:
# rebuild_title_year_v01
# ============================================================

from __future__ import annotations

import re
from datetime import date
from typing import Any

from app.rbs.base import build_rule_result
from app.rbs.helpers import (
    normalize_label,
    read_field,
    read_schedule_date,
    resolve_activity,
)


# ============================================================
# GROUP VERSION
# ============================================================

GROUP_11_VERSION = "rebuild_title_year_v01"


# ============================================================
# PATTERN
# ============================================================

TITLE_YEAR_PATTERN = re.compile(
    r"\b(?:19|20)\d{2}\b"
)


# ============================================================
# RESULT BUILDER
# ============================================================

def group_11_result(
    rule_id: str,
    status: str,
    applicability: str,
    reason: str,
    evidence: dict[str, Any],
    message: str | None = None,
) -> dict[str, Any]:
    """
    Bentuk hasil rule Group 11.
    """

    result = build_rule_result(
        rule_id=rule_id,
        status=status,
        applicability=applicability,
        reason=reason,
        evidence=evidence,
        message=message,
    )

    result["rule_version"] = (
        GROUP_11_VERSION
    )

    return result


# ============================================================
# TITLE RULE EVALUATOR
# ============================================================

def evaluate_title_rule(
    record: dict[str, Any],
    rule_id: str,
) -> dict[str, Any]:
    """
    Periksa pola judul menggunakan
    jenis kegiatan secara independen.
    """

    title = read_field(
        record,
        "nama_kegiatan",
    )

    evidence = {
        "title":
            title,
    }


    def finish(
        status: str,
        applicability: str,
        reason: str,
        message: str | None = None,
    ) -> dict[str, Any]:

        return group_11_result(
            rule_id,
            status,
            applicability,
            reason,
            evidence,
            message,
        )


    # ========================================================
    # Activity resolution hanya untuk
    # R-ID-02A dan R-ID-03
    # ========================================================

    if (
        rule_id
        in {
            "R-ID-02A",
            "R-ID-03",
        }
    ):

        activity = (
            resolve_activity(
                record
            )
        )

        evidence[
            "activity"
        ] = activity

        evidence[
            "activity_source"
        ] = [
            read_field(
                record,
                path,
            )
            for path
            in activity.get(
                "evidence_paths",
                [],
            )
        ]


        if (
            activity["value"]
            is None
        ):

            return finish(
                "not_evaluable",
                "unknown",
                "activity_type_unavailable",
            )


        # ----------------------------------------------------
        # R-ID-03 hanya berlaku untuk kompilasi
        # ----------------------------------------------------

        if (
            rule_id
            == "R-ID-03"
            and activity["value"]
            != "kompromin"
        ):

            return finish(
                "pass",
                "not_applicable",
                "non_compilation_activity",
            )


        # ----------------------------------------------------
        # R-ID-02A hanya untuk survei / kompilasi
        # ----------------------------------------------------

        if (
            rule_id
            == "R-ID-02A"
            and activity["value"]
            not in {
                "survei",
                "kompromin",
            }
        ):

            return finish(
                "pass",
                "not_applicable",
                (
                    "activity_outside_"
                    "survey_compilation_check"
                ),
            )


    # ========================================================
    # TITLE AVAILABILITY
    # ========================================================

    if (
        title["state"]
        != "populated"
        or not isinstance(
            title["raw_value"],
            str,
        )
    ):

        return finish(
            "not_evaluable",
            "applicable",
            (
                "title_unavailable_"
                "or_unrecognized"
            ),
        )


    text = normalize_label(
        title["raw_value"]
    )


    # ========================================================
    # R-ID-02A
    # ========================================================

    if (
        rule_id
        == "R-ID-02A"
    ):

        survey_mentioned = (
            "survei" in text
        )

        compilation_mentioned = (
            "kompilasi" in text
        )


        evidence[
            "survey_mentioned"
        ] = survey_mentioned

        evidence[
            "compilation_mentioned"
        ] = compilation_mentioned


        mismatch = (
            (
                activity["value"]
                == "survei"
                and compilation_mentioned
            )
            or
            (
                activity["value"]
                == "kompromin"
                and survey_mentioned
            )
        )


        if mismatch:

            return finish(
                "violation",
                "applicable",
                (
                    "title_activity_"
                    "mismatch_candidate"
                ),
                (
                    "Judul terindikasi tidak "
                    "konsisten dengan jenis kegiatan. "
                    "Tinjau penggunaan kata 'survei' "
                    "atau 'kompilasi'."
                ),
            )


        return finish(
            "pass",
            "applicable",
            (
                "title_activity_mismatch_"
                "not_detected"
            ),
        )


    # ========================================================
    # R-ID-03
    # ========================================================

    if (
        rule_id
        == "R-ID-03"
    ):

        if (
            "kompilasi"
            not in text
        ):

            return finish(
                "violation",
                "applicable",
                (
                    "compilation_keyword_"
                    "not_mentioned"
                ),
                (
                    "Judul kegiatan kompilasi "
                    "produk administrasi belum "
                    "memuat kata 'kompilasi'."
                ),
            )


        return finish(
            "pass",
            "applicable",
            (
                "compilation_keyword_"
                "mentioned"
            ),
        )


    # ========================================================
    # R-ID-04A
    # ========================================================

    years = sorted(
        set(
            TITLE_YEAR_PATTERN.findall(
                title["raw_value"]
            )
        )
    )


    evidence[
        "year_candidates"
    ] = years


    if years:

        return finish(
            "violation",
            "applicable",
            "year_candidate_in_title",
            (
                "Judul terindikasi mencantumkan "
                "tahun kegiatan. Tinjau penulisan "
                "tahun pada judul."
            ),
        )


    return finish(
        "pass",
        "applicable",
        "year_candidate_not_detected",
    )


# ============================================================
# ACTIVITY YEAR PARSER
# ============================================================

def parse_activity_year(
    value: Any,
) -> int | None:
    """
    Terima tahun empat digit berupa
    integer atau string.

    Boolean dan bilangan pecahan
    tidak diterima.
    """

    if isinstance(
        value,
        bool,
    ):

        return None


    if not isinstance(
        value,
        (int, str),
    ):

        return None


    text = str(
        value
    ).strip()


    if not re.fullmatch(
        r"[0-9]{4}",
        text,
    ):

        return None


    year = int(
        text
    )


    return (
        year
        if 1000 <= year <= 9999
        else None
    )


# ============================================================
# R-ID-05A
# ============================================================

def rule_r_id_05a(
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    Bandingkan tahun kegiatan dengan
    tahun awal/akhir pengumpulan data.
    """

    year_reading = read_field(
        record,
        "tahun_kegiatan",
    )

    activity_year = (
        parse_activity_year(
            year_reading[
                "raw_value"
            ]
        )
    )


    start = read_schedule_date(
        record,
        "pengumpulan_data",
        "awal",
    )

    end = read_schedule_date(
        record,
        "pengumpulan_data",
        "akhir",
    )


    evidence = {
        "activity_year":
            year_reading,

        "parsed_activity_year":
            activity_year,

        "collection_start":
            start,

        "collection_end":
            end,

        "comparison_basis":
            (
                "collection_start_"
                "and_end_years"
            ),
    }


    def finish(
        status: str,
        reason: str,
        message: str | None = None,
    ) -> dict[str, Any]:

        return group_11_result(
            "R-ID-05A",
            status,
            "applicable",
            reason,
            evidence,
            message,
        )


    # ========================================================
    # Tahun kegiatan invalid
    # ========================================================

    if (
        activity_year
        is None
    ):

        return finish(
            "not_evaluable",
            (
                "activity_year_"
                "unavailable_or_invalid"
            ),
        )


    # ========================================================
    # Parse tanggal jadwal
    # ========================================================

    start_date = (
        date.fromisoformat(
            start["parsed_date"]
        )
        if (
            start["parsed_date"]
            is not None
        )
        else None
    )


    end_date = (
        date.fromisoformat(
            end["parsed_date"]
        )
        if (
            end["parsed_date"]
            is not None
        )
        else None
    )


    # ========================================================
    # Jadwal terbalik
    # ========================================================

    if (
        start_date
        is not None
        and end_date
        is not None
        and start_date
        > end_date
    ):

        return finish(
            "not_evaluable",
            (
                "collection_schedule_"
                "reversed"
            ),
        )


    # ========================================================
    # Tahun batas jadwal
    # ========================================================

    boundary_years = sorted({
        value.year
        for value
        in (
            start_date,
            end_date,
        )
        if value
        is not None
    })


    evidence[
        "collection_boundary_years"
    ] = boundary_years


    # ========================================================
    # Tahun kegiatan sesuai salah satu boundary
    # ========================================================

    if (
        activity_year
        in boundary_years
    ):

        return finish(
            "pass",
            (
                "activity_year_matches_"
                "collection_boundary_year"
            ),
        )


    # ========================================================
    # Jangan simpulkan mismatch jika
    # jadwal belum lengkap
    # ========================================================

    if (
        start_date
        is None
        or end_date
        is None
    ):

        return finish(
            "not_evaluable",
            (
                "collection_schedule_"
                "incomplete_or_unrecognized"
            ),
        )


    # ========================================================
    # Mismatch
    # ========================================================

    return finish(
        "violation",
        (
            "activity_year_differs_from_"
            "collection_boundary_years"
        ),
        (
            "Tahun kegiatan terindikasi tidak "
            "sesuai dengan tahun awal/akhir "
            "pengumpulan data. Tinjau "
            "kesesuaiannya dengan jadwal "
            "pelaksanaan."
        ),
    )


# ============================================================
# RULE FUNCTIONS
# ============================================================

def rule_r_id_02a(
    record: dict[str, Any],
) -> dict[str, Any]:

    return evaluate_title_rule(
        record,
        "R-ID-02A",
    )


def rule_r_id_03(
    record: dict[str, Any],
) -> dict[str, Any]:

    return evaluate_title_rule(
        record,
        "R-ID-03",
    )


def rule_r_id_04a(
    record: dict[str, Any],
) -> dict[str, Any]:

    return evaluate_title_rule(
        record,
        "R-ID-04A",
    )


# ============================================================
# GROUP REGISTRY
# ============================================================

GROUP_11_RULES = {
    "R-ID-02A":
        rule_r_id_02a,

    "R-ID-03":
        rule_r_id_03,

    "R-ID-04A":
        rule_r_id_04a,

    "R-ID-05A":
        rule_r_id_05a,
}