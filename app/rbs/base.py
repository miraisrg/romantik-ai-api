# ============================================================
# ROMANTIK AI API
# RBS — Base Result Builder
# ============================================================

from __future__ import annotations

import re

from decimal import Decimal, InvalidOperation
from typing import Any


# ============================================================
# 1. RULE METADATA
# ============================================================
#
# Untuk sementara baru memuat metadata kelompok pertama.
# Nanti metadata rule lain ditambahkan ketika masing-masing
# kelompok rule dipindahkan dari notebook final.
# ============================================================

RULE_GROUP_VERSION = "rebuild_group_01_v03"


RULE_GROUP_METADATA = {
    "R-IV-07": (
        "blok_iv",
        "cakupan_wilayah_pengumpulan_data",
        "error",
    ),

    "R-VI-01": (
        "blok_vi",
        "apakah_melakukan_uji_coba",
        "warning",
    ),

    "R-VI-05": (
        "blok_vi",
        "jumlah_supervisor",
        "warning",
    ),

    "R-VI-08": (
        "blok_vi",
        "metode_pemeriksaan_kualitas",
        "error",
    ),
}

RULE_GROUP_METADATA.update({
    "R-VI-02": (
        "blok_vi",
        "apakah_melakukan_uji_coba",
        "warning",
    ),

    "R-VI-04A": (
        "blok_vi",
        "persyaratan_pendidikan_terendah",
        "warning",
    ),

    "R-VI-07": (
        "blok_vi",
        "apakah_melakukan_pelatihan",
        "error",
    ),
})

RULE_GROUP_METADATA.update({
    "R-V-03A": (
        "blok_v",
        "probability_method_detail",
        "error",
    ),
    "R-V-03B": (
        "blok_v",
        "sampling_frame",
        "error",
    ),
    "R-V-03C": (
        "blok_v",
        "sampling_fraction",
        "error",
    ),
    "R-V-03D": (
        "blok_v",
        "sampling_error",
        "error",
    ),
    "R-VII-03": (
        "blok_vii",
        "metode_analisis",
        "error",
    ),
})

RULE_GROUP_METADATA.update({
    "R-V-14A": (
        "blok_v",
        "unit_sampel",
        "warning",
    ),

    "R-V-12": (
        "blok_v",
        "sampling_error",
        "warning",
    ),

    "R-V-11": (
        "blok_v",
        "sampling_error",
        "warning",
    ),
})

RULE_GROUP_METADATA.update({
    "R-VII-01": (
        "blok_vii",
        "tahapan_pengolahan_data",
        "error",
    ),

    "R-VIII-01": (
        "blok_viii",
        "ketersediaan_produk",
        "error",
    ),
})

RULE_GROUP_METADATA.update({
    "R-I-01": (
        "blok_i",
        "instansi_penyelenggara",
        "error",
    ),

    "R-I-02A": (
        "blok_i",
        "instansi_penyelenggara",
        "warning",
    ),

    "R-I-04": (
        "blok_i",
        "alamat_instansi_penyelenggara",
        "error",
    ),

    "R-II-01": (
        "blok_ii",
        "unit_penanggung_jawab",
        "error",
    ),

    "R-II-02": (
        "blok_ii",
        "penanggung_jawab_teknis",
        "error",
    ),
})

RULE_GROUP_METADATA.update({
    "R-III-04": (
        "blok_iii",
        "rencana_jadwal_kegiatan",
        "error",
    ),
    "R-III-05A": (
        "blok_iii",
        "rencana_jadwal_kegiatan",
        "error",
    ),
    "R-III-06": (
        "blok_iii",
        "rencana_jadwal_kegiatan",
        "error",
    ),
})

RULE_GROUP_METADATA.update({
    "R-III-08A": (
        "blok_iii",
        "variabel_yang_dikumpulkan",
        "warning",
    ),

    "R-III-09": (
        "blok_iii",
        "variabel_yang_dikumpulkan",
        "error",
    ),

    "R-III-10": (
        "blok_iii",
        "variabel_yang_dikumpulkan",
        "warning",
    ),

    "R-III-12": (
        "blok_iii",
        "variabel_yang_dikumpulkan",
        "warning",
    ),
})

