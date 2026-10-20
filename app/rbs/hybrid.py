# ============================================================
# ROMANTIK AI API
# HYBRID RBS INTERFACE
# ============================================================

from __future__ import annotations

from typing import Any

from app.rbs.helpers import read_sampling_method

from collections import Counter

HYBRID_POLICY_VERSION = (
    "rebuild_hybrid_policy_v01_draft"
)

HYBRID_CLASSIFIER_VERSION = (
    "rebuild_hybrid_classifier_v01"
)


# ============================================================
# POLICY
# ============================================================

HYBRID_POLICY = {
    "R-I-01": {
        "policy_mode": "confirmed_finding",
        "issue_domain": "administrative_completeness",
    },
    "R-I-02A": {
        "policy_mode": "candidate_finding",
        "issue_domain": "editorial",
    },
    "R-I-04": {
        "policy_mode": "confirmed_finding",
        "issue_domain": "administrative_completeness",
    },
    "R-II-01": {
        "policy_mode": "confirmed_finding",
        "issue_domain": "administrative_completeness",
    },
    "R-II-02": {
        "policy_mode": "confirmed_finding",
        "issue_domain": "administrative_completeness",
    },

    "R-III-04": {
        "policy_mode": "candidate_finding",
        "issue_domain": "administrative_timing",
    },
    "R-III-05A": {
        "policy_mode": "candidate_finding",
        "issue_domain": "methodological",
    },
    "R-III-06": {
        "policy_mode": "confirmed_finding",
        "issue_domain": "methodological",
    },
    "R-III-08A": {
        "policy_mode": "candidate_finding",
        "issue_domain": "editorial",
    },
    "R-III-09": {
        "policy_mode": "confirmed_finding",
        "issue_domain": "methodological",
    },
    "R-III-10": {
        "policy_mode": "confirmed_finding",
        "issue_domain": "editorial",
    },
    "R-III-12": {
        "policy_mode": "confirmed_finding",
        "issue_domain": "methodological",
    },

    "R-IV-01": {
        "policy_mode": "confirmed_finding",
        "issue_domain": "methodological",
    },
    "R-IV-05": {
        "policy_mode": "confirmed_finding",
        "issue_domain": "methodological",
    },
    "R-IV-07": {
        "policy_mode": "confirmed_finding",
        "issue_domain": "methodological",
    },
    "R-IV-09": {
        "policy_mode": "confirmed_finding",
        "issue_domain": "methodological",
    },

    "R-V-01": {
        "policy_mode": "confirmed_finding",
        "issue_domain": "methodological",
    },
    "R-V-02": {
        "policy_mode": "conditional",
        "issue_domain": "methodological",
    },
    "R-V-03A": {
        "policy_mode": "confirmed_finding",
        "issue_domain": "methodological",
    },
    "R-V-03B": {
        "policy_mode": "confirmed_finding",
        "issue_domain": "methodological",
    },
    "R-V-03C": {
        "policy_mode": "confirmed_finding",
        "issue_domain": "methodological",
    },
    "R-V-03D": {
        "policy_mode": "confirmed_finding",
        "issue_domain": "methodological",
    },
    "R-V-08A": {
        "policy_mode": "candidate_finding",
        "issue_domain": "methodological",
    },
    "R-V-11": {
        "policy_mode": "candidate_finding",
        "issue_domain": "methodological",
    },
    "R-V-12": {
        "policy_mode": "candidate_finding",
        "issue_domain": "methodological",
    },
    "R-V-14A": {
        "policy_mode": "confirmed_finding",
        "issue_domain": "methodological",
    },

    "R-VI-01": {
        "policy_mode": "confirmed_finding",
        "issue_domain": "methodological",
    },
    "R-VI-02": {
        "policy_mode": "confirmed_finding",
        "issue_domain": "methodological",
    },
    "R-VI-04A": {
        "policy_mode": "candidate_finding",
        "issue_domain": "methodological",
    },
    "R-VI-05": {
        "policy_mode": "candidate_finding",
        "issue_domain": "methodological",
    },
    "R-VI-07": {
        "policy_mode": "confirmed_finding",
        "issue_domain": "methodological",
    },
    "R-VI-08": {
        "policy_mode": "confirmed_finding",
        "issue_domain": "methodological",
    },

    "R-VII-01": {
        "policy_mode": "confirmed_finding",
        "issue_domain": "methodological",
    },
    "R-VII-03": {
        "policy_mode": "confirmed_finding",
        "issue_domain": "methodological",
    },
    "R-VII-04": {
        "policy_mode": "conditional",
        "issue_domain": "methodological",
    },

    "R-VIII-01": {
        "policy_mode": "confirmed_finding",
        "issue_domain": "dissemination",
    },

    "R-ID-02A": {
        "policy_mode": "candidate_finding",
        "issue_domain": "editorial",
    },
    "R-ID-03": {
        "policy_mode": "confirmed_finding",
        "issue_domain": "editorial",
    },
    "R-ID-04A": {
        "policy_mode": "candidate_finding",
        "issue_domain": "editorial",
    },
    "R-ID-05A": {
        "policy_mode": "candidate_finding",
        "issue_domain": "methodological",
    },
}

