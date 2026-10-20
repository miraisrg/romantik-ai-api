# ============================================================
# ROMANTIK AI API
# RBS — Rule Group 10
# ============================================================
#
# Rules:
# - R-V-01
# - R-V-02
# - R-V-08A
# - R-VII-04
# ============================================================

from __future__ import annotations

import re
from typing import Any

from app.rbs.base import build_rule_result
from app.rbs.helpers import (
    GROUP_03_PATHS,
    detect_inferential_analysis,
    normalize_label,
    read_alternatives,
    read_field,
    resolve_activity,
)


# ============================================================
# GROUP VERSION
# ============================================================

GROUP_10_VERSION = "rebuild_sampling_design_v01"


# ============================================================
# PATH CONFIG
# ============================================================

SAMPLING_DESIGN_PATHS = {
    "sampling_design": (
        "form.blok_v.jenis_rancangan_sampel",
    ),

    "sampling_method":
        GROUP_03_PATHS["sampling_method"],

    "sampling_frame":
        GROUP_03_PATHS["sampling_frame"],

    "sampling_fraction":
        GROUP_03_PATHS["sampling_fraction"],

    "sampling_unit": (
        "form.blok_v.unit_sampel",
    ),
}


# ============================================================
# HELPERS
# ============================================================

def read_design_concept(
    record: dict[str, Any],
    concept: str,
) -> dict[str, Any]:
    """
    Baca alternatif path tanpa menyembunyikan
    konflik maupun nilai kosong eksplisit.
    """

    reading = read_alternatives(
        record,
        SAMPLING_DESIGN_PATHS[
            concept
        ],
    )


    if (
        reading["status"]
        == "selected"
    ):

        state = "present"


    elif (
        reading["status"]
        == "conflict"
    ):

        state = "conflict"


    elif any(
        item["state"]
        in {
            "empty_string",
            "empty_list",
            "empty_object",
        }
        for item
        in reading["observations"]
    ):

        state = "empty"


    else:

        state = "unavailable"


    return {
        "state":
            state,

        "reading":
            reading,
    }


def block_has_content(
    value: Any,
) -> bool:
    """
    Deteksi isi nyata pada blok template.

    Key dengan nilai null saja tidak
    dianggap sebagai isi informatif.
    """

    if value is None:
        return False


    if isinstance(
        value,
        str,
    ):

        return bool(
            value.strip()
        )


    if isinstance(
        value,
        dict,
    ):

        return any(
            block_has_content(
                item
            )
            for item
            in value.values()
        )


    if isinstance(
        value,
        list,
    ):

        return any(
            block_has_content(
                item
            )
            for item
            in value
        )


    # False dan 0 adalah nilai eksplisit.
    return True


# ============================================================
# MAIN EVALUATOR
# ============================================================

