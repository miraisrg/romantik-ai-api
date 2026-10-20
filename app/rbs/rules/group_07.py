# ============================================================
# ROMANTIK AI API
# RBS — Rule Group 07
# ============================================================
#
# Rules:
# - R-III-04
# - R-III-05A
# - R-III-06
# ============================================================

from __future__ import annotations

from datetime import date
from typing import Any

from app.rbs.base import build_rule_result
from app.rbs.helpers import (
    read_field,
    read_schedule_date,
)


# ============================================================
# GROUP VERSION
# ============================================================

GROUP_07_VERSION = "rebuild_schedule_group_v01"


# ============================================================
# SCHEDULE CONFIG
# ============================================================

SCHEDULE_STAGES = (
    "perencanaan_kegiatan",
    "pengumpulan_data",
    "pengolahan_data",
    "analisis",
    "penyajian",
)


# ============================================================
# HELPER
# ============================================================

def compare_schedule_dates(
    record: dict[str, Any],
    previous_stage: str,
    next_stage: str,
) -> dict[str, Any]:
    """
    Bandingkan akhir tahap sebelumnya
    dengan awal tahap berikutnya.
    """

    previous_end = (
        read_schedule_date(
            record,
            previous_stage,
            "akhir",
        )
    )

    next_start = (
        read_schedule_date(
            record,
            next_stage,
            "awal",
        )
    )


    end_value = (
        previous_end[
            "parsed_date"
        ]
    )

    start_value = (
        next_start[
            "parsed_date"
        ]
    )


    comparison = None


    if (
        end_value is not None
        and start_value is not None
    ):

        comparison = (
            date.fromisoformat(
                end_value
            )
            >
            date.fromisoformat(
                start_value
            )
        )


    return {
        "previous_stage":
            previous_stage,

        "next_stage":
            next_stage,

        "previous_end":
            previous_end,

        "next_start":
            next_start,

        "end_after_next_start":
            comparison,
    }


def group_07_result(
    rule_id: str,
    status: str,
    reason: str,
    evidence: dict[str, Any],
    message: str | None = None,
) -> dict[str, Any]:
    """
    Bentuk hasil rule Group 07.
    """

    result = build_rule_result(
        rule_id=rule_id,
        status=status,
        applicability="applicable",
        reason=reason,
        evidence=evidence,
        message=message,
    )

    result["rule_version"] = (
        GROUP_07_VERSION
    )

    return result


# ============================================================
# R-III-04
# ============================================================

def rule_r_iii_04(
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    Tanggal pengajuan historis
    tidak digunakan karena tidak reliabel.
    """

    return group_07_result(
        "R-III-04",
        "not_evaluable",
        (
            "historical_submission_"
            "date_unreliable"
        ),
        {
            "evaluation_context":
                "historical_final_form",

            "submission_date_used":
                False,
        },
    )


# ============================================================
# R-III-05A
# ============================================================

def rule_r_iii_05a(
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    Deteksi kandidat overlap
    antartahapan kegiatan.
    """

    comparisons = [
        compare_schedule_dates(
            record,
            previous_stage,
            next_stage,
        )
        for previous_stage, next_stage
        in zip(
            SCHEDULE_STAGES[:-1],
            SCHEDULE_STAGES[1:],
        )
    ]


    overlap_pairs = [
        {
            "previous_stage":
                item["previous_stage"],

            "next_stage":
                item["next_stage"],
        }
        for item in comparisons
        if (
            item[
                "end_after_next_start"
            ]
            is True
        )
    ]


    unevaluable_pairs = [
        {
            "previous_stage":
                item["previous_stage"],

            "next_stage":
                item["next_stage"],
        }
        for item in comparisons
        if (
            item[
                "end_after_next_start"
            ]
            is None
        )
    ]


    evidence = {
        "comparisons":
            comparisons,

        "overlap_pairs":
            overlap_pairs,

        "unevaluable_pairs":
            unevaluable_pairs,
    }


    if overlap_pairs:

        return group_07_result(
            "R-III-05A",
            "violation",
            (
                "schedule_overlap_"
                "candidate_detected"
            ),
            evidence,
            (
                "Terdeteksi kandidat overlap "
                "antartahapan kegiatan. Tinjau "
                "apakah jadwal yang bertumpang "
                "tindih sesuai dengan rancangan "
                "pelaksanaan kegiatan."
            ),
        )


    if unevaluable_pairs:

        return group_07_result(
            "R-III-05A",
            "not_evaluable",
            (
                "required_schedule_dates_"
                "unavailable_or_unrecognized"
            ),
            evidence,
        )


    return group_07_result(
        "R-III-05A",
        "pass",
        (
            "no_overlap_in_all_"
            "checked_stage_pairs"
        ),
        evidence,
    )


# ============================================================
# R-III-06
# ============================================================

def rule_r_iii_06(
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    Periksa akhir perencanaan terhadap
    awal pengumpulan data.
    """

    comparison = (
        compare_schedule_dates(
            record,
            "perencanaan_kegiatan",
            "pengumpulan_data",
        )
    )


    evidence = {
        "comparison":
            comparison,
    }


    overlaps = (
        comparison[
            "end_after_next_start"
        ]
    )


    if overlaps is None:

        return group_07_result(
            "R-III-06",
            "not_evaluable",
            (
                "required_schedule_dates_"
                "unavailable_or_unrecognized"
            ),
            evidence,
        )


    if overlaps:

        return group_07_result(
            "R-III-06",
            "violation",
            (
                "planning_ends_after_"
                "collection_starts"
            ),
            evidence,
            (
                "Perencanaan/persiapan "
                "berakhir setelah pengumpulan "
                "data dimulai."
            ),
        )


    return group_07_result(
        "R-III-06",
        "pass",
        (
            "planning_ends_on_or_before_"
            "collection_start"
        ),
        evidence,
    )


# ============================================================
# GROUP REGISTRY
# ============================================================

GROUP_07_RULES = {
    "R-III-04": rule_r_iii_04,
    "R-III-05A": rule_r_iii_05a,
    "R-III-06": rule_r_iii_06,
}