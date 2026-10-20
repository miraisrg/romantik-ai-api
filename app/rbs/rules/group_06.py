# ============================================================
# ROMANTIK AI API
# RBS — Rule Group 06
# ============================================================
#
# Rules:
# - R-I-01
# - R-I-02A
# - R-I-04
# - R-II-01
# - R-II-02
# ============================================================

from __future__ import annotations

import re
from typing import Any

from app.rbs.base import build_rule_result
from app.rbs.helpers import read_field


# ============================================================
# GROUP VERSION
# ============================================================

GROUP_06_VERSION = "rebuild_identity_group_v01"


# ============================================================
# RULE CONFIG
# ============================================================

IDENTITY_RULE_CONFIG = {
    "R-I-01": {
        "paths": {
            "instansi_penyelenggara":
                "form.blok_i.instansi_penyelenggara",
        },
    },

    "R-I-02A": {
        "paths": {
            "instansi_penyelenggara":
                "form.blok_i.instansi_penyelenggara",
        },
    },

    "R-I-04": {
        "paths": {
            "alamat":
                (
                    "form.blok_i."
                    "alamat_instansi_penyelenggara.alamat"
                ),
        },
    },

    "R-II-01": {
        "paths": {
            "eselon1":
                (
                    "form.blok_ii."
                    "unit_penanggung_jawab.eselon1"
                ),

            "eselon2":
                (
                    "form.blok_ii."
                    "unit_penanggung_jawab.eselon2"
                ),
        },
    },

    "R-II-02": {
        "paths": {
            name: (
                "form.blok_ii."
                f"penanggung_jawab_teknis.{name}"
            )
            for name in (
                "nama",
                "jabatan",
                "alamat",
                "telepon",
                "email",
            )
        },
    },
}


# ============================================================
# RESULT BUILDER
# ============================================================

def group_06_result(
    rule_id: str,
    status: str,
    reason: str,
    evidence: dict[str, Any],
    message: str | None = None,
) -> dict[str, Any]:
    """
    Bentuk hasil rule Group 06.
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
        GROUP_06_VERSION
    )

    return result


# ============================================================
# SHARED HELPER
# ============================================================

def check_identity_completeness(
    record: dict[str, Any],
    rule_id: str,
) -> dict[str, Any]:
    """
    Periksa keberadaan field wajib.

    Policy:
    - explicit empty -> violation
    - unavailable / absent -> not_evaluable
    - populated -> pass
    """

    readings = {
        name: read_field(
            record,
            path,
        )
        for name, path
        in IDENTITY_RULE_CONFIG[
            rule_id
        ]["paths"].items()
    }


    empty_states = {
        "empty_string",
        "empty_list",
        "empty_object",
    }


    empty_fields = [
        name
        for name, reading
        in readings.items()
        if reading["state"]
        in empty_states
    ]


    unavailable_fields = [
        name
        for name, reading
        in readings.items()
        if reading["state"]
        not in (
            empty_states
            | {"populated"}
        )
    ]


    evidence = {
        "fields": readings,
        "explicitly_empty_fields":
            empty_fields,
        "unavailable_fields":
            unavailable_fields,
    }


    if empty_fields:

        return group_06_result(
            rule_id,
            "violation",
            "required_fields_explicitly_empty",
            evidence,
            (
                "Isian wajib berikut masih kosong: "
                + ", ".join(empty_fields)
                + ". Lengkapi sesuai informasi kegiatan."
            ),
        )


    if unavailable_fields:

        return group_06_result(
            rule_id,
            "not_evaluable",
            "required_fields_unavailable",
            evidence,
        )


    return group_06_result(
        rule_id,
        "pass",
        "required_fields_present",
        evidence,
    )


# ============================================================
# R-I-01
# ============================================================

def rule_r_i_01(
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    Nama instansi penyelenggara wajib terisi.
    """

    return check_identity_completeness(
        record,
        "R-I-01",
    )


# ============================================================
# R-I-02A
# ============================================================

def rule_r_i_02a(
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    Deteksi kandidat singkatan / akronim
    berdasarkan token kapital.
    """

    path = (
        IDENTITY_RULE_CONFIG[
            "R-I-02A"
        ]["paths"][
            "instansi_penyelenggara"
        ]
    )

    reading = read_field(
        record,
        path,
    )

    evidence = {
        "instansi_penyelenggara":
            reading,
    }


    if (
        reading["state"]
        != "populated"
    ):

        return group_06_result(
            "R-I-02A",
            "not_evaluable",
            "institution_name_unavailable",
            evidence,
        )


    value = reading[
        "raw_value"
    ]


    if not isinstance(
        value,
        str,
    ):

        return group_06_result(
            "R-I-02A",
            "not_evaluable",
            "institution_name_format_unrecognized",
            evidence,
        )


    candidates = sorted(
        set(
            re.findall(
                r"\b[A-Z]{2,}\b",
                value,
            )
        )
    )

    evidence[
        "acronym_candidates"
    ] = candidates


    if candidates:

        return group_06_result(
            "R-I-02A",
            "violation",
            (
                "institution_acronym_"
                "candidate_detected"
            ),
            evidence,
            (
                "Nama instansi terindikasi "
                "mengandung singkatan atau akronim. "
                "Tinjau penulisannya dan gunakan "
                "nama lengkap jika diperlukan."
            ),
        )


    return group_06_result(
        "R-I-02A",
        "pass",
        (
            "institution_acronym_"
            "candidate_not_detected"
        ),
        evidence,
    )


# ============================================================
# R-I-04
# ============================================================

def rule_r_i_04(
    record: dict[str, Any],
) -> dict[str, Any]:

    return check_identity_completeness(
        record,
        "R-I-04",
    )


# ============================================================
# R-II-01
# ============================================================

def rule_r_ii_01(
    record: dict[str, Any],
) -> dict[str, Any]:

    return check_identity_completeness(
        record,
        "R-II-01",
    )


# ============================================================
# R-II-02
# ============================================================

def rule_r_ii_02(
    record: dict[str, Any],
) -> dict[str, Any]:

    return check_identity_completeness(
        record,
        "R-II-02",
    )


# ============================================================
# GROUP REGISTRY
# ============================================================

GROUP_06_RULES = {
    "R-I-01": rule_r_i_01,
    "R-I-02A": rule_r_i_02a,
    "R-I-04": rule_r_i_04,
    "R-II-01": rule_r_ii_01,
    "R-II-02": rule_r_ii_02,
}