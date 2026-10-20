# ============================================================
# ROMANTIK AI API
# Request & Response Schemas
# ============================================================

from typing import Any

from pydantic import BaseModel, Field


# ------------------------------------------------------------
# REQUEST
# ------------------------------------------------------------

class ReviewRequest(BaseModel):
    """
    Request pemeriksaan satu formulir ROMANTIK.

    `form` menerima raw JSON formulir ROMANTIK.
    """

    form: dict[str, Any]


# ------------------------------------------------------------
# RBS FINDING
# ------------------------------------------------------------

class RBSFinding(BaseModel):
    """
    Satu temuan aktif dari Rule-Based System
    yang ditampilkan kepada pengguna.
    """

    rule_id: str

    severity: str | None = None

    message: str | None = None

    evidence: Any | None = None


# ------------------------------------------------------------
# RBS NOT EVALUABLE
# ------------------------------------------------------------

class RBSNotEvaluable(BaseModel):
    """
    Satu aturan dari Rule-Based System yang berstatus
    belum dapat dievaluasi (not_evaluable).
    """

    rule_id: str

    status: str = "not_evaluable"

    applicability: str | None = None

    reason: str | None = None

    message: str | None = None

    evidence: Any | None = None


# ------------------------------------------------------------
# RBS SUMMARY
# ------------------------------------------------------------

class RBSSummary(BaseModel):
    """
    Ringkasan hasil Rule-Based System.
    """

    n_findings: int = 0

    n_not_evaluable: int = 0

    findings: list[RBSFinding] = Field(
        default_factory=list
    )

    not_evaluable: list[RBSNotEvaluable] = Field(
        default_factory=list
    )


# ------------------------------------------------------------
# FORM METADATA
# ------------------------------------------------------------

class ReviewMetadata(BaseModel):
    """
    Metadata utama formulir ROMANTIK.
    """

    id_trans: str | None = None

    nama_kegiatan: str | None = None

    tahun_kegiatan: int | str | None = None

    instansi: str | None = None


# ------------------------------------------------------------
# RESPONSE
# ------------------------------------------------------------

class ReviewResponse(BaseModel):
    """
    Response pemeriksaan Hybrid AI.
    """

    status: str

    metadata: ReviewMetadata

    rbs: RBSSummary

    hybrid_review: str

    processing_time_seconds: float | None = None
