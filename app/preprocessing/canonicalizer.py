# ============================================================
# ROMANTIK AI API
# Canonicalization Pipeline
# ============================================================
#
# Tujuan:
#   Mengubah raw record ROMANTIK dari berbagai schema family
#   menjadi satu canonical schema yang konsisten.
#
# Supported schema:
#   - modern_nested
#   - legacy_flat_v1
#   - legacy_flat_v2
#
# Catatan:
#   Kode ini berasal dari pipeline canonicalization penelitian,
#   tetapi komponen audit/DataFrame notebook tidak disertakan.
# ============================================================

from __future__ import annotations

import ast
import json
import re
import unicodedata

from copy import deepcopy
from typing import Any


# ============================================================
# 1. FORM PARSING
# ============================================================

def parse_json_object(
    value: Any,
) -> tuple[dict[str, Any] | None, str]:
    """
    Parse nilai yang diharapkan berupa JSON object.

    Returns
    -------
    tuple
        parsed object dan status parsing.
    """

    if value is None:
        return None, "null"

    if isinstance(value, dict):
        return value, "already_parsed"

    if not isinstance(value, str):
        return (
            None,
            f"unexpected_type:{type(value).__name__}",
        )

    if not value.strip():
        return None, "empty_string"

    try:
        parsed = json.loads(value)

    except json.JSONDecodeError:
        return None, "invalid_json"

    if not isinstance(parsed, dict):
        return (
            None,
            f"unexpected_root:{type(parsed).__name__}",
        )

    return parsed, "valid_json"


# ============================================================
# 2. SCHEMA FAMILY DETECTION
# ============================================================

def detect_schema_family(
    form: dict[str, Any],
) -> str:
    """
    Identifikasi schema family formulir ROMANTIK.
    """

    keys = set(form.keys())

    if (
        "blok_i" in keys
        or "blok_iii" in keys
    ):
        return "modern_nested"

    if {
        "Judul",
        "Tujuan_Dan_Manfaat_Kegiatan",
    }.intersection(keys):
        return "legacy_flat_v1"

    if {
        "judul",
        "Tujuan_Survei",
        "Peubah_yang_dikumpulkan",
    }.intersection(keys):
        return "legacy_flat_v2"

    return "unknown"


# ============================================================
# 3. NORMALIZATION HELPERS
# ============================================================

def normalize_label(
    value: Any,
) -> str | None:
    """
    Normalisasi label kategorikal menjadi lowercase snake_case.
    """

    if value is None:
        return None

    text = str(value).strip()

    if not text:
        return None

    text = unicodedata.normalize(
        "NFKC",
        text,
    )

    text = text.lower()

    text = re.sub(
        r"[^a-z0-9]+",
        "_",
        text,
    )

    text = re.sub(
        r"_+",
        "_",
        text,
    )

    return text.strip("_")


def normalize_yes_no(
    value: Any,
) -> bool | None:
    """
    Normalisasi representasi Ya/Tidak menjadi boolean.
    """

    if value is None:
        return None

    text = str(value).strip().lower()

    if not text:
        return None

    if text.startswith("ya"):
        return True

    if text.startswith("tidak"):
        return False

    return None


def extract_explanation(
    value: Any,
) -> str | None:
    """
    Ambil teks setelah pola `Penjelasan:`.
    """

    if not isinstance(
        value,
        str,
    ):
        return None

    match = re.search(
        r"penjelasan\s*:\s*(.+)$",
        value,
        flags=re.IGNORECASE,
    )

    if match:
        return match.group(1).strip()

    return None


def extract_option_value(
    value: Any,
) -> Any:
    """
    Ambil value dari representasi pilihan legacy.
    """

    if isinstance(value, dict):
        return value.get("value")

    if isinstance(value, list):
        return [
            item.get("value")
            if isinstance(item, dict)
            else item
            for item in value
        ]

    return value


# ============================================================
# 4. EMBEDDED JSON PARSER
# ============================================================