def audit_hybrid_policy(
    expected_rule_ids: tuple[str, ...],
) -> dict[str, Any]:
    """
    Pastikan kebijakan hybrid mencakup
    seluruh 40 rule tepat satu kali.
    """

    policy_ids = set(
        HYBRID_POLICY
    )

    expected_ids = set(
        expected_rule_ids
    )

    missing = sorted(
        expected_ids - policy_ids
    )

    unexpected = sorted(
        policy_ids - expected_ids
    )

    valid_modes = {
        "confirmed_finding",
        "candidate_finding",
        "conditional",
    }

    invalid_modes = {
        rule_id:
            item["policy_mode"]
        for rule_id, item
        in HYBRID_POLICY.items()
        if item["policy_mode"]
        not in valid_modes
    }

    return {
        "n_expected":
            len(expected_rule_ids),

        "n_policy":
            len(HYBRID_POLICY),

        "missing_rule_ids":
            missing,

        "unexpected_rule_ids":
            unexpected,

        "invalid_modes":
            invalid_modes,

        "is_valid": (
            len(HYBRID_POLICY) == 40
            and not missing
            and not unexpected
            and not invalid_modes
        ),
    }

def classify_hybrid_finding(
    finding: dict[str, Any],
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    Klasifikasikan satu violation RBS menjadi
    confirmed_finding atau candidate_finding.

    Field RBS sumber tetap dipertahankan.
    """

    rule_id = finding["rule_id"]

    if rule_id not in HYBRID_POLICY:
        raise ValueError(
            f"Rule belum memiliki hybrid policy: {rule_id}"
        )

    if (
        finding["status"] != "violation"
        or finding["violation"] is not True
        or finding["applicability"] != "applicable"
    ):
        raise ValueError(
            f"Hanya violation applicable yang dapat "
            f"diklasifikasikan: {rule_id}"
        )

    policy = HYBRID_POLICY[rule_id]

    evidence = finding.get("evidence")
    mode = policy["policy_mode"]

    concept_assessments = []
    classification_context = {}


    # ========================================================
    # Evidence tidak tersedia
    # ========================================================

    if (
        not isinstance(evidence, dict)
        or not evidence
    ):
        hybrid_class = (
            "candidate_finding"
        )

        classification_reason = (
            "supporting_evidence_unavailable"
        )


    # ========================================================
    # Rule non-conditional
    # ========================================================

    elif mode != "conditional":

        if mode not in {
            "confirmed_finding",
            "candidate_finding",
        }:
            raise ValueError(
                f"Mode hybrid tidak dikenal: {mode}"
            )

        hybrid_class = mode

        classification_reason = (
            "rule_policy_applied"
        )


    # ========================================================
    # Rule conditional
    # R-V-02 dan R-VII-04
    # ========================================================

    else:

        if rule_id not in {
            "R-V-02",
            "R-VII-04",
        }:
            raise ValueError(
                "Rule conditional belum memiliki resolver."
            )

        sampling = (
            read_sampling_method(
                record
            )
        )

        category = sampling[
            "category"
        ]

        empty_concepts = evidence.get(
            "explicitly_empty_concepts",
            [],
        )

        concepts = evidence.get(
            "concepts",
            {},
        )

        classification_context = {
            "sampling_category":
                category,

            "sampling_reading":
                sampling["reading"],
        }


        if not isinstance(
            empty_concepts,
            list,
        ):
            raise ValueError(
                "Format explicitly_empty_concepts "
                "tidak sesuai."
            )


        for concept in empty_concepts:

            concept_evidence = (
                concepts.get(
                    concept,
                    {},
                )
            )

            empty_verified = (
                concept_evidence.get(
                    "state"
                )
                == "empty"
            )


            if not empty_verified:

                concept_class = (
                    "candidate_finding"
                )

                reason = (
                    "explicit_empty_evidence_unavailable"
                )


            elif category not in {
                "probability",
                "non_probability",
            }:

                concept_class = (
                    "candidate_finding"
                )

                reason = (
                    "sampling_category_unknown"
                )


            elif (
                category
                == "non_probability"
                and concept
                in {
                    "sampling_frame",
                    "sampling_fraction",
                }
            ):

                concept_class = (
                    "candidate_finding"
                )

                reason = (
                    "nonprobability_requirement_"
                    "needs_context"
                )


            else:

                concept_class = (
                    "confirmed_finding"
                )

                reason = (
                    "explicit_empty_required_"
                    "concept_under_rule"
                )


            concept_assessments.append({
                "concept":
                    concept,

                "hybrid_class":
                    concept_class,

                "reason":
                    reason,
            })


        if not concept_assessments:

            hybrid_class = (
                "candidate_finding"
            )

            classification_reason = (
                "empty_concept_evidence_unavailable"
            )


        elif any(
            item["hybrid_class"]
            == "candidate_finding"
            for item
            in concept_assessments
        ):

            hybrid_class = (
                "candidate_finding"
            )

            classification_reason = (
                "at_least_one_concept_needs_review"
            )


        else:

            hybrid_class = (
                "confirmed_finding"
            )

            classification_reason = (
                "all_empty_concepts_supported"
            )


    return {
        **finding,

        "hybrid_class":
            hybrid_class,

        "hybrid_classification_reason":
            classification_reason,

        "issue_domain":
            policy["issue_domain"],

        "hybrid_policy_version":
            HYBRID_POLICY_VERSION,

        "hybrid_classifier_version":
            HYBRID_CLASSIFIER_VERSION,

        "hybrid_concept_assessments":
            concept_assessments,

        "hybrid_classification_context":
            classification_context,
    }

def build_related_rule_groups(
    findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Tandai hubungan potensial antar-rule
    tanpa menghapus atau menggabungkan finding.
    """

    active_ids = {
        item["rule_id"]
        for item in findings
    }

    groups = []


    # ========================================================
    # Schedule relationship
    # ========================================================

    schedule_ids = [
        rule_id
        for rule_id
        in (
            "R-III-05A",
            "R-III-06",
        )
        if rule_id
        in active_ids
    ]

    if len(schedule_ids) == 2:

        groups.append({
            "topic":
                "planning_collection_schedule",

            "rule_ids":
                schedule_ids,

            "relation":
                "potential_overlap",

            "instruction": (
                "Bandingkan pasangan tanggal pada evidence. "
                "Jika masalah yang dibahas sama, hindari "
                "pengulangan narasi; pertahankan masalah "
                "jadwal lain yang berbeda."
            ),
        })


    # ========================================================
    # Sampling completeness relationship
    # ========================================================

    sampling_ids = [
        rule_id
        for rule_id
        in (
            "R-V-02",
            "R-V-03A",
            "R-V-03B",
            "R-V-03C",
            "R-V-03D",
            "R-VII-04",
        )
        if rule_id
        in active_ids
    ]

    if len(sampling_ids) > 1:

        groups.append({
            "topic":
                "sampling_completeness",

            "rule_ids":
                sampling_ids,

            "relation":
                "potential_shared_missing_fields",

            "instruction": (
                "Bandingkan field kosong dan applicability "
                "setiap temuan. Jangan menganggap semua "
                "temuan sebagai duplikat atau menaikkan "
                "candidate menjadi confirmed."
            ),
        })


    # ========================================================
    # Inferential sampling relationship
    # ========================================================

    if {
        "R-VII-03",
        "R-VII-04",
    }.issubset(
        active_ids
    ):

        groups.append({
            "topic":
                "inferential_sampling_design",

            "rule_ids": [
                "R-VII-03",
                "R-VII-04",
            ],

            "relation":
                "related_but_not_necessarily_duplicate",

            "instruction": (
                "Ketidaksesuaian metode sampling dan "
                "kelengkapan field merupakan "
                "pemeriksaan berbeda."
            ),
        })


    return groups

def build_hybrid_context(
    record: dict[str, Any],
    rbs_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Bentuk konteks hybrid untuk satu formulir.

    RBS pass tidak menjadi finding.
    Violation diklasifikasikan menjadi confirmed/candidate.
    not_evaluable disimpan sebagai limitation.
    """

    confirmed = []
    candidates = []
    limitations = []

    status_counts = Counter()
    applicability_counts = Counter()


    for result in rbs_results:

        status = result[
            "status"
        ]

        applicability = result[
            "applicability"
        ]

        status_counts[
            status
        ] += 1

        applicability_counts[
            applicability
        ] += 1


        # ====================================================
        # Violation
        # ====================================================

        if status == "violation":

            finding = classify_hybrid_finding(
                result,
                record,
            )

            if (
                finding["hybrid_class"]
                == "confirmed_finding"
            ):

                confirmed.append(
                    finding
                )

            elif (
                finding["hybrid_class"]
                == "candidate_finding"
            ):

                candidates.append(
                    finding
                )

            else:

                raise ValueError(
                    "Hybrid class tidak dikenal."
                )


        # ====================================================
        # Not evaluable
        # ====================================================

        elif status == "not_evaluable":

            limitations.append({
                "rule_id":
                    result["rule_id"],

                "rule_version":
                    result["rule_version"],

                "applicability":
                    result["applicability"],

                "reason":
                    result["reason"],

                "block":
                    result["block"],

                "field":
                    result["field"],
            })


        # ====================================================
        # Pass
        # ====================================================

        elif status == "pass":

            continue


        else:

            raise ValueError(
                f"Status RBS tidak dikenal: {status}"
            )


    related_groups = (
        build_related_rule_groups(
            confirmed
            + candidates
        )
    )


    return {
        "confirmed_findings":
            confirmed,

        "candidate_findings":
            candidates,

        "evaluation_limitations":
            limitations,

        "related_rule_groups":
            related_groups,

        "execution_summary": {
            "n_rules":
                len(rbs_results),

            "status_counts":
                dict(status_counts),

            "applicability_counts":
                dict(
                    applicability_counts
                ),

            "n_confirmed":
                len(confirmed),

            "n_candidates":
                len(candidates),

            "n_limitations":
                len(limitations),
        },

        "interpretation": {
            "confirmed_scope":
                "rule_and_available_form_evidence",

            "expert_validated":
                False,

            "clean_label_inferred":
                False,

            "deduplication_applied":
                False,
        },
    }

def build_llm_rbs_context(
    hybrid_context: dict[str, Any],
) -> dict[str, Any]:
    """
    Ringkas hybrid context menjadi konteks
    yang diberikan kepada LLM.

    Tujuan:
    - tidak mengirim field internal deployment,
    - mempertahankan finding dan evidence penting,
    - merangkum not_evaluable,
    - menjaga struktur sesuai input SFT rebuild.
    """

    def compact_finding(
        finding: dict[str, Any],
    ) -> dict[str, Any]:

        return {
            "rule_id":
                finding["rule_id"],

            "rbs_status":
                finding["status"],

            "severity":
                finding["severity"],

            "issue_domain":
                finding["issue_domain"],

            "message":
                finding["message"],

            "reason":
                finding["reason"],

            "classification_reason":
                finding[
                    "hybrid_classification_reason"
                ],

            "evidence":
                finding["evidence"],

            "concept_assessments":
                finding[
                    "hybrid_concept_assessments"
                ],

            "classification_context":
                finding[
                    "hybrid_classification_context"
                ],
        }


    # ========================================================
    # Confirmed findings
    # ========================================================

    confirmed = [
        compact_finding(
            finding
        )
        for finding
        in hybrid_context[
            "confirmed_findings"
        ]
    ]


    # ========================================================
    # Candidate findings
    # ========================================================

    candidates = [
        compact_finding(
            finding
        )
        for finding
        in hybrid_context[
            "candidate_findings"
        ]
    ]


    # ========================================================
    # Group not_evaluable by
    # applicability + reason
    # ========================================================

    limitation_groups = {}

    for limitation in hybrid_context[
        "evaluation_limitations"
    ]:

        key = (
            limitation[
                "applicability"
            ],
            limitation[
                "reason"
            ],
        )

        limitation_groups.setdefault(
            key,
            [],
        ).append(
            limitation["rule_id"]
        )


    limitations = [
        {
            "applicability":
                applicability,

            "reason":
                reason,

            "rule_ids":
                sorted(rule_ids),
        }
        for (
            applicability,
            reason,
        ), rule_ids
        in limitation_groups.items()
    ]


    return {
        "confirmed_findings":
            confirmed,

        "candidate_findings":
            candidates,

        "evaluation_limitations":
            limitations,

        "related_rule_groups":
            hybrid_context[
                "related_rule_groups"
            ],

        "execution_summary":
            {
                "n_rules":
                    hybrid_context[
                        "execution_summary"
                    ]["n_rules"],

                "status_counts":
                    hybrid_context[
                        "execution_summary"
                    ]["status_counts"],

                "applicability_counts":
                    hybrid_context[
                        "execution_summary"
                    ]["applicability_counts"],
            },

        "interpretation":
            hybrid_context[
                "interpretation"
            ],
    }