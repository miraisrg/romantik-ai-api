# ============================================================
# ROMANTIK AI API
# RBS — Rule Group 09
# ============================================================
#
# Rules:
# - R-IV-01
# - R-IV-05
# - R-IV-09
#
# Final notebook version:
# rebuild_collection_group_v02
# ============================================================

from __future__ import annotations

from typing import Any

from app.rbs.base import build_rule_result
from app.rbs.helpers import (
    METHOD_ALIASES,
    normalize_label,
    read_field,
    resolve_activity,
    selected_option,
)


# ============================================================
# GROUP VERSION
# ============================================================

GROUP_09_VERSION = "rebuild_collection_group_v02"


# ============================================================
# PATH CONFIG
# ============================================================

COLLECTION_PATHS = {
    "recurrence":
        "form.blok_iv.kegiatan_ini_dilakukan",

    "frequency":
        "form.blok_iv.frekuensi_penyelenggara",

    "collection_type":
        "form.blok_iv.tipe_pengumpulan_data",

    "methods":
        "form.blok_iv.metode_pengumpulan_data",
}


# ============================================================
# FINAL COLLECTION TYPE ALIASES
# ============================================================

COLLECTION_TYPE_ALIASES = {
    "cross sectional":
        "cross_sectional",

    "crosssectional":
        "cross_sectional",

    "cross section":
        "cross_sectional",

    "longitudinal":
        "longitudinal",

    "longitudinal panel":
        "longitudinal",

    "longitudinal cross sectional":
        "longitudinal",

    "series":
        "series",

    "cross sectional dan longitudinal":
        "combined",

    "longitudinal dan cross sectional":
        "combined",

    "series dan cross section":
        "combined",
}


# ============================================================
# LOCAL ALIAS FOR R-IV-09
# ============================================================

SECONDARY_METHOD_ALIASES = {
    **METHOD_ALIASES,

    "dokumentasi":
        "data_sekunder",
}


# ============================================================
# RESULT BUILDER
# ============================================================

def group_09_result(
    rule_id: str,
    status: str,
    applicability: str,
    reason: str,
    evidence: dict[str, Any],
    message: str | None = None,
) -> dict[str, Any]:
    """
    Bentuk hasil rule Group 09.
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
        GROUP_09_VERSION
    )

    return result


# ============================================================
# RECURRENCE READER
# ============================================================

def read_collection_recurrence(
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    Kenali kegiatan berulang atau sekali
    berdasarkan label eksplisit.
    """

    reading = read_field(
        record,
        COLLECTION_PATHS[
            "recurrence"
        ],
    )

    category = None


    if (
        reading["state"]
        == "populated"
        and isinstance(
            reading["raw_value"],
            str,
        )
    ):

        label = normalize_label(
            reading["raw_value"]
        )

        category = {
            "berulang":
                "repeated",

            "hanya sekali":
                "one_time",

            "sekali":
                "one_time",
        }.get(
            label
        )


    return {
        "category":
            category,

        "reading":
            reading,
    }


# ============================================================
# R-IV-01
# ============================================================