def evaluate_sampling_design(
    record: dict[str, Any],
    rule_id: str,
) -> dict[str, Any]:
    """
    Evaluasi rule desain sampel
    dengan applicability eksplisit.
    """

    activity = resolve_activity(
        record
    )


    evidence = {
        "activity":
            activity,

        "activity_source": [
            read_field(
                record,
                path,
            )
            for path
            in activity.get(
                "evidence_paths",
                [],
            )
        ],
    }


    def finish(
        status: str,
        applicability: str,
        reason: str,
        message: str | None = None,
    ) -> dict[str, Any]:

        result = build_rule_result(
            rule_id=rule_id,
            status=status,
            applicability=applicability,
            reason=reason,
            evidence=evidence,
            message=message,
        )

        result[
            "rule_version"
        ] = GROUP_10_VERSION

        return result


    # ========================================================
    # ACTIVITY APPLICABILITY
    # ========================================================

    if (
        activity["value"]
        is None
    ):

        return finish(
            "not_evaluable",
            "unknown",
            "activity_type_unavailable",
        )


    if (
        activity["value"]
        != "survei"
    ):

        return finish(
            "pass",
            "not_applicable",
            "non_survey_activity",
        )


    # ========================================================
    # R-V-01
    # ========================================================

    if rule_id == "R-V-01":

        block = read_field(
            record,
            "form.blok_v",
        )

        evidence[
            "sampling_block"
        ] = block

        raw = block[
            "raw_value"
        ]


        if (
            block["state"]
            in {
                "empty_string",
                "empty_list",
                "empty_object",
            }
        ):

            return finish(
                "violation",
                "applicable",
                "sampling_block_explicitly_empty",
                (
                    "Blok desain sampel wajib "
                    "diisi untuk kegiatan survei."
                ),
            )


        if not isinstance(
            raw,
            dict,
        ):

            return finish(
                "not_evaluable",
                "applicable",
                (
                    "sampling_block_"
                    "unavailable_or_unrecognized"
                ),
            )


        if not block_has_content(
            raw
        ):

            return finish(
                "not_evaluable",
                "applicable",
                (
                    "sampling_block_has_"
                    "no_informative_content"
                ),
            )


        return finish(
            "pass",
            "applicable",
            "sampling_block_has_content",
        )


    # ========================================================
    # R-VII-04
    # ========================================================

    if (
        rule_id
        == "R-VII-04"
    ):

        analysis = read_field(
            record,
            "form.blok_vii.metode_analisis",
        )

        inferential = (
            detect_inferential_analysis(
                analysis["raw_value"]
            )
        )


        evidence[
            "analysis"
        ] = analysis

        evidence[
            "inferential_selected"
        ] = inferential


        if inferential is None:

            return finish(
                "not_evaluable",
                "unknown",
                (
                    "analysis_unavailable_"
                    "or_unrecognized"
                ),
            )


        if inferential is False:

            return finish(
                "pass",
                "not_applicable",
                (
                    "inferential_analysis_"
                    "not_selected"
                ),
            )


    # ========================================================
    # R-V-02 / R-VII-04
    # ========================================================

    if (
        rule_id
        in {
            "R-V-02",
            "R-VII-04",
        }
    ):

        concepts = {
            name:
                read_design_concept(
                    record,
                    name,
                )
            for name
            in SAMPLING_DESIGN_PATHS
        }


        empty = [
            name
            for name, item
            in concepts.items()
            if (
                item["state"]
                == "empty"
            )
        ]


        unknown = [
            name
            for name, item
            in concepts.items()
            if (
                item["state"]
                in {
                    "unavailable",
                    "conflict",
                }
            )
        ]


        evidence.update({
            "concepts":
                concepts,

            "explicitly_empty_concepts":
                empty,

            (
                "unavailable_or_"
                "conflicting_concepts"
            ):
                unknown,
        })


        if empty:

            return finish(
                "violation",
                "applicable",
                (
                    "sampling_fields_"
                    "explicitly_empty"
                ),
                (
                    "Isian desain sampel belum "
                    "lengkap. Lengkapi: "
                    + ", ".join(empty)
                    + "."
                ),
            )


        if unknown:

            return finish(
                "not_evaluable",
                "applicable",
                (
                    "sampling_fields_"
                    "unavailable_or_conflicting"
                ),
            )


        return finish(
            "pass",
            "applicable",
            (
                "required_sampling_"
                "fields_present"
            ),
        )


    # ========================================================
    # R-V-08A
    # ========================================================

    design = read_design_concept(
        record,
        "sampling_design",
    )

    fraction = read_design_concept(
        record,
        "sampling_fraction",
    )


    evidence.update({
        "design":
            design,

        "fraction":
            fraction,
    })


    raw_design = (
        design["reading"][
            "raw_value"
        ]
    )

    category = None


    if (
        design["state"]
        == "present"
        and isinstance(
            raw_design,
            str,
        )
    ):

        label = normalize_label(
            raw_design
        ).replace(
            "-",
            " ",
        )


        if re.search(
            r"\bmulti\s*(?:stage|phase)\b",
            label,
        ):

            category = (
                "multi_stage_or_phase"
            )


        elif re.search(
            r"\bsingle\s*(?:stage|phase)\b",
            label,
        ):

            category = (
                "single_stage_or_phase"
            )


    evidence[
        "normalized_design"
    ] = category


    if category is None:

        return finish(
            "not_evaluable",
            "unknown",
            (
                "sampling_design_"
                "unavailable_or_unrecognized"
            ),
        )


    if (
        category
        == "single_stage_or_phase"
    ):

        return finish(
            "pass",
            "not_applicable",
            (
                "design_not_multi_"
                "stage_or_phase"
            ),
        )


    if (
        fraction["state"]
        in {
            "unavailable",
            "conflict",
        }
    ):

        return finish(
            "not_evaluable",
            "applicable",
            (
                "sampling_fraction_"
                "unavailable_or_conflicting"
            ),
        )


    raw_fraction = (
        fraction["reading"][
            "raw_value"
        ]
    )


    if (
        fraction["state"]
        == "empty"
    ):

        text = ""


    elif (
        isinstance(
            raw_fraction,
            bool,
        )
        or not isinstance(
            raw_fraction,
            (str, int, float),
        )
    ):

        return finish(
            "not_evaluable",
            "applicable",
            (
                "sampling_fraction_"
                "format_unrecognized"
            ),
        )


    else:

        text = str(
            raw_fraction
        )


    multiplication_found = bool(
        re.search(
            r"[\*×xX]",
            text,
        )
    )


    evidence[
        "multiplication_marker_found"
    ] = multiplication_found


    if not multiplication_found:

        return finish(
            "violation",
            "applicable",
            (
                "stage_multiplication_"
                "not_indicated"
            ),
            (
                "Fraksi sampel terindikasi "
                "belum menunjukkan perkalian "
                "antartahap. Tinjau sesuai "
                "rancangan sampel."
            ),
        )


    return finish(
        "pass",
        "applicable",
        (
            "stage_multiplication_"
            "indicated"
        ),
    )


# ============================================================
# RULE FUNCTIONS
# ============================================================

def rule_r_v_01(
    record: dict[str, Any],
) -> dict[str, Any]:

    return evaluate_sampling_design(
        record,
        "R-V-01",
    )


def rule_r_v_02(
    record: dict[str, Any],
) -> dict[str, Any]:

    return evaluate_sampling_design(
        record,
        "R-V-02",
    )


def rule_r_v_08a(
    record: dict[str, Any],
) -> dict[str, Any]:

    return evaluate_sampling_design(
        record,
        "R-V-08A",
    )


def rule_r_vii_04(
    record: dict[str, Any],
) -> dict[str, Any]:

    return evaluate_sampling_design(
        record,
        "R-VII-04",
    )


# ============================================================
# GROUP REGISTRY
# ============================================================

GROUP_10_RULES = {
    "R-V-01": rule_r_v_01,
    "R-V-02": rule_r_v_02,
    "R-V-08A": rule_r_v_08a,
    "R-VII-04": rule_r_vii_04,
}