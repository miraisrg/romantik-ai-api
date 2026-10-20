# ============================================================
# ROMANTIK AI API
# REVIEW SERVICE
# ============================================================

from __future__ import annotations

from typing import Any

from app.preprocessing.canonicalizer import canonicalize_record
from app.rbs.engine import run_current_rbs
from app.rbs.hybrid import build_hybrid_context
from app.rbs.hybrid import (
    build_hybrid_context,
    build_llm_rbs_context,
)
from app.llm.prompt_builder import (
    build_prompt_messages,
)
from app.llm.inference import generate_review


def prepare_review_pipeline(
    raw_record: dict[str, Any],
) -> dict[str, Any]:
    """
    Siapkan satu formulir untuk proses pemeriksaan.

    Alur:
    raw JSON
    -> canonicalization
    -> RBS 40 rules
    -> active RBS findings
    -> hybrid context

    Belum memanggil LLM.
    """

    # ========================================================
    # 1. Canonicalization
    # ========================================================

    canonical_record = canonicalize_record(
        raw_record
    )


    # ========================================================
    # 2. Run 40 RBS rules
    # ========================================================

    rbs_results = run_current_rbs(
        canonical_record
    )


    # ========================================================
    # 3. Active RBS findings
    # ========================================================

    rbs_findings = [
        result
        for result in rbs_results
        if result["status"] == "violation"
    ]


    # ========================================================
    # 4. Hybrid context for LLM
    # ========================================================

    hybrid_context = build_hybrid_context(
        canonical_record,
        rbs_results,
    )

    llm_rbs_context = build_llm_rbs_context(
        hybrid_context
    )

    prompt_messages = build_prompt_messages(
        canonical_record,
        llm_rbs_context,
    )


    # ========================================================
    # 5. Internal pipeline result
    # ========================================================

    return {
        "canonical_record":
            canonical_record,

        "rbs_results":
            rbs_results,

        "rbs_findings":
            rbs_findings,

        "hybrid_context":
            hybrid_context,

        "llm_rbs_context":
            llm_rbs_context,

        "prompt_messages":
            prompt_messages,
    }

def run_review_pipeline(
    raw_record: dict[str, Any],
) -> dict[str, Any]:
    """
    Jalankan pipeline pemeriksaan ROMANTIK secara lengkap.

    Tahapan:
    1. Canonicalization
    2. RBS
    3. Hybrid context
    4. Compact LLM context
    5. Prompt construction
    6. LLM inference

    Catatan:
    Fungsi ini membutuhkan environment GPU
    ketika generate_review() dijalankan.
    """

    # ========================================================
    # 1. Siapkan seluruh input model
    # ========================================================

    prepared = prepare_review_pipeline(
        raw_record
    )


    # ========================================================
    # 2. Jalankan LLM inference
    # ========================================================

    llm_result = generate_review(
        prepared[
            "prompt_messages"
        ]
    )


    # ========================================================
    # 3. Gabungkan hasil
    # ========================================================

    return {
        **prepared,
        "llm_result":
            llm_result,
    }