def parse_embedded_json(
    value: Any,
) -> Any:
    """
    Parse structured value yang tersimpan sebagai string.

    Strategi:
    1. JSON standar.
    2. Double-encoded JSON.
    3. Python literal legacy.
    4. Jika gagal, nilai asli dipertahankan.
    """

    if not isinstance(
        value,
        str,
    ):
        return value

    text = value.strip()

    if not text:
        return None

    # --------------------------------------------------------
    # Standard JSON
    # --------------------------------------------------------

    try:
        parsed = json.loads(text)

        if isinstance(parsed, str):

            nested_text = (
                parsed.strip()
            )

            if (
                nested_text.startswith("[")
                or nested_text.startswith("{")
            ):

                try:
                    parsed = json.loads(
                        nested_text
                    )

                except json.JSONDecodeError:
                    pass

        if isinstance(
            parsed,
            (list, dict),
        ):
            return parsed

    except json.JSONDecodeError:
        pass

    # --------------------------------------------------------
    # Python literal representation
    # --------------------------------------------------------

    try:
        parsed = ast.literal_eval(
            text
        )

        if isinstance(
            parsed,
            (list, dict),
        ):
            return parsed

    except (
        ValueError,
        SyntaxError,
    ):
        pass

    return value


# ============================================================
# 5. VARIABLE CANONICALIZATION
# ============================================================

def canonicalize_variables(
    value: Any,
) -> dict[str, Any]:
    """
    Menyeragamkan struktur variabel.

    Output:
    {
        "items": [...],
        "raw_text": ...
    }

    `raw_text` dipertahankan sebagai fallback jika nilai
    legacy tidak berhasil diparse.
    """

    parsed_value = (
        parse_embedded_json(
            value
        )
    )

    variables = []

    raw_text = None


    if isinstance(
        parsed_value,
        list,
    ):

        for item in parsed_value:

            if not isinstance(
                item,
                dict,
            ):
                continue

            variables.append(
                {
                    "nama": (
                        item.get("nama")
                    ),

                    "definisi": (
                        item.get("definisi")
                    ),

                    "referensi_waktu": (
                        item.get(
                            "referensi_waktu"
                        )
                        or item.get(
                            "periode"
                        )
                    ),

                    "sumber": (
                        item.get("sumber")
                    ),
                }
            )


    elif isinstance(
        parsed_value,
        str,
    ):

        raw_text = (
            parsed_value
        )


    return {
        "items": variables,
        "raw_text": raw_text,
    }


# ============================================================
# 6. SCHEDULE CANONICALIZATION
# ============================================================

def create_schedule_period(
    start: Any,
    end: Any,
) -> dict[str, Any]:
    """
    Bentuk satu periode jadwal canonical.
    """

    return {
        "awal": start,
        "akhir": end,
    }


def canonicalize_legacy_schedule(
    form: dict[str, Any],
    schema_family: str,
) -> dict[str, Any]:
    """
    Seragamkan jadwal legacy menjadi struktur modern.
    """

    if schema_family == "legacy_flat_v1":

        return {
            "perencanaan_kegiatan": (
                create_schedule_period(
                    form.get(
                        "Perencanaan_Persiapan_Mulai"
                    ),
                    form.get(
                        "Perencanaan_Persiapan_Selesai"
                    ),
                )
            ),

            "pengumpulan_data": (
                create_schedule_period(
                    form.get(
                        "Pengumpulan_Data_Mulai"
                    ),
                    form.get(
                        "Pengumpulan_Data_Selesai"
                    ),
                )
            ),

            "pengolahan_data": (
                create_schedule_period(
                    form.get(
                        "Pengolahan_Mulai"
                    ),
                    form.get(
                        "Pengolahan_Selesai"
                    ),
                )
            ),

            "analisis": (
                create_schedule_period(
                    form.get(
                        "Analisis_Mulai"
                    ),
                    form.get(
                        "Analisis_Selesai"
                    ),
                )
            ),

            "penyajian": (
                create_schedule_period(
                    form.get(
                        "Diseminasi_Mulai"
                    ),
                    form.get(
                        "Diseminasi_Selesai"
                    ),
                )
            ),
        }


    if schema_family == "legacy_flat_v2":

        return {
            "perencanaan_kegiatan": (
                create_schedule_period(
                    form.get(
                        "Perencanaan_Persiapan_Mulai"
                    ),
                    form.get(
                        "Perencanaan_Persiapan_Selesai"
                    ),
                )
            ),

            "pengumpulan_data": (
                create_schedule_period(
                    form.get(
                        "Pelaksanaan_Lapangan_Mulai"
                    ),
                    form.get(
                        "Pelaksanaan_Lapangan_Selesai"
                    ),
                )
            ),

            "pengolahan_data": (
                create_schedule_period(
                    form.get(
                        "Pengolahan_Mulai"
                    ),
                    form.get(
                        "Pengolahan_Selesai"
                    ),
                )
            ),

            "analisis": (
                create_schedule_period(
                    form.get(
                        "Analisis_Mulai"
                    ),
                    form.get(
                        "Analisis_Selesai"
                    ),
                )
            ),

            "penyajian": (
                create_schedule_period(
                    form.get(
                        "Penyajian_Mulai"
                    ),
                    form.get(
                        "Penyajian_Selesai"
                    ),
                )
            ),
        }


    return {}


