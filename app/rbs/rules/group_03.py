# ============================================================
# ROMANTIK AI API
# RBS — Rule Group 03
# ============================================================

from __future__ import annotations

from typing import Any

from app.rbs.base import (
    build_rule_result,
)

from app.rbs.helpers import (
    detect_inferential_analysis,
    normalize_label,
    read_field,
    read_required_sampling,
    read_sampling_method,
    sampling_rule_context,
)


GROUP_03_VERSION = "rebuild_group_03_v04"


def group_03_result(
    rule_id: str,
    status: str,
    applicability: str,
    reason: str,
    evidence: dict[str, Any],
    message: str | None = None,
) -> dict[str, Any]:

    result = build_rule_result(
        rule_id,
        status,
        applicability,
        reason,
        evidence,
        message,
    )

    result["rule_version"] = (
        GROUP_03_VERSION
    )

    return result


def check_probability_requirement(
    record: dict[str, Any],
    rule_id: str,
    concept: str,
    message: str,
) -> dict[str, Any]:

    context = sampling_rule_context(
        record
    )

    required = read_required_sampling(
        record,
        concept,
    )

    evidence = {
        **context,
        "required_field": required,
    }

    activity = context[
        "activity"
    ]["value"]

    method = context[
        "sampling_method"
    ]["category"]


    if activity is None:

        return group_03_result(
            rule_id,
            "not_evaluable",
            "unknown",
            "activity_type_unavailable",
            evidence,
        )


    if activity != "survei":

        return group_03_result(
            rule_id,
            "pass",
            "not_applicable",
            "non_survey_activity",
            evidence,
        )


    if method is None:

        return group_03_result(
            rule_id,
            "not_evaluable",
            "unknown",
            "sampling_method_unavailable_or_unrecognized",
            evidence,
        )


    if method == "non_probability":

        return group_03_result(
            rule_id,
            "pass",
            "not_applicable",
            "non_probability_sampling",
            evidence,
        )


    if required["state"] in {
        "unavailable",
        "conflict",
    }:

        return group_03_result(
            rule_id,
            "not_evaluable",
            "applicable",
            "required_field_unavailable_or_conflicting",
            evidence,
        )


    if required["state"] == "empty":

        return group_03_result(
            rule_id,
            "violation",
            "applicable",
            "required_field_explicitly_empty",
            evidence,
            message,
        )


    return group_03_result(
        rule_id,
        "pass",
        "applicable",
        "required_field_present",
        evidence,
    )


# ============================================================
# R-V-03A
# ============================================================

SPECIFIC_SAMPLING_TECHNIQUES = {
    "simple random sampling":
        "simple_random_sampling",

    "systematic sampling":
        "systematic_sampling",
}


def rule_r_v_03a(
    record: dict[str, Any],
) -> dict[str, Any]:

    result = check_probability_requirement(
        record,
        rule_id="R-V-03A",
        concept="method_detail",
        message=(
            "Rincian teknik probability "
            "sampling perlu diisi."
        ),
    )

    if (
        result["status"]
        != "not_evaluable"
        or result["applicability"]
        != "applicable"
        or result["reason"]
        != "required_field_unavailable_or_conflicting"
    ):
        return result


    detail = read_required_sampling(
        record,
        "method_detail",
    )

    # Konflik dan explicit empty
    # tidak boleh ditutupi.
    if detail["state"] != "unavailable":
        return result


    sampling = read_sampling_method(
        record
    )

    reading = sampling[
        "reading"
    ]

    if (
        sampling["category"]
        != "probability"
        or reading["status"]
        != "selected"
        or not isinstance(
            reading["raw_value"],
            str,
        )
    ):
        return result


    label = (
        normalize_label(
            reading["raw_value"]
        )
        .strip(" -")
    )

    technique = (
        SPECIFIC_SAMPLING_TECHNIQUES
        .get(label)
    )

    if technique is None:
        return result


    evidence = {
        "initial_evidence":
            result["evidence"],

        "alternative_technique_evidence": {
            "source_path":
                reading["source_path"],

            "raw_value":
                reading["raw_value"],

            "normalized_technique":
                technique,

            "basis": (
                "specific_technique_"
                "in_sampling_method_field"
            ),
        },
    }

    return group_03_result(
        rule_id="R-V-03A",
        status="pass",
        applicability="applicable",
        reason=(
            "required_technique_present_"
            "in_sampling_method"
        ),
        evidence=evidence,
    )


