# ============================================================
# ROMANTIK AI API
# RBS — Rule Group 08
# ============================================================
#
# Rules:
# - R-III-08A
# - R-III-09
# - R-III-10
# - R-III-12
# ============================================================

from __future__ import annotations

import re
from typing import Any

from app.rbs.base import build_rule_result
from app.rbs.helpers import read_field


# ============================================================
# GROUP VERSION
# ============================================================

GROUP_08_VERSION = "rebuild_variable_group_v01"


# ============================================================
# VARIABLE CONFIG
# ============================================================

VARIABLE_LIST_PATH = (
    "form.blok_iii.variabel_yang_dikumpulkan"
)


VARIABLE_RULE_CONFIG = {
    "R-III-08A": {
        "field": "nama",
        "mode": "name_pattern",
        "message": (
            "Nama beberapa variabel terindikasi "
            "mengandung singkatan atau satuan. "
            "Tinjau penulisannya."
        ),
    },

    "R-III-09": {
        "field": "definisi",
        "mode": "required",
        "message": (
            "Definisi beberapa variabel masih kosong. "
            "Lengkapi definisi variabel tersebut."
        ),
    },

    "R-III-10": {
        "field": "definisi",
        "mode": "definition_format",
        "message": (
            "Format definisi beberapa variabel perlu "
            "diperbaiki: diawali 'adalah' dan "
            "tidak diakhiri tanda titik."
        ),
    },

    "R-III-12": {
        "field": "referensi_waktu",
        "mode": "required",
        "message": (
            "Referensi waktu beberapa variabel masih "
            "kosong. Lengkapi sesuai periode yang diukur."
        ),
    },
}


# ============================================================
# PATTERNS
# ============================================================

ACRONYM_PATTERN = re.compile(
    r"\b[A-Z]{2,}\b"
)

VARIABLE_UNIT_PATTERN = re.compile(
    r"\b(?:kg|gram|km|cm|mm|persen)\b|%",
    flags=re.IGNORECASE,
)


# ============================================================
# RESULT BUILDER
# ============================================================