# ============================================================
# 7. CANONICAL FORM TEMPLATE
# ============================================================

def create_empty_canonical_form(
    schema_family: str,
) -> dict[str, Any]:
    """
    Struktur canonical dasar untuk seluruh schema family.
    """

    return {
        "metadata": {
            "schema_family": (
                schema_family
            ),
            "nomor_rekomendasi": None,
            "jenis_kegiatan": None,
            "judul": None,
        },

        "blok_i": {
            "instansi_penyelenggara": None,

            "alamat_instansi_penyelenggara": {
                "alamat": None,
                "telepon": None,
                "email": None,
                "faksimile": None,
            },
        },

        "blok_ii": {
            "penanggung_jawab_teknis": {
                "nama": None,
                "jabatan": None,
                "alamat": None,
                "telepon": None,
                "email": None,
                "faksimile": None,
            }
        },

        "blok_iii": {
            "latar_belakang_kegiatan": None,

            "tujuan_kegiatan": None,

            "rencana_jadwal_kegiatan": {},

            "variabel_yang_dikumpulkan": {
                "items": [],
                "raw_text": None,
            },
        },

        "blok_iv": {
            "kegiatan_ini_dilakukan": None,
            "frekuensi_penyelenggara": None,
            "tipe_pengumpulan_data": None,

            "cakupan_wilayah_pengumpulan_data": None,

            "wilayah_pengumpulan_data": [],

            "metode_pengumpulan_data": None,

            "metode_pengumpulan_data_lainnya": None,

            "sarana_pengumpulan_data": None,
        },

        "blok_v": {
            "cara_pengumpulan_data": None,
            "metode_penelitian": None,

            "metode_sampel_non_probabilitas": None,

            "jenis_rancangan_sampel": None,
            "rancangan_sampel": None,
            "kerangka_sampel": None,

            "metode_pemilihan_sampel": None,

            "fraksi_sampel": None,
            "unit_sampel": None,

            "perkiraan_sampling_error": None,

            "responden": None,
        },

        "blok_vi": {
            "apakah_melakukan_uji_coba": None,
            "penjelasan_uji_coba": None,

            "petugas_pengumpulan_data": None,

            "persyaratan_pendidikan_terendah": None,

            "jumlah_supervisor": None,
            "jumlah_enumerator": None,

            "apakah_melakukan_pelatihan": None,
            "penjelasan_pelatihan": None,

            "metode_pemeriksaan_kualitas": None,
        },

        "blok_vii": {
            "tahapan_pengolahan_data": {
                "editing": None,
                "coding": None,
                "data_entry": None,
                "validasi": None,
            },

            "metode_analisis": None,

            "unit_analisis": None,

            "tingkat_penyajian_hasil_analisis": None,
        },

        "blok_viii": {
            "ketersediaan_produk_tercetak": None,

            "ketersediaan_produk_digital": None,

            "ketersediaan_produk_mikrodata": None,

            "ketersediaan_produk_makrodata": None,

            "waktu_ketersediaan_hasil": None,
        },

        "blok_ix": {
            "file_berkas_pendukung": [],
        },
    }


# ============================================================
# 8. LEGACY V1 CANONICALIZER
# ============================================================

