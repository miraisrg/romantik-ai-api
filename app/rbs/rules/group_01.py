# ============================================================
# ROMANTIK AI API
# RBS — Rule Group 01
# ============================================================
#
# Rules:
# - R-IV-07
# - R-VI-01
# - R-VI-05
# - R-VI-08
# ============================================================

from __future__ import annotations

from typing import Any

from app.rbs.base import (
    build_rule_result,
    parse_staff_count,
)

from app.rbs.helpers import (
    parse_boolean,
    read_field,
    resolve_activity,
    resolve_region_coverage,
)


# ============================================================
# R-IV-07
# ============================================================

def rule_r_iv_07(
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    Daftar wilayah wajib tersedia
    untuk cakupan sebagian wilayah.
    """

    context = resolve_region_coverage(
        record
    )

    evidence = {
        "coverage": (
            context["coverage_evidence"]
        ),

        "regions": (
            context["regions_evidence"]
        ),

        "regions_status": (
            context["regions_status"]
        ),
    }


    if context["coverage"] is None:

        return build_rule_result(
            "R-IV-07",
            "not_evaluable",
            "unknown",
            "coverage_unavailable_or_unrecognized",
            evidence,
        )


    if (
        context["coverage"]
        == "national"
    ):

        return build_rule_result(
            "R-IV-07",
            "pass",
            "not_applicable",
            "national_coverage",
            evidence,
        )


    if (
        context["regions_status"]
        == "recognized_list"
    ):

        return build_rule_result(
            "R-IV-07",
            "pass",
            "applicable",
            "region_list_present",
            evidence,
        )


    if (
        context["regions_status"]
        in {
            "empty_list",
            "empty_marker",
        }
    ):

        return build_rule_result(
            "R-IV-07",
            "violation",
            "applicable",
            "region_list_empty",
            evidence,
            (
                "Daftar wilayah wajib diisi apabila "
                "cakupan pengumpulan data hanya "
                "sebagian wilayah Indonesia."
            ),
        )


    return build_rule_result(
        "R-IV-07",
        "not_evaluable",
        "applicable",
        "region_list_unavailable_or_unreadable",
        evidence,
    )


# ============================================================
# R-VI-01
# ============================================================

def rule_r_vi_01(
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    Kegiatan nonkompilasi disarankan
    melakukan uji coba.
    """

    activity = resolve_activity(
        record
    )

    pilot = read_field(
        record,
        (
            "form.blok_vi."
            "apakah_melakukan_uji_coba"
        ),
    )

    pilot_value = (
        parse_boolean(
            pilot["raw_value"]
        )["value"]
    )

    evidence = {
        "activity_resolution": (
            activity
        ),

        "activity_explicit": (
            read_field(
                record,
                "form.metadata.jenis_kegiatan",
            )
        ),

        "activity_support": [
            read_field(
                record,
                path,
            )
            for path in activity[
                "evidence_paths"
            ]
        ],

        "pilot_test": pilot,
    }


    if activity["value"] is None:

        return build_rule_result(
            "R-VI-01",
            "not_evaluable",
            "unknown",
            "activity_type_unavailable",
            evidence,
        )


    if (
        activity["value"]
        == "kompromin"
    ):

        return build_rule_result(
            "R-VI-01",
            "pass",
            "not_applicable",
            "compilation_activity",
            evidence,
        )


    if pilot_value is None:

        return build_rule_result(
            "R-VI-01",
            "not_evaluable",
            "applicable",
            "pilot_test_unavailable_or_unrecognized",
            evidence,
        )


    if pilot_value is False:

        return build_rule_result(
            "R-VI-01",
            "violation",
            "applicable",
            "pilot_test_not_performed",
            evidence,
            (
                "Kegiatan nonkompilasi "
                "disarankan melakukan uji coba."
            ),
        )


    return build_rule_result(
        "R-VI-01",
        "pass",
        "applicable",
        "pilot_test_performed",
        evidence,
    )


# ============================================================
# R-VI-05
# ============================================================

def rule_r_vi_05(
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    Jumlah supervisor tidak boleh
    melebihi jumlah enumerator.
    """

    supervisor = read_field(
        record,
        "form.blok_vi.jumlah_supervisor",
    )

    enumerator = read_field(
        record,
        "form.blok_vi.jumlah_enumerator",
    )

    n_supervisor = parse_staff_count(
        supervisor["raw_value"]
    )

    n_enumerator = parse_staff_count(
        enumerator["raw_value"]
    )

    evidence = {
        "supervisor": supervisor,
        "enumerator": enumerator,
        "parsed_supervisor": (
            n_supervisor
        ),
        "parsed_enumerator": (
            n_enumerator
        ),
    }


    if (
        n_supervisor is None
        or n_enumerator is None
    ):

        return build_rule_result(
            "R-VI-05",
            "not_evaluable",
            "unknown",
            "staff_counts_unavailable_or_invalid",
            evidence,
        )


    if (
        n_supervisor
        > n_enumerator
    ):

        return build_rule_result(
            "R-VI-05",
            "violation",
            "applicable",
            "supervisors_exceed_enumerators",
            evidence,
            (
                "Jumlah supervisor melebihi "
                "jumlah enumerator."
            ),
        )


    return build_rule_result(
        "R-VI-05",
        "pass",
        "applicable",
        "staff_count_comparison_satisfied",
        evidence,
    )


# ============================================================
# R-VI-08
# ============================================================

def rule_r_vi_08(
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    Jika terdapat supervisor,
    metode pemeriksaan kualitas
    harus mencakup supervisi.
    """

    supervisor = read_field(
        record,
        "form.blok_vi.jumlah_supervisor",
    )

    supervision = read_field(
        record,
        (
            "form.blok_vi."
            "metode_pemeriksaan_kualitas."
            "supervisi"
        ),
    )

    n_supervisor = parse_staff_count(
        supervisor["raw_value"]
    )

    supervision_value = (
        parse_boolean(
            supervision["raw_value"]
        )["value"]
    )

    evidence = {
        "supervisor": supervisor,
        "parsed_supervisor": (
            n_supervisor
        ),
        "supervision": supervision,
    }


    if n_supervisor is None:

        return build_rule_result(
            "R-VI-08",
            "not_evaluable",
            "unknown",
            "supervisor_count_unavailable_or_invalid",
            evidence,
        )


    if n_supervisor == 0:

        return build_rule_result(
            "R-VI-08",
            "pass",
            "not_applicable",
            "no_supervisor",
            evidence,
        )


    if supervision_value is None:

        return build_rule_result(
            "R-VI-08",
            "not_evaluable",
            "applicable",
            "supervision_unavailable_or_unrecognized",
            evidence,
        )


    if supervision_value is False:

        return build_rule_result(
            "R-VI-08",
            "violation",
            "applicable",
            "supervision_not_selected",
            evidence,
            (
                "Jika terdapat supervisor, "
                "metode pemeriksaan kualitas "
                "harus mencakup supervisi."
            ),
        )


    return build_rule_result(
        "R-VI-08",
        "pass",
        "applicable",
        "supervision_selected",
        evidence,
    )


# ============================================================
# GROUP REGISTRY
# ============================================================

GROUP_01_RULES = {
    "R-IV-07": rule_r_iv_07,
    "R-VI-01": rule_r_vi_01,
    "R-VI-05": rule_r_vi_05,
    "R-VI-08": rule_r_vi_08,
}