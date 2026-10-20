# ============================================================
# ROMANTIK AI API
# RBS — Rule Engine
# ============================================================
#
# Tahap sementara:
# menjalankan Rule Group 01 pada satu canonical record.
#
# Nanti registry seluruh kelompok rule akan digabung
# setelah semua 40 rule selesai dipindahkan.
# ============================================================

from __future__ import annotations

from typing import Any

from app.rbs.rules.group_01 import GROUP_01_RULES
from app.rbs.rules.group_02 import GROUP_02_RULES
from app.rbs.rules.group_03 import GROUP_03_RULES
from app.rbs.rules.group_04 import GROUP_04_RULES
from app.rbs.rules.group_05 import GROUP_05_RULES
from app.rbs.rules.group_06 import GROUP_06_RULES
from app.rbs.rules.group_07 import GROUP_07_RULES
from app.rbs.rules.group_08 import GROUP_08_RULES
from app.rbs.rules.group_09 import GROUP_09_RULES
from app.rbs.rules.group_10 import GROUP_10_RULES
from app.rbs.rules.group_11 import GROUP_11_RULES

# ============================================================
# FINAL ENGINE REGISTRY AUDIT
# ============================================================

FINAL_ENGINE_VERSION = "rebuild_integrated_v01"


EXPECTED_RULE_IDS = (
    "R-I-01",
    "R-I-02A",
    "R-I-04",

    "R-II-01",
    "R-II-02",

    "R-III-04",
    "R-III-05A",
    "R-III-06",
    "R-III-08A",
    "R-III-09",
    "R-III-10",
    "R-III-12",

    "R-IV-01",
    "R-IV-05",
    "R-IV-07",
    "R-IV-09",

    "R-V-01",
    "R-V-02",
    "R-V-03A",
    "R-V-03B",
    "R-V-03C",
    "R-V-03D",
    "R-V-08A",
    "R-V-11",
    "R-V-12",
    "R-V-14A",

    "R-VI-01",
    "R-VI-02",
    "R-VI-04A",
    "R-VI-05",
    "R-VI-07",
    "R-VI-08",

    "R-VII-01",
    "R-VII-03",
    "R-VII-04",

    "R-VIII-01",

    "R-ID-02A",
    "R-ID-03",
    "R-ID-04A",
    "R-ID-05A",
)

EXPECTED_RULE_VERSIONS = {
    # --------------------------------------------------------
    # Identity
    # --------------------------------------------------------
    "R-I-01":
        "rebuild_identity_group_v01",

    "R-I-02A":
        "rebuild_identity_group_v01",

    "R-I-04":
        "rebuild_identity_group_v01",

    "R-II-01":
        "rebuild_identity_group_v01",

    "R-II-02":
        "rebuild_identity_group_v01",


    # --------------------------------------------------------
    # Schedule
    # --------------------------------------------------------
    "R-III-04":
        "rebuild_schedule_group_v01",

    "R-III-05A":
        "rebuild_schedule_group_v01",

    "R-III-06":
        "rebuild_schedule_group_v01",


    # --------------------------------------------------------
    # Variable
    # --------------------------------------------------------
    "R-III-08A":
        "rebuild_variable_group_v01",

    "R-III-09":
        "rebuild_variable_group_v01",

    "R-III-10":
        "rebuild_variable_group_v01",

    "R-III-12":
        "rebuild_variable_group_v01",


    # --------------------------------------------------------
    # Collection
    # --------------------------------------------------------
    "R-IV-01":
        "rebuild_collection_group_v02",

    "R-IV-05":
        "rebuild_collection_group_v02",

    "R-IV-07":
        "rebuild_group_01_v03",

    "R-IV-09":
        "rebuild_collection_group_v02",


    # --------------------------------------------------------
    # Sampling design
    # --------------------------------------------------------
    "R-V-01":
        "rebuild_sampling_design_v01",

    "R-V-02":
        "rebuild_sampling_design_v01",

    "R-V-08A":
        "rebuild_sampling_design_v01",


    # --------------------------------------------------------
    # Sampling method / inferential group
    # --------------------------------------------------------
    "R-V-03A":
        "rebuild_group_03_v04",

    "R-V-03B":
        "rebuild_group_03_v04",

    "R-V-03C":
        "rebuild_group_03_v04",

    "R-V-03D":
        "rebuild_group_03_v04",


    # --------------------------------------------------------
    # Sampling-specific standalone rules
    # --------------------------------------------------------
    "R-V-11":
        "rebuild_r_v_11_v01",

    "R-V-12":
        "rebuild_r_v_12_v01",

    "R-V-14A":
        "rebuild_r_v_14a_v01",


    # --------------------------------------------------------
    # Data collection / processing
    # --------------------------------------------------------
    "R-VI-01":
        "rebuild_group_01_v03",

    "R-VI-02":
        "rebuild_group_02_v02",

    "R-VI-04A":
        "rebuild_group_02_v02",

    "R-VI-05":
        "rebuild_group_01_v03",

    "R-VI-07":
        "rebuild_group_02_v02",

    "R-VI-08":
        "rebuild_group_01_v03",


    # --------------------------------------------------------
    # Analysis
    # --------------------------------------------------------
    "R-VII-01":
        "rebuild_r_vii_01_v01",

    "R-VII-03":
        "rebuild_group_03_v04",

    "R-VII-04":
        "rebuild_sampling_design_v01",


    # --------------------------------------------------------
    # Dissemination
    # --------------------------------------------------------
    "R-VIII-01":
        "rebuild_r_viii_01_v01",


    # --------------------------------------------------------
    # Title & year
    # --------------------------------------------------------
    "R-ID-02A":
        "rebuild_title_year_v01",

    "R-ID-03":
        "rebuild_title_year_v01",

    "R-ID-04A":
        "rebuild_title_year_v01",

    "R-ID-05A":
        "rebuild_title_year_v01",
}