def rule_r_iv_01(
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    Frekuensi wajib tersedia
    untuk kegiatan berulang.
    """

    recurrence = (
        read_collection_recurrence(
            record
        )
    )

    frequency = read_field(
        record,
        COLLECTION_PATHS[
            "frequency"
        ],
    )


    evidence = {
        "recurrence":
            recurrence,

        "frequency":
            frequency,
    }


    if (
        recurrence["category"]
        is None
    ):

        return group_09_result(
            "R-IV-01",
            "not_evaluable",
            "unknown",
            (
                "activity_recurrence_"
                "unavailable_or_unrecognized"
            ),
            evidence,
        )


    if (
        recurrence["category"]
        != "repeated"
    ):

        return group_09_result(
            "R-IV-01",
            "pass",
            "not_applicable",
            "activity_not_repeated",
            evidence,
        )


    if (
        frequency["state"]
        in {
            "empty_string",
            "empty_list",
            "empty_object",
        }
    ):

        return group_09_result(
            "R-IV-01",
            "violation",
            "applicable",
            "frequency_explicitly_empty",
            evidence,
            (
                "Frekuensi penyelenggaraan wajib "
                "diisi untuk kegiatan yang "
                "dilakukan berulang."
            ),
        )


    if (
        frequency["state"]
        != "populated"
        or not isinstance(
            frequency["raw_value"],
            str,
        )
    ):

        return group_09_result(
            "R-IV-01",
            "not_evaluable",
            "applicable",
            (
                "frequency_unavailable_"
                "or_format_unrecognized"
            ),
            evidence,
        )


    return group_09_result(
        "R-IV-01",
        "pass",
        "applicable",
        "frequency_present",
        evidence,
    )


# ============================================================
# R-IV-05
# ============================================================

def rule_r_iv_05(
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    Kegiatan sekali harus menggunakan
    tipe cross-sectional.
    """

    recurrence = (
        read_collection_recurrence(
            record
        )
    )

    reading = read_field(
        record,
        COLLECTION_PATHS[
            "collection_type"
        ],
    )


    evidence = {
        "recurrence":
            recurrence,

        "collection_type":
            reading,
    }


    def finish(
        status: str,
        applicability: str,
        reason: str,
        message: str | None = None,
    ) -> dict[str, Any]:

        return group_09_result(
            "R-IV-05",
            status,
            applicability,
            reason,
            evidence,
            message,
        )


    if (
        recurrence["category"]
        is None
    ):

        return finish(
            "not_evaluable",
            "unknown",
            (
                "activity_recurrence_"
                "unavailable_or_unrecognized"
            ),
        )


    if (
        recurrence["category"]
        != "one_time"
    ):

        return finish(
            "pass",
            "not_applicable",
            "activity_not_one_time",
        )


    if (
        reading["state"]
        in {
            "empty_string",
            "empty_list",
            "empty_object",
        }
    ):

        return finish(
            "violation",
            "applicable",
            "collection_type_explicitly_empty",
            (
                "Tipe pengumpulan data masih kosong. "
                "Kegiatan sekali harus menggunakan "
                "tipe pengumpulan data cross-sectional."
            ),
        )


    category = None


    if (
        reading["state"]
        == "populated"
        and isinstance(
            reading["raw_value"],
            str,
        )
    ):

        label = normalize_label(
            reading["raw_value"]
        ).replace(
            "-",
            " ",
        )

        label = " ".join(
            label.split()
        )

        category = (
            COLLECTION_TYPE_ALIASES.get(
                label
            )
        )


    evidence[
        "normalized_collection_type"
    ] = category


    if category is None:

        return finish(
            "not_evaluable",
            "applicable",
            (
                "collection_type_"
                "unavailable_or_unrecognized"
            ),
        )


    if (
        category
        != "cross_sectional"
    ):

        return finish(
            "violation",
            "applicable",
            (
                "one_time_activity_"
                "not_cross_sectional"
            ),
            (
                "Kegiatan yang hanya dilakukan "
                "sekali harus menggunakan tipe "
                "pengumpulan data cross-sectional."
            ),
        )


    return finish(
        "pass",
        "applicable",
        (
            "one_time_activity_"
            "cross_sectional"
        ),
    )


# ============================================================
# R-IV-09
# ============================================================

def rule_r_iv_09(
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    Kegiatan kompilasi harus menggunakan
    pengumpulan data sekunder.

    Dokumentasi dikenali sebagai
    data sekunder pada versi final.
    """

    activity = (
        resolve_activity(
            record
        )
    )

    methods = read_field(
        record,
        COLLECTION_PATHS[
            "methods"
        ],
    )


    evidence = {
        "activity":
            activity,

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

        "methods":
            methods,

        "other_method_detail":
            read_field(
                record,
                (
                    "form.blok_iv."
                    "metode_pengumpulan_data_lainnya"
                ),
            ),

        "normalization_basis": {
            "dokumentasi":
                "data_sekunder",

            "basis":
                "user_confirmed_equivalence",
        },
    }


    def finish(
        status: str,
        applicability: str,
        reason: str,
        message: str | None = None,
    ) -> dict[str, Any]:

        return group_09_result(
            "R-IV-09",
            status,
            applicability,
            reason,
            evidence,
            message,
        )


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
        != "kompromin"
    ):

        return finish(
            "pass",
            "not_applicable",
            "non_compilation_activity",
        )


    secondary_selected = None


    if (
        methods["state"]
        == "populated"
    ):

        secondary_selected = (
            selected_option(
                methods[
                    "raw_value"
                ],
                targets={
                    "data_sekunder"
                },
                aliases=(
                    SECONDARY_METHOD_ALIASES
                ),
            )
        )


    evidence[
        "secondary_data_selected"
    ] = secondary_selected


    if (
        secondary_selected
        is None
    ):

        return finish(
            "not_evaluable",
            "applicable",
            (
                "secondary_data_selection_"
                "unavailable_or_unrecognized"
            ),
        )


    if (
        secondary_selected
        is False
    ):

        return finish(
            "violation",
            "applicable",
            (
                "compilation_without_"
                "secondary_data_selection"
            ),
            (
                "Kegiatan kompilasi produk "
                "administrasi harus menggunakan "
                "pengumpulan data sekunder."
            ),
        )


    return finish(
        "pass",
        "applicable",
        (
            "compilation_with_"
            "secondary_data_selection"
        ),
    )


# ============================================================
# GROUP REGISTRY
# ============================================================

GROUP_09_RULES = {
    "R-IV-01": rule_r_iv_01,
    "R-IV-05": rule_r_iv_05,
    "R-IV-09": rule_r_iv_09,
}