def canonicalize_legacy_v1(
    form: dict[str, Any],
) -> dict[str, Any]:
    """
    Convert legacy flat schema v1 ke canonical schema.
    """

    canonical = (
        create_empty_canonical_form(
            "legacy_flat_v1"
        )
    )


    canonical["metadata"].update(
        {
            "nomor_rekomendasi": (
                form.get(
                    "Nomor_Rekomendasi"
                )
            ),

            "jenis_kegiatan": (
                form.get(
                    "Jenis_Kegiatan"
                )
            ),

            "judul": (
                form.get("Judul")
            ),
        }
    )


    canonical["blok_i"][
        "instansi_penyelenggara"
    ] = form.get(
        "Instansi_Pemerintah_Penyelenggara"
    )


    canonical["blok_i"][
        "alamat_instansi_penyelenggara"
    ] = {
        "alamat": (
            form.get(
                "Alamat_Lengkap_Instansi_Penyelenggara"
            )
        ),
        "telepon": (
            form.get("Telepon")
        ),
        "email": (
            form.get("E-mail")
        ),
        "faksimile": (
            form.get("Fax")
        ),
    }


    canonical["blok_ii"][
        "penanggung_jawab_teknis"
    ] = {
        "nama": (
            form.get(
                "Nama_Manajer_Survei"
            )
        ),
        "jabatan": (
            form.get(
                "Jabatan_Manajer_Survei"
            )
        ),
        "alamat": (
            form.get(
                "Alamat_Manajer_Survei"
            )
        ),
        "telepon": (
            form.get(
                "Telepon_Manajer_Survei"
            )
        ),
        "email": (
            form.get(
                "E-mail_Manajer_Survei"
            )
        ),
        "faksimile": (
            form.get(
                "Fax_Manajer_Survei"
            )
        ),
    }


    canonical["blok_iii"][
        "tujuan_kegiatan"
    ] = form.get(
        "Tujuan_Dan_Manfaat_Kegiatan"
    )


    canonical["blok_iii"][
        "rencana_jadwal_kegiatan"
    ] = canonicalize_legacy_schedule(
        form,
        "legacy_flat_v1",
    )


    canonical["blok_iii"][
        "variabel_yang_dikumpulkan"
    ] = canonicalize_variables(
        form.get("Variabel")
    )


    canonical["blok_iv"][
        "kegiatan_ini_dilakukan"
    ] = normalize_label(
        extract_option_value(
            form.get(
                "Kegiatan_Ini_Dilakukan"
            )
        )
    )


    canonical["blok_iv"][
        "frekuensi_penyelenggara"
    ] = normalize_label(
        extract_option_value(
            form.get(
                "Frekuensi_Penyelenggaraan_Kegiatan"
            )
        )
    )


    canonical["blok_iv"][
        "tipe_pengumpulan_data"
    ] = normalize_label(
        extract_option_value(
            form.get("Jenis_data")
        )
    )


    canonical["blok_iv"][
        "cakupan_wilayah_pengumpulan_data"
    ] = normalize_label(
        extract_option_value(
            form.get(
                "Cakupan_Wilayah_Data"
            )
        )
    )


    canonical["blok_iv"][
        "wilayah_pengumpulan_data"
    ] = (
        form.get("Wilayah_Data")
        or []
    )


    canonical["blok_iv"][
        "metode_pengumpulan_data"
    ] = extract_option_value(
        form.get(
            "Metode_Pengumpulan_Data"
        )
    )


    canonical["blok_iv"][
        "metode_pengumpulan_data_lainnya"
    ] = form.get(
        "Metode_Pengumpulan_Data_Lainnya"
    )


    canonical["blok_vi"][
        "petugas_pengumpulan_data"
    ] = extract_option_value(
        form.get(
            "Petugas_Pengumpulan_Data"
        )
    )


    canonical["blok_vi"][
        "persyaratan_pendidikan_terendah"
    ] = normalize_label(
        extract_option_value(
            form.get(
                "Persyaratan_pendidikan_terendah_petugas_pengumpulan_data"
            )
        )
    )


    canonical["blok_vi"][
        "jumlah_supervisor"
    ] = form.get(
        "Supervisor_Penyelia_Pengawas"
    )


    canonical["blok_vi"][
        "jumlah_enumerator"
    ] = form.get(
        "Enumerator_Kompilator_Pengumpuldata"
    )


    canonical["blok_vi"][
        "apakah_melakukan_pelatihan"
    ] = normalize_yes_no(
        form.get(
            "Apakah_Melakukan_Pelatihan_Petugas_Pengumpulandata"
        )
    )


    canonical["blok_vii"][
        "tahapan_pengolahan_data"
    ] = {
        "editing": normalize_yes_no(
            form.get("Penyuntingan")
        ),

        "coding": normalize_yes_no(
            form.get("Penyandian")
        ),

        "data_entry": normalize_yes_no(
            form.get("Inputdata")
        ),

        "validasi": normalize_yes_no(
            form.get("Penyahihan")
        ),
    }


    canonical["blok_vii"][
        "metode_analisis"
    ] = form.get(
        "Metode_Analisis"
    )


    canonical["blok_vii"][
        "unit_analisis"
    ] = form.get(
        "Unit_Analisis"
    )


    canonical["blok_vii"][
        "tingkat_penyajian_hasil_analisis"
    ] = extract_option_value(
        form.get(
            "Tingkat_Penyajian_Data"
        )
    )


    canonical["blok_viii"][
        "ketersediaan_produk_tercetak"
    ] = normalize_yes_no(
        form.get(
            "Publikasi_Tercetak"
        )
    )


    canonical["blok_viii"][
        "ketersediaan_produk_digital"
    ] = normalize_yes_no(
        form.get(
            "Publikasi_Elektronik"
        )
    )


    canonical["blok_viii"][
        "waktu_ketersediaan_hasil"
    ] = form.get(
        "Rencana_Penerbitan_Publikasi_Untuk_Umum"
    )


    return canonical


