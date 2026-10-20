# ============================================================
# ROMANTIK AI API
# RBS — Shared Helper Functions
# ============================================================
#
# Berisi fungsi pembacaan dan normalisasi nilai yang digunakan
# oleh berbagai rule.
#
# Fungsi-fungsi ini tidak mengubah raw evidence.
# ============================================================

from __future__ import annotations

import json
import re
import unicodedata

from typing import Any

from datetime import date, datetime

# ============================================================
# 1. VALUE STATE
# ============================================================

def value_state(
    value: Any,
) -> str:
    """
    Klasifikasikan kondisi nilai tanpa menganggap
    False atau 0 sebagai nilai kosong.

    Returns
    -------
    str
        - null
        - empty_string
        - empty_list
        - empty_object
        - populated
    """

    if value is None:
        return "null"

    if (
        isinstance(value, str)
        and not value.strip()
    ):
        return "empty_string"

    if (
        isinstance(value, list)
        and not value
    ):
        return "empty_list"

    if (
        isinstance(value, dict)
        and not value
    ):
        return "empty_object"

    return "populated"


# ============================================================
# 2. PATH INSPECTION
# ============================================================

def inspect_path(
    record: dict[str, Any],
    path: str,
) -> tuple[str, Any]:
    """
    Telusuri nested dictionary menggunakan dot notation.

    Status:
    - present
    - absent
    - parent_not_object

    `parent_not_object` digunakan ketika penelusuran terhenti
    karena parent bukan dictionary.
    """

    current: Any = record

    for key in path.split("."):

        if not isinstance(current, dict):
            return "parent_not_object", None

        if key not in current:
            return "absent", None

        current = current[key]

    return "present", current


# ============================================================
# 3. LABEL NORMALIZATION
# ============================================================

def normalize_label(
    value: str,
) -> str:
    """
    Normalisasi label untuk proses pencocokan.

    Nilai sumber tidak diubah.
    """

    text = unicodedata.normalize(
        "NFKC",
        value,
    )

    text = (
        text
        .casefold()
        .replace("_", " ")
    )

    return re.sub(
        r"\s+",
        " ",
        text,
    ).strip()


# ============================================================
# 4. READ FIELD
# ============================================================

def read_field(
    record: dict[str, Any],
    path: str,
) -> dict[str, Any]:
    """
    Membaca field sekaligus menyimpan informasi evidence.
    """

    access, value = inspect_path(
        record,
        path,
    )

    return {
        "path": path,

        "state": (
            value_state(value)
            if access == "present"
            else access
        ),

        "raw_value": value,
    }


# ============================================================
# 5. BOOLEAN PARSER
# ============================================================

def parse_boolean(
    value: Any,
) -> dict[str, Any]:
    """
    Membaca representasi boolean secara eksplisit.

    Tidak menggunakan bool(value), karena string "false"
    tidak boleh dianggap True.
    """

    if value_state(value) != "populated":
        return {
            "status": "empty",
            "value": None,
        }


    if isinstance(value, bool):
        return {
            "status": "recognized",
            "value": value,
        }


    if type(value) in (int, float):

        if value == 1:
            return {
                "status": "recognized",
                "value": True,
            }

        if value == 0:
            return {
                "status": "recognized",
                "value": False,
            }

        return {
            "status": "unrecognized",
            "value": None,
        }


    if isinstance(value, str):

        label = normalize_label(
            value
        )

        true_labels = {
            "true",
            "1",
            "ya",
            "yes",
            "y",
            "iya",
            "ada",
        }

        false_labels = {
            "false",
            "0",
            "tidak",
            "no",
            "n",
            "tidak ada",
        }


        if label in true_labels:

            return {
                "status": "recognized",
                "value": True,
            }


        if label in false_labels:

            return {
                "status": "recognized",
                "value": False,
            }


    return {
        "status": "unrecognized",
        "value": None,
    }


# ============================================================
# 6. VALUE SIGNATURE
# ============================================================

