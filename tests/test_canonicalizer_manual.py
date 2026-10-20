# ============================================================
# ROMANTIK AI API
# MANUAL TEST — CANONICALIZATION
# ============================================================

from pathlib import Path
import json

from app.preprocessing.canonicalizer import (
    canonicalize_record,
)


# ------------------------------------------------------------
# 1. PATH
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "sample_input"
    / "sample_romantik.json"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "sample_output"
    / "sample_romantik_canonical.json"
)


# ------------------------------------------------------------
# 2. LOAD RAW SAMPLE
# ------------------------------------------------------------

with INPUT_PATH.open(
    "r",
    encoding="utf-8",
) as handle:

    raw_record = json.load(
        handle
    )


# ------------------------------------------------------------
# 3. CANONICALIZE
# ------------------------------------------------------------

canonical_record = canonicalize_record(
    raw_record
)


# ------------------------------------------------------------
# 4. SAVE RESULT
# ------------------------------------------------------------

OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True,
)

with OUTPUT_PATH.open(
    "w",
    encoding="utf-8",
) as handle:

    json.dump(
        canonical_record,
        handle,
        ensure_ascii=False,
        indent=2,
    )


# ------------------------------------------------------------
# 5. BASIC VALIDATION
# ------------------------------------------------------------

required_top_level = [
    "id_trans",
    "nama_kegiatan",
    "tahun_kegiatan",
    "instansi",
    "schema_family",
    "form",
]

missing = [
    key
    for key in required_top_level
    if key not in canonical_record
]


print("=" * 72)
print("ROMANTIK — CANONICALIZATION TEST")
print("=" * 72)

print(
    f"Input             : "
    f"{INPUT_PATH}"
)

print(
    f"Output            : "
    f"{OUTPUT_PATH}"
)

print(
    f"Schema family     : "
    f"{canonical_record.get('schema_family')}"
)

print(
    f"ID transaksi      : "
    f"{canonical_record.get('id_trans')}"
)

print(
    f"Nama kegiatan     : "
    f"{canonical_record.get('nama_kegiatan')}"
)

print(
    f"Missing top-level : "
    f"{missing}"
)


form = canonical_record.get(
    "form",
    {}
)

print(
    f"Canonical blocks  : "
    f"{list(form.keys())}"
)


print("\n" + "=" * 72)

if not missing:
    print(
        "STATUS: canonicalization sample berhasil."
    )
else:
    print(
        "STATUS: canonicalization perlu diperiksa."
    )

print("=" * 72)