def audit_rule_registry() -> dict[str, Any]:
    """
    Audit bahwa engine API memiliki tepat
    40 rule final tanpa rule hilang atau duplikat.
    """

    registries = (
        GROUP_01_RULES,
        GROUP_02_RULES,
        GROUP_03_RULES,
        GROUP_04_RULES,
        GROUP_05_RULES,
        GROUP_06_RULES,
        GROUP_07_RULES,
        GROUP_08_RULES,
        GROUP_09_RULES,
        GROUP_10_RULES,
        GROUP_11_RULES,
    )

    actual_rule_ids = [
        rule_id
        for registry in registries
        for rule_id in registry
    ]

    duplicate_rule_ids = sorted({
        rule_id
        for rule_id in actual_rule_ids
        if actual_rule_ids.count(rule_id) > 1
    })

    expected_set = set(
        EXPECTED_RULE_IDS
    )

    actual_set = set(
        actual_rule_ids
    )

    missing_rule_ids = sorted(
        expected_set
        - actual_set
    )

    unexpected_rule_ids = sorted(
        actual_set
        - expected_set
    )

    return {
        "engine_version":
            FINAL_ENGINE_VERSION,

        "n_expected":
            len(EXPECTED_RULE_IDS),

        "n_actual":
            len(actual_rule_ids),

        "n_unique":
            len(actual_set),

        "missing_rule_ids":
            missing_rule_ids,

        "unexpected_rule_ids":
            unexpected_rule_ids,

        "duplicate_rule_ids":
            duplicate_rule_ids,

        "is_valid": (
            len(EXPECTED_RULE_IDS) == 40
            and len(actual_rule_ids) == 40
            and len(actual_set) == 40
            and not missing_rule_ids
            and not unexpected_rule_ids
            and not duplicate_rule_ids
        ),
    }