def value_signature(
    value: Any,
) -> str:
    """
    Representasi nilai untuk membandingkan beberapa
    alternative field paths.
    """

    comparable = (
        normalize_label(value)
        if isinstance(value, str)
        else value
    )

    return json.dumps(
        {
            "type": type(value).__name__,
            "value": comparable,
        },
        ensure_ascii=False,
        sort_keys=True,
        allow_nan=False,
    )


# ============================================================
# 7. ALTERNATIVE PATH READER
# ============================================================

def read_alternatives(
    record: dict[str, Any],
    paths: tuple[str, ...],
) -> dict[str, Any]:
    """
    Membaca beberapa alternatif lokasi untuk konsep yang sama.

    Status:
    - unavailable
    - selected
    - conflict
    """

    observations = [
        read_field(
            record,
            path,
        )
        for path in paths
    ]


    populated = [
        item
        for item in observations
        if item["state"] == "populated"
    ]


    if not populated:

        return {
            "status": "unavailable",
            "source_path": None,
            "raw_value": None,
            "observations": observations,
        }


    signatures = {
        value_signature(
            item["raw_value"]
        )
        for item in populated
    }


    if len(signatures) > 1:

        return {
            "status": "conflict",
            "source_path": None,
            "raw_value": None,
            "observations": observations,
        }


    selected = populated[0]


    return {
        "status": "selected",
        "source_path": selected["path"],
        "raw_value": selected["raw_value"],
        "observations": observations,
    }

# ============================================================
# 8. ACTIVITY TYPE RESOLVER
# ============================================================

ACTIVITY_PATHS = (
    "form.metadata.jenis_kegiatan",
    "metadata.jenis_kegiatan",
    "jenis_kegiatan",
)


ACTIVITY_LABELS = {
    "survei": "survei",
    "survey": "survei",
    "kompromin": "kompromin",
    "kompilasi": "kompromin",
    "kompilasi produk administrasi": "kompromin",
    "pendataan lengkap": "pendataan_lengkap",
    "sensus": "pendataan_lengkap",
}