# ============================================================
# R-V-03B
# ============================================================

def rule_r_v_03b(
    record: dict[str, Any],
) -> dict[str, Any]:

    return check_probability_requirement(
        record,
        "R-V-03B",
        "sampling_frame",
        (
            "Kerangka sampel wajib diisi "
            "untuk sampel probabilitas."
        ),
    )


# ============================================================
# R-V-03C
# ============================================================

def rule_r_v_03c(
    record: dict[str, Any],
) -> dict[str, Any]:

    return check_probability_requirement(
        record,
        "R-V-03C",
        "sampling_fraction",
        (
            "Fraksi sampel wajib diisi "
            "untuk sampel probabilitas."
        ),
    )


# ============================================================
# R-V-03D
# ============================================================

def rule_r_v_03d(
    record: dict[str, Any],
) -> dict[str, Any]:

    return check_probability_requirement(
        record,
        "R-V-03D",
        "sampling_error",
        (
            "Perkiraan sampling error wajib "
            "diisi untuk sampel probabilitas."
        ),
    )


# ============================================================
# R-VII-03
# ============================================================

def rule_r_vii_03(
    record: dict[str, Any],
) -> dict[str, Any]:

    context = sampling_rule_context(
        record
    )

    analysis = read_field(
        record,
        "form.blok_vii.metode_analisis",
    )

    inferential = (
        detect_inferential_analysis(
            analysis["raw_value"]
        )
    )

    evidence = {
        **context,
        "analysis": analysis,
        "inferential_selected":
            inferential,
    }

    activity = context[
        "activity"
    ]["value"]

    method = context[
        "sampling_method"
    ]["category"]


    if activity is None:

        return group_03_result(
            "R-VII-03",
            "not_evaluable",
            "unknown",
            "activity_type_unavailable",
            evidence,
        )


    if activity != "survei":

        return group_03_result(
            "R-VII-03",
            "pass",
            "not_applicable",
            "non_survey_activity",
            evidence,
        )


    if inferential is None:

        return group_03_result(
            "R-VII-03",
            "not_evaluable",
            "unknown",
            "analysis_unavailable_or_unrecognized",
            evidence,
        )


    if inferential is False:

        return group_03_result(
            "R-VII-03",
            "pass",
            "not_applicable",
            "inferential_analysis_not_selected",
            evidence,
        )


    if method is None:

        return group_03_result(
            "R-VII-03",
            "not_evaluable",
            "applicable",
            "sampling_method_unavailable_or_unrecognized",
            evidence,
        )


    if method == "non_probability":

        return group_03_result(
            "R-VII-03",
            "violation",
            "applicable",
            (
                "inferential_analysis_with_"
                "non_probability_sampling"
            ),
            evidence,
            (
                "Analisis inferensia pada survei "
                "harus menggunakan sampel "
                "probabilitas sesuai ketentuan "
                "R-VII-03."
            ),
        )


    return group_03_result(
        "R-VII-03",
        "pass",
        "applicable",
        (
            "inferential_analysis_with_"
            "probability_sampling"
        ),
        evidence,
    )


GROUP_03_RULES = {
    "R-V-03A": rule_r_v_03a,
    "R-V-03B": rule_r_v_03b,
    "R-V-03C": rule_r_v_03c,
    "R-V-03D": rule_r_v_03d,
    "R-VII-03": rule_r_vii_03,
}