RULE_GROUP_METADATA.update({
    "R-IV-01": (
        "blok_iv",
        "frekuensi_penyelenggara",
        "error",
    ),

    "R-IV-05": (
        "blok_iv",
        "tipe_pengumpulan_data",
        "error",
    ),

    "R-IV-09": (
        "blok_iv",
        "metode_pengumpulan_data",
        "error",
    ),
})

RULE_GROUP_METADATA.update({
    "R-V-01": (
        "blok_v",
        None,
        "error",
    ),

    "R-V-02": (
        "blok_v",
        None,
        "error",
    ),

    "R-V-08A": (
        "blok_v",
        "fraksi_sampel_keseluruhan",
        "warning",
    ),

    "R-VII-04": (
        "blok_vii",
        "metode_analisis",
        "error",
    ),
})

RULE_GROUP_METADATA.update({
    "R-ID-02A": (
        "identitas",
        "nama_kegiatan",
        "error",
    ),

    "R-ID-03": (
        "identitas",
        "nama_kegiatan",
        "warning",
    ),

    "R-ID-04A": (
        "identitas",
        "nama_kegiatan",
        "warning",
    ),

    "R-ID-05A": (
        "identitas",
        "tahun_kegiatan",
        "error",
    ),
})

# ============================================================
# 2. RULE RESULT BUILDER
# ============================================================

def build_rule_result(
    rule_id: str,
    status: str,
    applicability: str,
    reason: str,
    evidence: dict[str, Any],
    message: str | None = None,
) -> dict[str, Any]:
    """
    Bentuk hasil standar satu rule.

    Parameters
    ----------
    status
        - pass
        - violation
        - not_evaluable

    applicability
        - applicable
        - not_applicable
        - unknown

    Notes
    -----
    `not_applicable` tetap memakai status `pass`,
    tetapi dibedakan melalui field applicability.

    `unknown` harus menggunakan `not_evaluable`.
    """

    valid_status = {
        "pass",
        "violation",
        "not_evaluable",
    }

    if status not in valid_status:
        raise ValueError(
            f"Status tidak valid: {status}"
        )


    valid_applicability = {
        "applicable",
        "not_applicable",
        "unknown",
    }

    if applicability not in valid_applicability:
        raise ValueError(
            "Applicability tidak valid: "
            f"{applicability}"
        )


    if (
        applicability == "not_applicable"
        and status != "pass"
    ):
        raise ValueError(
            "Aturan tidak berlaku harus "
            "diberi status pass."
        )


    if (
        applicability == "unknown"
        and status != "not_evaluable"
    ):
        raise ValueError(
            "Applicability unknown harus "
            "not_evaluable."
        )


    if rule_id not in RULE_GROUP_METADATA:
        raise KeyError(
            f"Metadata rule tidak ditemukan: {rule_id}"
        )


    block, field, severity = (
        RULE_GROUP_METADATA[rule_id]
    )


    return {
        "rule_id": rule_id,

        "rule_version": (
            RULE_GROUP_VERSION
        ),

        "status": status,

        "violation": (
            status == "violation"
        ),

        "applicability": (
            applicability
        ),

        "block": block,

        "field": field,

        "severity": severity,

        "message": message,

        "reason": reason,

        "evidence": evidence,
    }


# ============================================================
# 3. STAFF COUNT PARSER
# ============================================================

def parse_staff_count(
    value: Any,
) -> int | None:
    """
    Parse jumlah petugas sebagai bilangan bulat.

    Menerima:
    - integer
    - angka string
    - angka dengan akhiran "orang"
    - angka desimal yang ekuivalen integer, mis. "3.0"

    Sesuai keputusan rule engine final:
    nilai negatif dikonversi menjadi positif karena tanda minus
    dianggap kesalahan pengisian jumlah petugas.

    Tidak menerima:
    - boolean
    - pecahan non-integer
    - rentang
    - narasi bebas
    """

    if (
        isinstance(value, bool)
        or value is None
    ):
        return None


    if not isinstance(
        value,
        (str, int, float),
    ):
        return None


    match = re.fullmatch(
        r"(-?[0-9]+(?:\.[0-9]+)?)"
        r"\s*(?:orang)?",
        str(value).strip(),
        flags=re.IGNORECASE,
    )


    if match is None:
        return None


    try:
        number = Decimal(
            match.group(1)
        )

    except InvalidOperation:
        return None


    if (
        not number.is_finite()
        or number
        != number.to_integral_value()
    ):
        return None


    return abs(
        int(number)
    )