def resolve_explicit_activity(
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    Baca jenis kegiatan dari lokasi eksplisit.
    """

    result = read_alternatives(
        record,
        ACTIVITY_PATHS,
    )

    result["normalized_value"] = None

    if result["status"] != "selected":
        return result

    raw_value = result["raw_value"]

    normalized = (
        ACTIVITY_LABELS.get(
            normalize_label(raw_value)
        )
        if isinstance(raw_value, str)
        else None
    )

    result["normalized_value"] = normalized

    result["status"] = (
        "recognized"
        if normalized is not None
        else "unrecognized"
    )

    return result


def resolve_activity(
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    Tentukan jenis kegiatan dari:

    1. Field jenis kegiatan eksplisit.
    2. Key khusus Blok V pada modern_nested.

    Tidak menggunakan judul maupun catatan pemeriksaan.
    """

    explicit = resolve_explicit_activity(
        record
    )

    if explicit["status"] == "recognized":

        return {
            "value": explicit[
                "normalized_value"
            ],
            "basis": "explicit_field",
            "evidence_paths": [
                explicit["source_path"]
            ],
        }

    # Jangan menutupi nilai eksplisit
    # yang konflik atau tidak dikenali.
    if explicit["status"] != "unavailable":

        return {
            "value": None,
            "basis": explicit["status"],
            "evidence_paths": [],
        }

    # Modern nested tidak punya jenis_kegiatan eksplisit.
    # Survei hanya diinferensikan jika key sampling khusus ada.
    if (
        record.get("schema_family")
        == "modern_nested"
    ):

        form = record.get("form")

        block_v = (
            form.get("blok_v")
            if isinstance(form, dict)
            else None
        )

        marker_keys = (
            "metode_pemilihan_sampel_tahap_terakhir",
            "metode_yang_digunakan",
            "kerangka_sampel_tahap_terakhir",
            "fraksi_sampel_keseluruhan",
            "nilai_perkiraan_sampling_error_variabel_utama",
            "unit_observasi",
            "jumlah_responden",
        )

        if isinstance(block_v, dict):

            evidence_paths = [
                f"form.blok_v.{key}"
                for key in marker_keys
                if key in block_v
            ]

            if evidence_paths:

                return {
                    "value": "survei",
                    "basis": (
                        "modern_sampling_block_keys"
                    ),
                    "evidence_paths": (
                        evidence_paths
                    ),
                }

    return {
        "value": None,
        "basis": "insufficient_information",
        "evidence_paths": [],
    }


# ============================================================
# 9. INFERENTIAL ANALYSIS RESOLVER
# ============================================================

INFERENTIAL_METHOD_LABELS = {
    "analisis inferensia",
    "inferensia",
    "analisis inferensial",
    "inferensial",
}


def detect_inferential_analysis(
    value: Any,
) -> bool | None:
    """
    Tentukan apakah analisis inferensia dipilih.

    Returns
    -------
    True
        Inferensia aktif.

    False
        Deskriptif saja atau inferensia eksplisit False.

    None
        Nilai kosong, ambigu, atau tidak dikenali.
    """

    if isinstance(value, str):

        label = normalize_label(
            value
        )

        descriptive_labels = {
            "deskriptif",
            "analisis deskriptif",
        }

        inferential_labels = {
            "inferensia",
            "inferensial",
            "analisis inferensia",
            "analisis inferensial",
            "deskriptif dan inferensia",
            "deskriptif dan inferensial",
            "analisis deskriptif dan analisis inferensia",
            "analisis deskriptif dan analisis inferensial",
            "analisis deskriptif dan inferensia",
            "analisis deskriptif dan inferensial",
        }

        if label in descriptive_labels:
            return False

        if label in inferential_labels:
            return True

        return None


    if isinstance(value, dict):

        inferential_flags = []

        for key, selected in value.items():

            if re.search(
                r"\binferensi(?:a|al)\b",
                normalize_label(
                    str(key)
                ),
            ):

                parsed = parse_boolean(
                    selected
                )

                inferential_flags.append(
                    parsed["value"]
                )

        if not inferential_flags:
            return None

        if any(
            flag is None
            for flag in inferential_flags
        ):
            return None

        if (
            len(
                set(
                    inferential_flags
                )
            )
            > 1
        ):
            return None

        return inferential_flags[0]


    if isinstance(value, list):

        if not value:
            return None

        results = [
            detect_inferential_analysis(
                item
            )
            for item in value
        ]

        if any(
            result is True
            for result in results
        ):
            return True

        if all(
            result is False
            for result in results
        ):
            return False


    return None

# ============================================================
# 10. EDUCATION RESOLVER
# ============================================================

EDUCATION_PATHS = (
    "form.blok_vi.persyaratan_pendidikan_terendah",
    "blok_vi.persyaratan_pendidikan_terendah",
)


def resolve_education_level(
    value: Any,
) -> str | None:
    """
    Kenali jenjang pendidikan.

    Tidak menggunakan kata 'sederajat'
    sebagai indikator jenjang.
    """

    if (
        not isinstance(value, str)
        or not value.strip()
    ):
        return None

    label = normalize_label(
        value
    )

    patterns = {
        "sd": (
            r"\b(?:sd|mi|sekolah dasar)\b"
        ),

        "smp": (
            r"\b(?:smp|mts|sekolah menengah pertama)\b"
        ),

        "sma_smk": (
            r"\b(?:sma|smu|smk|ma|"
            r"sekolah menengah atas|"
            r"sekolah menengah kejuruan)\b"
        ),

        "diploma": (
            r"\b(?:diploma|akademi|d[1-4])\b"
        ),

        "sarjana": (
            r"\b(?:sarjana|s1)\b"
        ),

        "pascasarjana": (
            r"\b(?:magister|doktor|s2|s3)\b"
        ),
    }

    if label in {
        "akademi universitas",
        "-akademi/universitas",
    }:
        return (
            "pendidikan_tinggi_tidak_spesifik"
        )

    matches = [
        level
        for level, pattern
        in patterns.items()
        if re.search(
            pattern,
            label,
        )
    ]

    return (
        matches[0]
        if len(matches) == 1
        else None
    )


# ============================================================
# 11. REGION COVERAGE RESOLVER
# ============================================================

REGION_SCOPE_PATHS = (
    "form.blok_iv.cakupan_wilayah_pengumpulan_data",
    "blok_iv.cakupan_wilayah_pengumpulan_data",
)

REGION_LIST_PATHS = (
    "form.blok_iv.wilayah_pengumpulan_data",
    "blok_iv.wilayah_pengumpulan_data",
)


def resolve_region_coverage(
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    Membaca cakupan dan daftar wilayah pengumpulan data.

    Mendukung:
    - list kode/nama wilayah,
    - list dictionary legacy,
    - string JSON list,
    - penanda kosong eksplisit "kosong".
    """

    coverage = read_field(
        record,
        "form.blok_iv.cakupan_wilayah_pengumpulan_data",
    )

    coverage_labels = {
        "sebagian wilayah indonesia": "partial",
        "seluruh wilayah indonesia": "national",
        "seluruh wilayah di indonesia": "national",
    }

    raw_coverage = coverage["raw_value"]

    coverage_value = (
        coverage_labels.get(
            normalize_label(raw_coverage)
        )
        if isinstance(raw_coverage, str)
        else None
    )

    region_reading = read_alternatives(
        record,
        (
            "form.blok_iv.wilayah_pengumpulan_data",
            "form.blok_iv.sebagian_cakupan_wilayah_pengumpulan_data",
        ),
    )

    result = {
        "coverage": coverage_value,
        "coverage_evidence": coverage,
        "regions": None,
        "regions_status": region_reading["status"],
        "regions_evidence": region_reading,
    }

    if region_reading["status"] == "conflict":
        return result

    if region_reading["status"] == "unavailable":

        states = {
            item["state"]
            for item in region_reading["observations"]
        }

        if "empty_list" in states:
            result.update(
                regions=[],
                regions_status="empty_list",
            )

        return result

    parsed_regions = region_reading["raw_value"]

    if isinstance(parsed_regions, str):

        if normalize_label(parsed_regions) == "kosong":
            result.update(
                regions=[],
                regions_status="empty_marker",
            )
            return result

        try:
            parsed_regions = json.loads(
                parsed_regions
            )
        except json.JSONDecodeError:
            result["regions_status"] = (
                "unrecognized_format"
            )
            return result

    if not isinstance(parsed_regions, list):
        result["regions_status"] = (
            "unrecognized_format"
        )
        return result

    if not parsed_regions:
        result.update(
            regions=[],
            regions_status="empty_list",
        )
        return result

    def has_region_identifier(
        value: Any,
    ) -> bool:

        if isinstance(value, str):
            return (
                bool(value.strip())
                and normalize_label(value)
                not in {"kosong", "-"}
            )

        return (
            type(value) is int
            and value > 0
        )

    def is_supported_region_item(
        item: Any,
    ) -> bool:

        if isinstance(item, dict):

            return any(
                has_region_identifier(
                    item.get(key)
                )
                for key in (
                    "kode_provinsi",
                    "provinsi",
                    "kode_kabkot",
                    "kabkot",
                )
            )

        return has_region_identifier(
            item
        )

    if not all(
        is_supported_region_item(item)
        for item in parsed_regions
    ):
        result["regions_status"] = (
            "unrecognized_items"
        )
        return result

    result.update(
        regions=parsed_regions,
        regions_status="recognized_list",
    )

    return result


# ============================================================
# 12. COLLECTION METHOD RESOLVER
# ============================================================

COLLECTION_METHOD_PATHS = (
    "form.blok_iv.metode_pengumpulan_data",
    "blok_iv.metode_pengumpulan_data",
)


def resolve_collection_methods(
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    Normalize metode pengumpulan data lintas schema.

    Output selalu berupa list label normalized.
    """

    resolved = read_alternatives(
        record,
        COLLECTION_METHOD_PATHS,
    )

    if resolved["status"] != "selected":
        return {
            "status": resolved["status"],
            "methods": [],
            "source_path": resolved.get("source_path"),
            "raw_value": resolved.get("raw_value"),
            "observations": resolved["observations"],
        }

    raw_value = resolved["raw_value"]

    methods: list[str] = []

    if isinstance(raw_value, dict):

        for key, value in raw_value.items():

            parsed = parse_boolean(value)

            if (
                parsed["status"] == "recognized"
                and parsed["value"] is True
            ):
                methods.append(
                    normalize_label(key).replace(" ", "_")
                )

    elif isinstance(raw_value, list):

        methods = [
            normalize_label(str(item)).replace(" ", "_")
            for item in raw_value
            if value_state(item) == "populated"
        ]

    elif isinstance(raw_value, str):

        if value_state(raw_value) == "populated":
            methods = [
                normalize_label(raw_value).replace(" ", "_")
            ]

    else:
        return {
            "status": "unrecognized",
            "methods": [],
            "source_path": resolved["source_path"],
            "raw_value": raw_value,
            "observations": resolved["observations"],
        }

    return {
        "status": "resolved",
        "methods": methods,
        "source_path": resolved["source_path"],
        "raw_value": raw_value,
        "observations": resolved["observations"],
    }


# ============================================================
# 13. COLLECTION FACILITY RESOLVER
# ============================================================

COLLECTION_FACILITY_PATHS = (
    "form.blok_iv.sarana_pengumpulan_data",
    "blok_iv.sarana_pengumpulan_data",
)


def resolve_collection_facilities(
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    Normalize sarana pengumpulan data lintas schema.

    Output selalu berupa list label normalized.
    """

    resolved = read_alternatives(
        record,
        COLLECTION_FACILITY_PATHS,
    )

    if resolved["status"] != "selected":
        return {
            "status": resolved["status"],
            "facilities": [],
            "source_path": resolved.get("source_path"),
            "raw_value": resolved.get("raw_value"),
            "observations": resolved["observations"],
        }

    raw_value = resolved["raw_value"]

    facilities: list[str] = []

    if isinstance(raw_value, dict):

        for key, value in raw_value.items():

            parsed = parse_boolean(value)

            if (
                parsed["status"] == "recognized"
                and parsed["value"] is True
            ):
                facilities.append(
                    normalize_label(key).replace(" ", "_")
                )

    elif isinstance(raw_value, list):

        facilities = [
            normalize_label(str(item)).replace(" ", "_")
            for item in raw_value
            if value_state(item) == "populated"
        ]

    elif isinstance(raw_value, str):

        if value_state(raw_value) == "populated":
            facilities = [
                normalize_label(raw_value).replace(" ", "_")
            ]

    else:
        return {
            "status": "unrecognized",
            "facilities": [],
            "source_path": resolved["source_path"],
            "raw_value": raw_value,
            "observations": resolved["observations"],
        }

    return {
        "status": "resolved",
        "facilities": facilities,
        "source_path": resolved["source_path"],
        "raw_value": raw_value,
        "observations": resolved["observations"],
    }

# ============================================================
# 14. SAMPLING HELPERS
# ============================================================

GROUP_03_PATHS = {
    "sampling_method": (
        "form.blok_v.metode_pemilihan_sampel_tahap_terakhir",
        "form.blok_v.metode_pemilihan_sampel",
    ),

    "method_detail": (
        "form.blok_v.metode_yang_digunakan",
        "form.blok_v.metode_sampel_probabilitas",
        "form.blok_v.metode_probabilitas",
    ),

    "sampling_frame": (
        "form.blok_v.kerangka_sampel_tahap_terakhir",
        "form.blok_v.kerangka_sampel",
    ),

    "sampling_fraction": (
        "form.blok_v.fraksi_sampel_keseluruhan",
        "form.blok_v.fraksi_sampel",
    ),

    "sampling_error": (
        "form.blok_v.nilai_perkiraan_sampling_error_variabel_utama",
        "form.blok_v.perkiraan_sampling_error",
    ),
}


SAMPLING_CATEGORY_ALIASES = {
    # Probability
    "probabilitas": "probability",
    "sampel probabilitas": "probability",
    "probability": "probability",
    "probability sampling": "probability",

    # Non-probability
    "nonprobabilitas": "non_probability",
    "sampel nonprobabilitas": "non_probability",
    "nonprobability": "non_probability",
    "nonprobability sampling": "non_probability",

    # Teknik probability yang ditemukan pada audit
    "simple random sampling": "probability",
    "systematic sampling": "probability",
    "random sampling method": "probability",
    "random sampling": "probability",
    "acak": "probability",
}


def read_sampling_method(
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    Membaca kategori metode sampling.

    Returns
    -------
    dict
        category:
            - "probability"
            - "non_probability"
            - None

        reading:
            Hasil pembacaan field beserta evidence.
    """

    reading = read_alternatives(
        record,
        GROUP_03_PATHS[
            "sampling_method"
        ],
    )

    category = None

    if reading["status"] == "selected":

        raw_value = reading[
            "raw_value"
        ]

        if isinstance(
            raw_value,
            str,
        ):

            label = (
                normalize_label(
                    raw_value
                )
                .strip(" -")
            )

            # Normalisasi:
            # "non probabilitas"
            # "non-probabilitas"
            # menjadi bentuk "nonprobabilitas"
            label = re.sub(
                r"\bnon[\s-]+",
                "non",
                label,
            )

            category = (
                SAMPLING_CATEGORY_ALIASES
                .get(label)
            )

    return {
        "category": category,
        "reading": reading,
    }


def read_required_sampling(
    record: dict[str, Any],
    concept: str,
) -> dict[str, Any]:
    """
    Membaca field yang diwajibkan ketika menggunakan
    probability sampling.

    State:
    - present
    - empty
    - unavailable
    - conflict

    Catatan:
    'present' hanya berarti nilai terisi,
    bukan berarti metodologinya sudah benar.
    """

    if concept not in GROUP_03_PATHS:
        raise ValueError(
            f"Konsep sampling tidak dikenal: {concept}"
        )

    reading = read_alternatives(
        record,
        GROUP_03_PATHS[concept],
    )

    if reading["status"] == "selected":

        state = "present"

    elif reading["status"] == "conflict":

        state = "conflict"

    else:

        states = {
            item["state"]
            for item
            in reading["observations"]
        }

        if states & {
            "empty_string",
            "empty_list",
            "empty_object",
        }:

            state = "empty"

        else:

            state = "unavailable"

    return {
        "state": state,
        "reading": reading,
    }

# ============================================================
# 15. METHOD / FACILITY OPTION HELPERS
# ============================================================

METHOD_ALIASES = {
    "wawancara": "wawancara",
    "pengamatan": "pengamatan",
    "observasi": "pengamatan",
    "mengisi kuesioner sendiri": "swacacah",
    "mengisi kuesioner sendiri (swacacah)": "swacacah",
    "swacacah": "swacacah",
    "pengumpulan data sekunder": "data_sekunder",
    "dokumentasi": "dokumentasi",
    "lainnya": "lainnya",

    # Tambahan hasil audit final
    "wawancara langsung": "wawancara",
    "pengamatan (observasi)": "pengamatan",
    "lainnya (sebutkan)": "lainnya",
}


FACILITY_ALIASES = {
    name: name
    for name in (
        "papi",
        "capi",
        "cati",
        "cawi",
        "mail",
        "lainnya",
    )
}


def selected_option(
    raw: Any,
    targets: set[str],
    aliases: dict[str, str],
) -> bool | None:
    """
    Periksa apakah minimal satu pilihan target dipilih.

    Returns
    -------
    True
        Ada target yang jelas dipilih.

    False
        Target dapat dipastikan tidak dipilih.

    None
        Informasi kosong, konflik,
        atau belum dapat dikenali.
    """

    # --------------------------------------------------------
    # Dictionary
    # --------------------------------------------------------

    if isinstance(raw, dict):

        flags = {
            target: []
            for target in targets
        }

        for key, value in raw.items():

            concept = aliases.get(
                normalize_label(
                    str(key)
                )
            )

            if concept in flags:

                flags[concept].append(
                    parse_boolean(
                        value
                    )["value"]
                )

        resolved = []

        for values in flags.values():

            if (
                not values
                or any(
                    value is None
                    for value in values
                )
                or len(set(values)) > 1
            ):

                resolved.append(
                    None
                )

            else:

                resolved.append(
                    values[0]
                )

        if any(
            value is True
            for value in resolved
        ):
            return True

        if all(
            value is False
            for value in resolved
        ):
            return False

        return None


    # --------------------------------------------------------
    # String
    # --------------------------------------------------------

    if isinstance(raw, str):

        text = (
            normalize_label(raw)
            .strip(" -")
        )

        # Coba sebagai satu label utuh.
        if text in aliases:

            items = [
                text
            ]

        else:

            # Mendukung contoh:
            # "-WAWANCARA -PENGAMATAN"
            items = re.split(
                r"\s+-\s*|[;,\n]+",
                raw.strip(),
            )


    # --------------------------------------------------------
    # List
    # --------------------------------------------------------

    elif isinstance(raw, list):

        items = raw


    else:

        return None


    if not items:

        return None


    selected = set()
    has_unknown = False


    for item in items:

        if not isinstance(
            item,
            str,
        ):

            has_unknown = True
            continue

        label = (
            normalize_label(item)
            .strip(" -")
        )

        concept = aliases.get(
            label
        )

        if concept is None:

            has_unknown = True

        else:

            selected.add(
                concept
            )


    if selected & targets:

        return True


    # "lainnya" bisa berisi metode target
    # pada keterangan bebas, sehingga
    # tidak aman dipastikan False.
    if (
        has_unknown
        or "lainnya" in selected
    ):

        return None


    return False

def sampling_rule_context(
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    Siapkan konteks dan evidence
    untuk rule sampling.
    """

    activity = resolve_activity(
        record
    )

    return {
        "activity": activity,

        "activity_evidence": [
            read_field(
                record,
                path,
            )
            for path in activity[
                "evidence_paths"
            ]
        ],

        "sampling_method": (
            read_sampling_method(
                record
            )
        ),
    }

# ============================================================
# SCHEDULE DATE HELPER
# ============================================================

SCHEDULE_BASE_PATH = (
    "form.blok_iii.rencana_jadwal_kegiatan"
)


def read_schedule_date(
    record: dict,
    stage: str,
    boundary: str,
) -> dict:
    """
    Baca tanggal jadwal dengan format eksplisit
    dan simpan evidence pembacaannya.

    Format yang dikenali:
    - YYYY-MM-DD
    - ISO datetime
    - DD/MM/YYYY
    - DD-MM-YYYY
    """

    path = (
        f"{SCHEDULE_BASE_PATH}."
        f"{stage}.{boundary}"
    )

    reading = read_field(
        record,
        path,
    )

    raw_value = reading[
        "raw_value"
    ]

    parsed_date = None
    parsing_reason = (
        "date_unavailable"
    )


    if (
        reading["state"]
        == "populated"
    ):

        parsing_reason = (
            "date_format_unrecognized"
        )


        if isinstance(
            raw_value,
            str,
        ):

            text = (
                raw_value.strip()
            )


            try:

                parsed_date = (
                    date.fromisoformat(
                        text
                    )
                )

                parsing_reason = (
                    "iso_date"
                )


            except ValueError:

                try:

                    parsed_date = (
                        datetime.fromisoformat(
                            text.replace(
                                "Z",
                                "+00:00",
                            )
                        ).date()
                    )

                    parsing_reason = (
                        "iso_datetime"
                    )


                except ValueError:

                    for fmt in (
                        "%d/%m/%Y",
                        "%d-%m-%Y",
                    ):

                        try:

                            parsed_date = (
                                datetime.strptime(
                                    text,
                                    fmt,
                                ).date()
                            )

                            parsing_reason = (
                                f"explicit_format:{fmt}"
                            )

                            break


                        except ValueError:

                            continue


    return {
        "reading":
            reading,

        "parsed_date": (
            parsed_date.isoformat()
            if parsed_date
            is not None
            else None
        ),

        "parsing_reason":
            parsing_reason,
    }