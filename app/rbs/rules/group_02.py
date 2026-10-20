# ============================================================
# ROMANTIK AI API
# RBS — Rule Group 02
# ============================================================
#
# Rules:
# - R-VI-02
# - R-VI-04A
# - R-VI-07
# ============================================================

from __future__ import annotations

from typing import Any

from app.rbs.base import (
    build_rule_result,
)

from app.rbs.helpers import (
    FACILITY_ALIASES,
    METHOD_ALIASES,
    parse_boolean,
    read_field,
    resolve_education_level,
    selected_option,
)


GROUP_02_VERSION = "rebuild_group_02_v02"


def group_02_result(
    rule_id: str,
    status: str,
    applicability: str,
    reason: str,
    evidence: dict[str, Any],
    message: str | None = None,
) -> dict[str, Any]:
    """
    Gunakan format hasil bersama
    dengan versi khusus Group 02.
    """

    result = build_rule_result(
        rule_id,
        status,
        applicability,
        reason,
        evidence,
        message,
    )

    result["rule_version"] = (
        GROUP_02_VERSION
    )

    return result


# ============================================================
# R-VI-02
# ============================================================

def rule_r_vi_02(
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    CAPI/CAWI memerlukan uji coba.
    """

    facilities = read_field(
        record,
        "form.blok_iv.sarana_pengumpulan_data",
    )

    pilot = read_field(
        record,
        "form.blok_vi.apakah_melakukan_uji_coba",
    )

    applicable = selected_option(
        facilities["raw_value"],
        {"capi", "cawi"},
        FACILITY_ALIASES,
    )

    pilot_value = (
        parse_boolean(
            pilot["raw_value"]
        )["value"]
    )

    evidence = {
        "facilities": facilities,
        "pilot_test": pilot,
        "uses_capi_or_cawi": applicable,
    }

    if applicable is None:

        return group_02_result(
            "R-VI-02",
            "not_evaluable",
            "unknown",
            "collection_facilities_unavailable_or_unrecognized",
            evidence,
        )

    if applicable is False:

        return group_02_result(
            "R-VI-02",
            "pass",
            "not_applicable",
            "capi_cawi_not_selected",
            evidence,
        )

    if pilot_value is None:

        return group_02_result(
            "R-VI-02",
            "not_evaluable",
            "applicable",
            "pilot_test_unavailable_or_unrecognized",
            evidence,
        )

    if pilot_value is False:

        return group_02_result(
            "R-VI-02",
            "violation",
            "applicable",
            "capi_cawi_without_pilot_test",
            evidence,
            (
                "CAPI/CAWI digunakan tanpa "
                "pelaksanaan uji coba sistem."
            ),
        )

    return group_02_result(
        "R-VI-02",
        "pass",
        "applicable",
        "pilot_test_performed",
        evidence,
    )


# ============================================================
# R-VI-04A
# ============================================================

def rule_r_vi_04a(
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    Peringatan pendidikan SMP
    pada metode wawancara.
    """

    methods = read_field(
        record,
        "form.blok_iv.metode_pengumpulan_data",
    )

    education = read_field(
        record,
        (
            "form.blok_vi."
            "persyaratan_pendidikan_terendah"
        ),
    )

    interview = selected_option(
        methods["raw_value"],
        {"wawancara"},
        METHOD_ALIASES,
    )

    level = resolve_education_level(
        education["raw_value"]
    )

    evidence = {
        "collection_methods": methods,
        "education": education,
        "education_level": level,
        "uses_interview": interview,
    }

    if interview is None:

        return group_02_result(
            "R-VI-04A",
            "not_evaluable",
            "unknown",
            "interview_selection_unavailable_or_unrecognized",
            evidence,
        )

    if interview is False:

        return group_02_result(
            "R-VI-04A",
            "pass",
            "not_applicable",
            "interview_not_selected",
            evidence,
        )

    if level is None:

        return group_02_result(
            "R-VI-04A",
            "not_evaluable",
            "applicable",
            "education_unavailable_or_ambiguous",
            evidence,
        )

    if level == "smp":

        return group_02_result(
            "R-VI-04A",
            "violation",
            "applicable",
            "smp_education_for_interview",
            evidence,
            (
                "Pendidikan petugas "
                "terindikasi rendah "
                "untuk metode wawancara."
            ),
        )

    if level == "sd":

        return group_02_result(
            "R-VI-04A",
            "not_evaluable",
            "applicable",
            "education_level_requires_rule_confirmation",
            evidence,
        )

    return group_02_result(
        "R-VI-04A",
        "pass",
        "applicable",
        "education_warning_not_triggered",
        evidence,
    )


# ============================================================
# R-VI-07
# ============================================================

def rule_r_vi_07(
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    Wawancara/pengamatan memerlukan
    pelatihan petugas.
    """

    methods = read_field(
        record,
        "form.blok_iv.metode_pengumpulan_data",
    )

    training = read_field(
        record,
        "form.blok_vi.apakah_melakukan_pelatihan",
    )

    applicable = selected_option(
        methods["raw_value"],
        {
            "wawancara",
            "pengamatan",
        },
        METHOD_ALIASES,
    )

    training_value = (
        parse_boolean(
            training["raw_value"]
        )["value"]
    )

    evidence = {
        "collection_methods": methods,
        "training": training,
        "uses_interview_or_observation": (
            applicable
        ),
    }

    if applicable is None:

        return group_02_result(
            "R-VI-07",
            "not_evaluable",
            "unknown",
            "collection_methods_unavailable_or_unrecognized",
            evidence,
        )

    if applicable is False:

        return group_02_result(
            "R-VI-07",
            "pass",
            "not_applicable",
            "interview_observation_not_selected",
            evidence,
        )

    if training_value is None:

        return group_02_result(
            "R-VI-07",
            "not_evaluable",
            "applicable",
            "training_unavailable_or_unrecognized",
            evidence,
        )

    if training_value is False:

        return group_02_result(
            "R-VI-07",
            "violation",
            "applicable",
            "training_not_performed",
            evidence,
            (
                "Pelatihan petugas wajib "
                "dilakukan untuk wawancara "
                "atau pengamatan."
            ),
        )

    return group_02_result(
        "R-VI-07",
        "pass",
        "applicable",
        "training_performed",
        evidence,
    )


# ============================================================
# GROUP REGISTRY
# ============================================================

GROUP_02_RULES = {
    "R-VI-02": rule_r_vi_02,
    "R-VI-04A": rule_r_vi_04a,
    "R-VI-07": rule_r_vi_07,
}