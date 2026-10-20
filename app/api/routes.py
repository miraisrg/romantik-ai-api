# ============================================================
# ROMANTIK AI API
# API Routes
# ============================================================

from time import perf_counter

from fastapi import APIRouter

from app.schemas.review import (
    ReviewRequest,
    ReviewResponse,
    ReviewMetadata,
    RBSFinding,
    RBSNotEvaluable,
    RBSSummary,
)

from app.services.review_service import (
    run_review_pipeline,
)


router = APIRouter()


# ------------------------------------------------------------
# HEALTH CHECK
# ------------------------------------------------------------

@router.get("/health")
def health_check():
    """
    Memastikan API berjalan.
    """

    return {
        "status": "ok",
        "service": "romantik-ai-api",
    }


# ------------------------------------------------------------
# REVIEW ENDPOINT
# ------------------------------------------------------------

@router.post(
    "/api/v1/review",
    response_model=ReviewResponse,
)
def review_form(
    request: ReviewRequest,
):
    """
    Jalankan pemeriksaan satu formulir ROMANTIK.

    Pipeline:
    1. Canonicalization
    2. Rule-Based System
    3. Hybrid Interface
    4. Compact RBS Context
    5. Prompt Construction
    6. Fine-tuned LLM Inference
    """

    start_time = perf_counter()


    # ========================================================
    # 1. Jalankan pipeline lengkap
    # ========================================================

    result = run_review_pipeline(
        request.form
    )


    canonical_record = result[
        "canonical_record"
    ]

    rbs_results = result[
        "rbs_results"
    ]

    rbs_findings = result[
        "rbs_findings"
    ]

    llm_result = result[
        "llm_result"
    ]


    # ========================================================
    # 2. Metadata formulir
    # ========================================================

    raw_id_trans = canonical_record.get(
        "id_trans"
    )

    metadata = ReviewMetadata(
        id_trans=(
            str(raw_id_trans)
            if raw_id_trans is not None
            else None
        ),

        nama_kegiatan=canonical_record.get(
            "nama_kegiatan"
        ),

        tahun_kegiatan=canonical_record.get(
            "tahun_kegiatan"
        ),

        instansi=canonical_record.get(
            "instansi"
        ),
    )


    # ========================================================
    # 3. Temuan RBS untuk frontend
    # ========================================================

    findings = [
        RBSFinding(
            rule_id=finding[
                "rule_id"
            ],

            severity=finding.get(
                "severity"
            ),

            message=finding.get(
                "message"
            ),

            evidence=finding.get(
                "evidence"
            ),
        )

        for finding
        in rbs_findings
    ]


    # ========================================================
    # 4. Aturan belum dapat dievaluasi (not_evaluable)
    # ========================================================

    raw_not_evaluable = [
        item
        for item in rbs_results
        if item.get("status")
        == "not_evaluable"
    ]

    not_evaluable = [
        RBSNotEvaluable(
            rule_id=item[
                "rule_id"
            ],

            status=item.get(
                "status",
                "not_evaluable",
            ),

            applicability=item.get(
                "applicability"
            ),

            reason=item.get(
                "reason"
            ),

            message=item.get(
                "message"
            ),

            evidence=item.get(
                "evidence"
            ),
        )

        for item
        in raw_not_evaluable
    ]

    n_not_evaluable = len(
        not_evaluable
    )


    # ========================================================
    # 5. Ringkasan RBS
    # ========================================================

    rbs_summary = RBSSummary(
        n_findings=len(
            findings
        ),

        n_not_evaluable=
            n_not_evaluable,

        findings=findings,

        not_evaluable=not_evaluable,
    )


    # ========================================================
    # 6. Status inference
    # ========================================================

    inference_status = llm_result.get(
        "status"
    )

    if inference_status == "generated":
        response_status = "success"

    else:
        response_status = (
            inference_status
            or "error"
        )


    # ========================================================
    # 7. Waktu proses
    # ========================================================

    processing_time = (
        perf_counter()
        - start_time
    )


    # ========================================================
    # 8. Response
    # ========================================================

    return ReviewResponse(
        status=response_status,

        metadata=metadata,

        rbs=rbs_summary,

        hybrid_review=llm_result.get(
            "review_html",
            "",
        ),

        processing_time_seconds=round(
            processing_time,
            3,
        ),
    )
