# ============================================================
# ROMANTIK AI API
# LLM PROMPT BUILDER
# ============================================================

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any


# ============================================================
# SYSTEM INSTRUCTION
# ============================================================

SYSTEM_PROMPT = (
    "Anda membantu pemeriksaan formulir kegiatan statistik ROMANTIK. "
    "Berdasarkan formulir final dan konteks RBS, tuliskan catatan "
    "pemeriksaan yang jelas, relevan, dan dapat ditindaklanjuti. "
    "Candidate findings perlu ditafsirkan sesuai isian formulir. "
    "Jangan mengaku telah membaca dokumen atau mengetahui hasil rapat "
    "yang tidak tersedia dalam input. "
    "Keluarkan hanya catatan dalam HTML menggunakan paragraf <p>."
)


# ============================================================
# FORM PAYLOAD
# ============================================================

def build_llm_form_payload(
    canonical_record: dict[str, Any],
) -> dict[str, Any]:
    """
    Bentuk payload formulir yang diberikan ke LLM.

    Hanya membawa data formulir final yang relevan dengan
    pemeriksaan. Catatan pemeriksaan historis,
    catatan rekomendasi, dan status rekomendasi
    tidak dimasukkan ke prompt.
    """

    return {
        "nama_kegiatan":
            canonical_record.get(
                "nama_kegiatan"
            ),

        "tahun_kegiatan":
            canonical_record.get(
                "tahun_kegiatan"
            ),

        "instansi":
            canonical_record.get(
                "instansi"
            ),

        "form":
            deepcopy(
                canonical_record.get(
                    "form",
                    {},
                )
            ),
    }


# ============================================================
# COMPACT JSON
# ============================================================

def dumps_prompt_json(
    value: Any,
) -> str:
    """
    Serialisasi JSON ringkas untuk prompt.
    """

    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    )


# ============================================================
# USER PROMPT
# ============================================================

def build_user_prompt(
    canonical_record: dict[str, Any],
    llm_rbs_context: dict[str, Any],
) -> str:
    """
    Bentuk role user sesuai format SFT rebuild.
    """

    form_payload = (
        build_llm_form_payload(
            canonical_record
        )
    )

    form_text = dumps_prompt_json(
        form_payload
    )

    rbs_text = dumps_prompt_json(
        llm_rbs_context
    )

    return (
        "Periksa formulir kegiatan statistik berikut.\n\n"
        "FORMULIR_FINAL:\n"
        f"{form_text}\n\n"
        "KONTEKS_RBS:\n"
        f"{rbs_text}"
    )


# ============================================================
# CHAT MESSAGES
# ============================================================

def build_prompt_messages(
    canonical_record: dict[str, Any],
    llm_rbs_context: dict[str, Any],
) -> list[dict[str, str]]:
    """
    Bangun dua role input inference:
    system + user.

    Role assistant tidak ditambahkan karena
    jawaban akan dihasilkan oleh model.
    """

    user_prompt = build_user_prompt(
        canonical_record,
        llm_rbs_context,
    )

    return [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": user_prompt,
        },
    ]