def run_rule_group(
    record: dict[str, Any],
    rules: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Jalankan sekumpulan rule terhadap satu canonical record.

    Parameters
    ----------
    record
        Satu formulir canonical ROMANTIK.

    rules
        Mapping:
        rule_id -> rule_function

    Returns
    -------
    list[dict]
        Hasil setiap rule.
    """

    results = []

    for rule_id, rule_function in rules.items():

        try:
            result = rule_function(
                record
            )

        except Exception as exc:
            raise RuntimeError(
                "Rule execution failed: "
                f"{rule_id}"
            ) from exc

        if (
            result.get("rule_id")
            != rule_id
        ):
            raise ValueError(
                "Rule ID mismatch: "
                f"expected={rule_id}, "
                f"actual={result.get('rule_id')}"
            )

        results.append(
            result
        )

    return results


def run_group_01(
    record: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Jalankan empat rule pada Group 01.
    """

    return run_rule_group(
        record,
        GROUP_01_RULES,
    )

def run_group_02(
    record: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Jalankan tiga rule pada Group 02.
    """

    return run_rule_group(
        record,
        GROUP_02_RULES,
    )


def run_current_rbs(
    record: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Jalankan seluruh rule yang sudah
    dipindahkan ke API sejauh ini.

    Saat ini:
    - Group 01 = 4 rules
    - Group 02 = 3 rules
    - Group 03 = 5 rules
    - Group 04 = 3 rules
    - Group 05 = 2 rules
    - Group 06 = 5 rules
    - Group 07 = 3 rules
    - Group 08 = 4 rules
    - Group 09 = 3 rules
    - Group 10 = 4 rules
    - Group 11 = 4 rules

    Total = 40 rules
    """

    results = []

    results.extend(
        run_group_01(
            record
        )
    )

    results.extend(
        run_group_02(
            record
        )
    )

    results.extend(
        run_group_03(
            record
        )
    )

    results.extend(
        run_group_04(
            record
        )
    )

    results.extend(
        run_group_05(
            record
        )
    )

    results.extend(
        run_group_06(
            record
        )
    )

    results.extend(
        run_group_07(
            record
        )
    )

    results.extend(
        run_group_08(
            record
        )
    )   

    results.extend(
        run_group_09(
            record
        )
    )

    results.extend(
        run_group_10(
            record
        )
    )

    results.extend(
        run_group_11(
            record
        )
    )

    return results

def run_group_03(
    record: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Jalankan lima rule pada Group 03.
    """

    return run_rule_group(
        record,
        GROUP_03_RULES,
    )

def run_group_04(
    record: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Jalankan tiga rule pada Group 04.
    """

    return run_rule_group(
        record,
        GROUP_04_RULES,
    )

def run_group_05(
    record: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Jalankan dua rule pada Group 05.
    """

    return run_rule_group(
        record,
        GROUP_05_RULES,
    )

def run_group_06(
    record: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Jalankan lima rule pada Group 06.
    """

    return run_rule_group(
        record,
        GROUP_06_RULES,
    )

def run_group_07(
    record: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Jalankan tiga rule pada Group 07.
    """

    return run_rule_group(
        record,
        GROUP_07_RULES,
    )

def run_group_08(
    record: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Jalankan empat rule pada Group 08.
    """

    return run_rule_group(
        record,
        GROUP_08_RULES,
    )

def run_group_09(
    record: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Jalankan tiga rule pada Group 09.
    """

    return run_rule_group(
        record,
        GROUP_09_RULES,
    )

def run_group_10(
    record: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Jalankan empat rule pada Group 10.
    """

    return run_rule_group(
        record,
        GROUP_10_RULES,
    )

def run_group_11(
    record: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Jalankan empat rule pada Group 11.
    """

    return run_rule_group(
        record,
        GROUP_11_RULES,
    )

def audit_rule_versions(
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    Pastikan seluruh 40 rule menghasilkan
    rule_version yang sama dengan versi
    final notebook.
    """

    results = run_current_rbs(
        record
    )

    actual_versions = {
        result["rule_id"]:
            result["rule_version"]
        for result in results
    }


    mismatches = {}

    for (
        rule_id,
        expected_version,
    ) in EXPECTED_RULE_VERSIONS.items():

        actual_version = (
            actual_versions.get(
                rule_id
            )
        )

        if (
            actual_version
            != expected_version
        ):

            mismatches[
                rule_id
            ] = {
                "expected":
                    expected_version,

                "actual":
                    actual_version,
            }


    return {
        "n_expected":
            len(
                EXPECTED_RULE_VERSIONS
            ),

        "n_checked":
            len(
                actual_versions
            ),

        "mismatches":
            mismatches,

        "is_valid": (
            len(
                EXPECTED_RULE_VERSIONS
            ) == 40
            and len(
                actual_versions
            ) == 40
            and not mismatches
        ),
    }

def audit_result_contract(
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    Audit kontrak output seluruh 40 rule.

    Memeriksa:
    - status valid,
    - applicability valid,
    - relasi status-applicability,
    - konsistensi flag violation.
    """

    results = run_current_rbs(
        record
    )

    valid_statuses = {
        "pass",
        "violation",
        "not_evaluable",
    }

    valid_applicabilities = {
        "applicable",
        "not_applicable",
        "unknown",
    }

    errors = []


    for result in results:

        rule_id = result[
            "rule_id"
        ]

        status = result[
            "status"
        ]

        applicability = result[
            "applicability"
        ]

        violation = result[
            "violation"
        ]


        if (
            status
            not in valid_statuses
        ):

            errors.append({
                "rule_id":
                    rule_id,

                "error":
                    "invalid_status",

                "value":
                    status,
            })


        if (
            applicability
            not in valid_applicabilities
        ):

            errors.append({
                "rule_id":
                    rule_id,

                "error":
                    "invalid_applicability",

                "value":
                    applicability,
            })


        if (
            applicability
            == "not_applicable"
            and status
            != "pass"
        ):

            errors.append({
                "rule_id":
                    rule_id,

                "error":
                    (
                        "not_applicable_"
                        "must_be_pass"
                    ),
            })


        if (
            applicability
            == "unknown"
            and status
            != "not_evaluable"
        ):

            errors.append({
                "rule_id":
                    rule_id,

                "error":
                    (
                        "unknown_must_be_"
                        "not_evaluable"
                    ),
            })


        if (
            violation
            is not (
                status
                == "violation"
            )
        ):

            errors.append({
                "rule_id":
                    rule_id,

                "error":
                    (
                        "violation_flag_"
                        "inconsistent"
                    ),

                "status":
                    status,

                "violation":
                    violation,
            })


    return {
        "n_results":
            len(results),

        "n_errors":
            len(errors),

        "errors":
            errors,

        "is_valid": (
            len(results) == 40
            and not errors
        ),
    }

REQUIRED_RESULT_FIELDS = {
    "rule_id",
    "rule_version",
    "status",
    "violation",
    "applicability",
    "block",
    "field",
    "severity",
    "message",
    "reason",
    "evidence",
}


def audit_result_schema(
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    Audit kelengkapan struktur output
    seluruh 40 rule RBS.
    """

    results = run_current_rbs(
        record
    )

    errors = []


    for result in results:

        rule_id = result.get(
            "rule_id"
        )

        result_fields = set(
            result
        )

        missing_fields = sorted(
            REQUIRED_RESULT_FIELDS
            - result_fields
        )


        if missing_fields:

            errors.append({
                "rule_id":
                    rule_id,

                "error":
                    "missing_result_fields",

                "fields":
                    missing_fields,
            })


        # --------------------------------------------
        # Tipe field utama
        # --------------------------------------------

        if not isinstance(
            result.get("rule_id"),
            str,
        ):

            errors.append({
                "rule_id":
                    rule_id,

                "error":
                    "rule_id_not_string",
            })


        if not isinstance(
            result.get("rule_version"),
            str,
        ):

            errors.append({
                "rule_id":
                    rule_id,

                "error":
                    "rule_version_not_string",
            })


        if not isinstance(
            result.get("violation"),
            bool,
        ):

            errors.append({
                "rule_id":
                    rule_id,

                "error":
                    "violation_not_boolean",
            })


        if not isinstance(
            result.get("evidence"),
            dict,
        ):

            errors.append({
                "rule_id":
                    rule_id,

                "error":
                    "evidence_not_dictionary",
            })


    return {
        "n_results":
            len(results),

        "n_required_fields":
            len(
                REQUIRED_RESULT_FIELDS
            ),

        "n_errors":
            len(errors),

        "errors":
            errors,

        "is_valid": (
            len(results) == 40
            and not errors
        ),
    }