def group_08_result(
    rule_id: str,
    status: str,
    reason: str,
    evidence: dict[str, Any],
    message: str | None = None,
) -> dict[str, Any]:
    """
    Bentuk hasil rule Group 08.
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
        GROUP_08_VERSION
    )

    return result


# ============================================================
# SHARED VARIABLE EVALUATOR
# ============================================================

def evaluate_variable_rule(
    record: dict[str, Any],
    rule_id: str,
) -> dict[str, Any]:
    """
    Periksa satu rule terhadap seluruh
    item variabel yang terstruktur.
    """

    config = VARIABLE_RULE_CONFIG[
        rule_id
    ]

    source = read_field(
        record,
        VARIABLE_LIST_PATH,
    )

    raw_variables = source[
        "raw_value"
    ]


    # ============================================================
    # API CANONICAL COMPATIBILITY
    # ============================================================
    #
    # Notebook RBS:
    #   variabel_yang_dikumpulkan = list[dict]
    #
    # Canonical API:
    #   variabel_yang_dikumpulkan = {
    #       "items": list[dict],
    #       "raw_text": str | None,
    #   }
    #
    # Rule tetap hanya mengevaluasi structured items.
    # raw_text dipertahankan untuk LLM fallback.
    # ============================================================

    if isinstance(
        raw_variables,
        dict,
    ):

        variables = raw_variables.get(
            "items"
        )

    else:

        variables = raw_variables


    # --------------------------------------------------------
    # Sumber harus list of dict
    # --------------------------------------------------------

    if (
        not isinstance(
            variables,
            list,
        )
        or not all(
            isinstance(item, dict)
            for item in variables
        )
    ):

        return group_08_result(
            rule_id,
            "not_evaluable",
            (
                "variables_unavailable_"
                "or_not_structured"
            ),
            {
                "source": source,
            },
        )


    if not variables:

        return group_08_result(
            rule_id,
            "not_evaluable",
            "variable_list_empty",
            {
                "source": source,
            },
        )


    observations = []
    violation_indices = []
    unevaluable_indices = []


    # --------------------------------------------------------
    # Evaluasi setiap variabel
    # --------------------------------------------------------

    for index, item in enumerate(
        variables
    ):

        reading = read_field(
            item,
            config["field"],
        )

        state = reading[
            "state"
        ]

        value = reading[
            "raw_value"
        ]


        observation = {
            "index": index,

            "nama":
                item.get("nama"),

            "source_path": (
                f"{VARIABLE_LIST_PATH}"
                f"[{index}]."
                f"{config['field']}"
            ),

            "reading":
                reading,

            "problems": [],
        }


        explicitly_empty = (
            state in {
                "empty_string",
                "empty_list",
                "empty_object",
            }
        )


        # ----------------------------------------------------
        # Required field kosong eksplisit
        # ----------------------------------------------------

        if (
            explicitly_empty
            and config["mode"]
            == "required"
        ):

            observation[
                "status"
            ] = "violation"

            observation[
                "problems"
            ] = [
                "required_field_explicitly_empty"
            ]


        # ----------------------------------------------------
        # Tidak tersedia / null / empty untuk format rule
        # ----------------------------------------------------

        elif state != "populated":

            observation[
                "status"
            ] = "not_evaluable"

            observation[
                "reason"
            ] = (
                "field_empty_or_unavailable"
            )


        # ----------------------------------------------------
        # Field harus berupa text
        # ----------------------------------------------------

        elif not isinstance(
            value,
            str,
        ):

            observation[
                "status"
            ] = "not_evaluable"

            observation[
                "reason"
            ] = (
                "field_text_format_unrecognized"
            )


        else:

            text = value.strip()

            problems = []


            # ------------------------------------------------
            # R-III-08A
            # ------------------------------------------------

            if (
                config["mode"]
                == "name_pattern"
            ):

                acronyms = sorted(
                    set(
                        ACRONYM_PATTERN.findall(
                            text
                        )
                    )
                )

                units = sorted(
                    set(
                        VARIABLE_UNIT_PATTERN.findall(
                            text
                        )
                    )
                )


                observation[
                    "acronym_candidates"
                ] = acronyms

                observation[
                    "unit_candidates"
                ] = units


                if acronyms:

                    problems.append(
                        "acronym_candidate"
                    )


                if units:

                    problems.append(
                        "unit_candidate"
                    )


            # ------------------------------------------------
            # R-III-10
            # ------------------------------------------------

            elif (
                config["mode"]
                == "definition_format"
            ):

                if text.lower().startswith(
                    "adalah"
                ):

                    problems.append(
                        "starts_with_adalah"
                    )


                if not text.endswith(
                    "."
                ):

                    problems.append(
                        "missing_final_period"
                    )


            observation[
                "problems"
            ] = problems

            observation[
                "status"
            ] = (
                "violation"
                if problems
                else "pass"
            )


        observations.append(
            observation
        )


        if (
            observation["status"]
            == "violation"
        ):

            violation_indices.append(
                index
            )


        elif (
            observation["status"]
            == "not_evaluable"
        ):

            unevaluable_indices.append(
                index
            )


    # --------------------------------------------------------
    # Evidence level formulir
    # --------------------------------------------------------

    evidence = {
        "source_path":
            VARIABLE_LIST_PATH,

        "n_variables":
            len(variables),

        "observations":
            observations,

        "violation_indices":
            violation_indices,

        "unevaluable_indices":
            unevaluable_indices,
    }


    # Pelanggaran yang teramati tetap violation,
    # walaupun item lain not_evaluable.
    if violation_indices:

        return group_08_result(
            rule_id,
            "violation",
            (
                "variable_rule_"
                "violation_detected"
            ),
            evidence,
            config["message"],
        )


    if unevaluable_indices:

        return group_08_result(
            rule_id,
            "not_evaluable",
            (
                "variable_fields_unavailable_"
                "or_unrecognized"
            ),
            evidence,
        )


    return group_08_result(
        rule_id,
        "pass",
        (
            "all_variable_items_"
            "satisfy_check"
        ),
        evidence,
    )


# ============================================================
# RULE FUNCTIONS
# ============================================================

def rule_r_iii_08a(
    record: dict[str, Any],
) -> dict[str, Any]:

    return evaluate_variable_rule(
        record,
        "R-III-08A",
    )


def rule_r_iii_09(
    record: dict[str, Any],
) -> dict[str, Any]:

    return evaluate_variable_rule(
        record,
        "R-III-09",
    )


def rule_r_iii_10(
    record: dict[str, Any],
) -> dict[str, Any]:

    return evaluate_variable_rule(
        record,
        "R-III-10",
    )


def rule_r_iii_12(
    record: dict[str, Any],
) -> dict[str, Any]:

    return evaluate_variable_rule(
        record,
        "R-III-12",
    )


# ============================================================
# GROUP REGISTRY
# ============================================================

GROUP_08_RULES = {
    "R-III-08A": rule_r_iii_08a,
    "R-III-09": rule_r_iii_09,
    "R-III-10": rule_r_iii_10,
    "R-III-12": rule_r_iii_12,
}