# ============================================================
# 9. LEGACY V2 CANONICALIZER
# ============================================================

def canonicalize_legacy_v2(
    form: dict[str, Any],
) -> dict[str, Any]:
    """
    Convert legacy flat schema v2 ke canonical schema.
    """

    canonical = (
        create_empty_canonical_form(
            "legacy_flat_v2"
        )
    )


    canonical["metadata"].update(
        {
            "nomor_rekomendasi": (
                form.get(
                    "nomor_rekomendasi"
                )
            ),

            "jenis_kegiatan": (
                form.get(
                    "jenis_kegiatan"
                )
            ),

            "judul": (
                form.get("judul")
            ),
        }
    )


    canonical["blok_i"][
        "instansi_penyelenggara"
    ] = form.get(
        "Instansi_Pemerintah_Penyelenggara"
    )


    canonical["blok_i"][
        "alamat_instansi_penyelenggara"
    ] = {
        "alamat": (
            form.get(
                "Alamat_Lengkap_Instansi_Penyelenggara"
            )
        ),
        "telepon": (
            form.get("Telepon")
        ),
        "email": (
            form.get("E-mail")
        ),
        "faksimile": (
            form.get("Fax")
        ),
    }


    canonical["blok_ii"][
        "penanggung_jawab_teknis"
    ] = {
        "nama": (
            form.get(
                "Nama_Manajer_Survei"
            )
        ),
        "jabatan": (
            form.get(
                "Jabatan_Manajer_Survei"
            )
        ),
        "alamat": (
            form.get(
                "Alamat_Manajer_Survei"
            )
        ),
        "telepon": (
            form.get(
                "Telepon_Manajer_Survei"
            )
        ),
        "email": (
            form.get(
                "E-mail_Manajer_Survei"
            )
        ),
        "faksimile": (
            form.get(
                "Fax_Manajer_Survei"
            )
        ),
    }


    canonical["blok_iii"][
        "tujuan_kegiatan"
    ] = form.get(
        "Tujuan_Survei"
    )


    canonical["blok_iii"][
        "rencana_jadwal_kegiatan"
    ] = canonicalize_legacy_schedule(
        form,
        "legacy_flat_v2",
    )


    canonical["blok_iii"][
        "variabel_yang_dikumpulkan"
    ] = canonicalize_variables(
        form.get(
            "Peubah_yang_dikumpulkan"
        )
    )


    canonical["blok_iv"][
        "kegiatan_ini_dilakukan"
    ] = normalize_label(
        form.get(
            "Survei_ini_dilakukan"
        )
    )


    canonical["blok_iv"][
        "frekuensi_penyelenggara"
    ] = normalize_label(
        form.get(
            "Jika_Berulang_Frekuensi_Penyelenggaraan"
        )
    )


    canonical["blok_iv"][
        "tipe_pengumpulan_data"
    ] = normalize_label(
        form.get(
            "Tipe_Pengumpulan_Data"
        )
    )


    canonical["blok_iv"][
        "cakupan_wilayah_pengumpulan_data"
    ] = normalize_label(
        form.get(
            "Survei_dilakukan_di"
        )
    )


    canonical["blok_iv"][
        "wilayah_pengumpulan_data"
    ] = (
        form.get(
            "Wilayah_Data_New"
        )
        or form.get(
            "wilayah"
        )
        or []
    )


    canonical["blok_iv"][
        "metode_pengumpulan_data"
    ] = form.get(
        "Metode_Pengumpulan_Data"
    )


    canonical["blok_iv"][
        "metode_pengumpulan_data_lainnya"
    ] = form.get(
        "Metode_Pengumpulan_Data_Lainnya"
    )


    canonical["blok_v"].update(
        {
            "cara_pengumpulan_data": (
                normalize_label(
                    form.get(
                        "Cara_Pengumpulan_Data"
                    )
                )
            ),

            "metode_penelitian": (
                normalize_label(
                    form.get(
                        "Metode_Penelitian"
                    )
                )
            ),

            "metode_sampel_non_probabilitas": (
                form.get(
                    "Metode_untuk_Sampel_Non_Probabilitas"
                )
            ),

            "jenis_rancangan_sampel": (
                form.get(
                    "Jenis_Rancangan_Sampel"
                )
            ),

            "rancangan_sampel": (
                form.get(
                    "Jelaskan_Rancangannya"
                )
            ),

            "kerangka_sampel": (
                form.get(
                    "Kerangka_Sampel"
                )
            ),

            "metode_pemilihan_sampel": (
                form.get(
                    "Metode_pemilihan_sampel"
                )
            ),

            "fraksi_sampel": (
                form.get(
                    "Keseluruhan_fraksi_sampel"
                )
            ),

            "unit_sampel": (
                form.get(
                    "Unit_sampel"
                )
            ),

            "perkiraan_sampling_error": (
                form.get(
                    "Perkiraan_sampling_error"
                )
            ),

            "responden": (
                form.get("Responden")
            ),
        }
    )


    uji_coba = form.get(
        "Apakah_melakukan_Uji_Coba"
    )

    pelatihan = form.get(
        "Apakah_melakukan_pelatihan_petugas"
    )


    canonical["blok_vi"].update(
        {
            "apakah_melakukan_uji_coba": (
                normalize_yes_no(
                    uji_coba
                )
            ),

            "penjelasan_uji_coba": (
                extract_explanation(
                    uji_coba
                )
            ),

            "petugas_pengumpulan_data": (
                form.get(
                    "Petugas_Pengumpul_Data"
                )
            ),

            "persyaratan_pendidikan_terendah": (
                form.get(
                    "Persyaratan_pendidikan_terendah_petugas_pengumpul_data"
                )
            ),

            "jumlah_supervisor": (
                form.get(
                    "Supervisi_Penyelia_Pengawas"
                )
            ),

            "jumlah_enumerator": (
                form.get(
                    "PengumpulData_Enumerator"
                )
            ),

            "apakah_melakukan_pelatihan": (
                normalize_yes_no(
                    pelatihan
                )
            ),

            "penjelasan_pelatihan": (
                extract_explanation(
                    pelatihan
                )
            ),
        }
    )


    canonical["blok_vii"][
        "tahapan_pengolahan_data"
    ] = {
        "editing": normalize_yes_no(
            form.get("Penyuntingan")
        ),

        "coding": normalize_yes_no(
            form.get("Penyandian")
        ),

        "data_entry": None,

        "validasi": normalize_yes_no(
            form.get("Penyahihan")
        ),
    }


    canonical["blok_vii"][
        "metode_analisis"
    ] = form.get(
        "Metode_analisis_hasil_survei"
    )


    canonical["blok_vii"][
        "unit_analisis"
    ] = form.get(
        "Unit_sampel"
    )


    canonical["blok_vii"][
        "tingkat_penyajian_hasil_analisis"
    ] = form.get(
        "Tingkat_estimasi_yang_diharapkan"
    )


    canonical["blok_viii"].update(
        {
            "ketersediaan_produk_tercetak": (
                normalize_yes_no(
                    form.get(
                        "Publikasi_dalam_Media_Cetak"
                    )
                )
            ),

            "ketersediaan_produk_digital": (
                normalize_yes_no(
                    form.get(
                        "Publikasi_dalam_Media_Elektronik"
                    )
                )
            ),

            "ketersediaan_produk_mikrodata": (
                normalize_yes_no(
                    form.get(
                        "Micro_Data"
                    )
                )
            ),

            "ketersediaan_produk_makrodata": (
                normalize_yes_no(
                    form.get(
                        "Macro_Data"
                    )
                )
            ),

            "waktu_ketersediaan_hasil": (
                form.get(
                    "Waktu_ketersediaan_hasil_survei_untuk_umum"
                )
            ),
        }
    )


    return canonical


# ============================================================
# 10. MODERN CANONICALIZER
# ============================================================

def canonicalize_modern(
    form: dict[str, Any],
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    Convert modern nested schema ke canonical schema.
    """

    canonical = (
        create_empty_canonical_form(
            "modern_nested"
        )
    )


    canonical["metadata"].update(
        {
            "nomor_rekomendasi": None,
            "jenis_kegiatan": None,

            "judul": (
                record.get(
                    "nama_kegiatan"
                )
            ),
        }
    )


    blok_i = (
        form.get("blok_i")
        or {}
    )

    blok_ii = (
        form.get("blok_ii")
        or {}
    )

    blok_iii = (
        form.get("blok_iii")
        or {}
    )

    blok_iv = (
        form.get("blok_iv")
        or {}
    )

    blok_v = (
        form.get("blok_v")
        or {}
    )

    blok_vi = (
        form.get("blok_vi")
        or {}
    )

    blok_vii = (
        form.get("blok_vii")
        or {}
    )

    blok_viii = (
        form.get("blok_viii")
        or {}
    )

    blok_ix = (
        form.get("blok_ix")
        or {}
    )


    canonical["blok_i"] = {
        "instansi_penyelenggara": (
            blok_i.get(
                "instansi_penyelenggara"
            )
        ),

        "alamat_instansi_penyelenggara": (
            deepcopy(
                blok_i.get(
                    "alamat_instansi_penyelenggara"
                )
                or {}
            )
        ),
    }


    canonical["blok_ii"] = {
        "unit_penanggung_jawab": (
            deepcopy(
                blok_ii.get(
                    "unit_penanggung_jawab"
                )
                or {}
            )
        ),

        "penanggung_jawab_teknis": (
            deepcopy(
                blok_ii.get(
                    "penanggung_jawab_teknis"
                )
                or {}
            )
        ),
    }


    canonical["blok_iii"] = {
        "latar_belakang_kegiatan": (
            blok_iii.get(
                "latar_belakang_kegiatan"
            )
        ),

        "tujuan_kegiatan": (
            blok_iii.get(
                "tujuan_kegiatan"
            )
        ),

        "rencana_jadwal_kegiatan": (
            deepcopy(
                blok_iii.get(
                    "rencana_jadwal_kegiatan"
                )
                or {}
            )
        ),

        "variabel_yang_dikumpulkan": (
            canonicalize_variables(
                blok_iii.get(
                    "variabel_yang_dikumpulkan"
                )
            )
        ),
    }


    canonical["blok_iv"] = {
        "kegiatan_ini_dilakukan": (
            blok_iv.get(
                "kegiatan_ini_dilakukan"
            )
        ),

        "frekuensi_penyelenggara": (
            blok_iv.get(
                "frekuensi_penyelanggara"
            )
        ),

        "tipe_pengumpulan_data": (
            blok_iv.get(
                "tipe_pengumpulan_data"
            )
        ),

        "cakupan_wilayah_pengumpulan_data": (
            blok_iv.get(
                "cakupan_wilayah_pengumpulan_data"
            )
        ),

        "wilayah_pengumpulan_data": (
            deepcopy(
                blok_iv.get(
                    "sebagian_cakupan_wilayah_pengumpulan_data"
                )
                or []
            )
        ),

        "metode_pengumpulan_data": (
            deepcopy(
                blok_iv.get(
                    "metode_pengumpulan_data"
                )
            )
        ),

        "metode_pengumpulan_data_lainnya": (
            (
                blok_iv.get(
                    "metode_pengumpulan_data"
                )
                or {}
            ).get(
                "metode_pengumpulan_lainnya"
            )
        ),

        "sarana_pengumpulan_data": (
            deepcopy(
                blok_iv.get(
                    "sarana_pengumpulan_data"
                )
            )
        ),
    }


    if isinstance(
        blok_v,
        dict,
    ):
        canonical[
            "blok_v"
        ].update(
            deepcopy(
                blok_v
            )
        )


    quality_control = (
        blok_vi.get(
            "metode_pemeriksaan_kualitas_pengumpulan_data"
        )
        or {}
    )


    canonical["blok_vi"].update(
        {
            "apakah_melakukan_uji_coba": (
                blok_vi.get(
                    "apakah_melakukan_uji_coba"
                )
            ),

            "penjelasan_uji_coba": None,

            "petugas_pengumpulan_data": (
                blok_vi.get(
                    "petugas_pengumpulan_data"
                )
            ),

            "persyaratan_pendidikan_terendah": (
                blok_vi.get(
                    "persyaratan_pendidikan_terendah_petugas_pengumpulan_data"
                )
            ),

            "jumlah_supervisor": (
                blok_vi.get(
                    "jumlah_petugas_supervisor"
                )
            ),

            "jumlah_enumerator": (
                blok_vi.get(
                    "jumlah_petugas_enumerator"
                )
            ),

            "apakah_melakukan_pelatihan": (
                blok_vi.get(
                    "apakah_melakukan_pelatihan_petugas"
                )
            ),

            "penjelasan_pelatihan": None,

            "metode_pemeriksaan_kualitas": (
                deepcopy(
                    quality_control
                )
            ),
        }
    )


    canonical["blok_vii"].update(
        {
            "tahapan_pengolahan_data": (
                deepcopy(
                    blok_vii.get(
                        "tahapan_pengolahan_data"
                    )
                    or {}
                )
            ),

            "metode_analisis": (
                blok_vii.get(
                    "metode_analisis"
                )
            ),

            "unit_analisis": (
                deepcopy(
                    blok_vii.get(
                        "unit_analsis"
                    )
                )
            ),

            "tingkat_penyajian_hasil_analisis": (
                deepcopy(
                    blok_vii.get(
                        "tingkat_penyajian_hasil_analisis"
                    )
                )
            ),
        }
    )


    canonical["blok_viii"].update(
        {
            "ketersediaan_produk_tercetak": (
                blok_viii.get(
                    "ketersediaan_produk_tercetak"
                )
            ),

            "ketersediaan_produk_digital": (
                blok_viii.get(
                    "ketersediaan_produk_digital"
                )
            ),

            "ketersediaan_produk_mikrodata": (
                blok_viii.get(
                    "ketersediaan_produk_mikrodata"
                )
            ),
        }
    )


    canonical["blok_ix"] = {
        "file_berkas_pendukung": (
            deepcopy(
                blok_ix.get(
                    "file_berkas_pendukung"
                )
                or []
            )
        )
    }


    return canonical


# ============================================================
# 11. SCHEMA DISPATCHER
# ============================================================

def canonicalize_by_schema(
    form: dict[str, Any],
    record: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    """
    Pilih canonicalizer berdasarkan schema family.
    """

    family = (
        detect_schema_family(
            form
        )
    )


    if family == "modern_nested":

        return (
            canonicalize_modern(
                form,
                record,
            ),
            family,
        )


    if family == "legacy_flat_v1":

        return (
            canonicalize_legacy_v1(
                form
            ),
            family,
        )


    if family == "legacy_flat_v2":

        return (
            canonicalize_legacy_v2(
                form
            ),
            family,
        )


    raise ValueError(
        "Schema family tidak dikenali: "
        f"{family}"
    )


# ============================================================
# 12. PUBLIC API FUNCTION
# ============================================================

def canonicalize_record(
    raw_record: dict[str, Any],
) -> dict[str, Any]:
    """
    Canonicalize satu raw record ROMANTIK.

    Fungsi ini merupakan entry point utama yang akan
    digunakan FastAPI.

    Parameters
    ----------
    raw_record
        Satu record ROMANTIK dengan field top-level dan `form`.

    Returns
    -------
    dict
        Record canonical.
    """

    if not isinstance(
        raw_record,
        dict,
    ):
        raise TypeError(
            "raw_record harus berupa dictionary."
        )


    parsed_form, parse_status = (
        parse_json_object(
            raw_record.get("form")
        )
    )


    if parsed_form is None:

        raise ValueError(
            "Field `form` tidak dapat diparse. "
            f"parse_status={parse_status}"
        )


    canonical_form, schema_family = (
        canonicalize_by_schema(
            parsed_form,
            raw_record,
        )
    )


    wilayah = (
        raw_record.get(
            "wilayah"
        )
    )


    return {
        "wilayah": wilayah,

        "id_trans": (
            raw_record.get(
                "id_trans"
            )
        ),

        "nama_kegiatan": (
            raw_record.get(
                "nama_kegiatan"
            )
        ),

        "tahun_kegiatan": (
            raw_record.get(
                "tahun_kegiatan"
            )
        ),

        "instansi": (
            raw_record.get(
                "instansi"
            )
        ),

        "status_pengajuan": (
            raw_record.get(
                "status_pengajuan"
            )
        ),

        "status_rekomendasi": (
            raw_record.get(
                "status_rekomendasi"
            )
        ),

        "is_bps_pusat": (
            str(wilayah) == "0000"
            if wilayah is not None
            else False
        ),

        "schema_family": (
            schema_family
        ),

        "form": (
            canonical_form
        ),
    }