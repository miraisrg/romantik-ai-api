# ============================================================
# ROMANTIK AI API
# RBS — Rule Group 05
# ============================================================
#
# Rules:
# - R-VII-01
# - R-VIII-01
# ============================================================

from __future__ import annotations

from typing import Any

from app.rbs.base import build_rule_result

from app.rbs.helpers import (
    parse_boolean,
    read_field,
)


# ============================================================
# RULE VERSIONS
# ============================================================

R_VII_01_VERSION = "rebuild_r_vii_01_v01"


# ============================================================
# R-VII-01
# ============================================================

PROCESSING_STAGE_PATHS = {
    stage: (
        f"form.blok_vii."
        f"tahapan_pengolahan_data.{stage}"
    )
    for stage in (
        "editing",
        "coding",
        "data_entry",
        "validasi",
    )
}


def rule_r_vii_01(
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    Minimal satu tahapan pengolahan
    data harus dipilih.

    Decision policy:
    - any True -> pass
    - all False -> violation
    - no True + unknown -> not_evaluable
    """

    stage_evidence = {}

    selected_stages = []
    false_stages = []
    unknown_stages = []


    for stage, path in (
        PROCESSING_STAGE_PATHS.items()
    ):

        reading = read_field(
            record,
            path,
        )

        parsed_value = None


        if (
            reading["state"]
            == "populated"
        ):

            parsed = parse_boolean(
                reading["raw_value"]
            )

            if (
                parsed["status"]
                == "recognized"
            ):
                parsed_value = (
                    parsed["value"]
                )


        stage_evidence[stage] = {
            "reading": reading,
            "parsed_value": parsed_value,
        }


        if parsed_value is True:

            selected_stages.append(
                stage
            )

        elif parsed_value is False:

            false_stages.append(
                stage
            )

        else:

            unknown_stages.append(
                stage
            )


    evidence = {
        "stages": stage_evidence,

        "selected_stages":
            selected_stages,

        "false_stages":
            false_stages,

        "unknown_stages":
            unknown_stages,
    }


    message = None


    # Satu True sudah cukup memenuhi aturan.
    if selected_stages:

        status = "pass"

        reason = (
            "at_least_one_processing_"
            "stage_selected"
        )


    # Tidak ada True, tetapi masih ada
    # field yang tidak dapat dinilai.
    elif unknown_stages:

        status = "not_evaluable"

        reason = (
            "processing_stage_selection_"
            "unavailable_or_unrecognized"
        )


    # Semua field berhasil dibaca
    # dan semuanya False.
    else:

        status = "violation"

        reason = (
            "all_processing_stages_"
            "not_selected"
        )

        message = (
            "Tidak ada tahapan pengolahan data "
            "yang dipilih. Minimal satu tahapan "
            "editing, coding, data entry, atau "
            "validasi harus dilakukan sesuai "
            "rancangan kegiatan."
        )


    result = build_rule_result(
        rule_id="R-VII-01",
        status=status,
        applicability="applicable",
        reason=reason,
        evidence=evidence,
        message=message,
    )

    result["rule_version"] = (
        R_VII_01_VERSION
    )

    return result

R_VIII_01_VERSION = "rebuild_r_viii_01_v01"


PRODUCT_FIELD_PATHS = {
    "digital":
        "form.blok_viii.ketersediaan_produk_digital",

    "mikrodata":
        "form.blok_viii.ketersediaan_produk_mikrodata",

    "tercetak":
        "form.blok_viii.ketersediaan_produk_tercetak",
}

def rule_r_viii_01(
    record: dict[str, Any],
) -> dict[str, Any]:
    """
    Periksa minimal satu produk
    tersedia untuk umum.

    Decision policy:
    - any True -> pass
    - all False -> violation
    - no True + unknown -> not_evaluable
    """

    product_evidence = {}

    available_products = []
    unavailable_products = []
    unknown_products = []


    for product, path in (
        PRODUCT_FIELD_PATHS.items()
    ):

        reading = read_field(
            record,
            path,
        )

        parsed_value = None


        if (
            reading["state"]
            == "populated"
        ):

            parsed = parse_boolean(
                reading["raw_value"]
            )

            if (
                parsed["status"]
                == "recognized"
            ):
                parsed_value = (
                    parsed["value"]
                )


        product_evidence[
            product
        ] = {
            "reading": reading,
            "parsed_value": parsed_value,
        }


        if parsed_value is True:

            available_products.append(
                product
            )

        elif parsed_value is False:

            unavailable_products.append(
                product
            )

        else:

            unknown_products.append(
                product
            )


    evidence = {
        "products":
            product_evidence,

        "available_products":
            available_products,

        "explicitly_unavailable_products":
            unavailable_products,

        "unknown_products":
            unknown_products,
    }


    message = None


    if available_products:

        status = "pass"

        reason = (
            "at_least_one_product_available"
        )


    elif unknown_products:

        status = "not_evaluable"

        reason = (
            "product_availability_"
            "unavailable_or_unrecognized"
        )


    else:

        status = "violation"

        reason = (
            "all_products_"
            "explicitly_unavailable"
        )

        message = (
            "Seluruh pilihan ketersediaan "
            "produk bernilai tidak. Minimal "
            "satu produk hasil kegiatan harus "
            "tersedia untuk umum sesuai "
            "ketentuan R-VIII-01."
        )


    result = build_rule_result(
        rule_id="R-VIII-01",
        status=status,
        applicability="applicable",
        reason=reason,
        evidence=evidence,
        message=message,
    )

    result["rule_version"] = (
        R_VIII_01_VERSION
    )

    return result

# ============================================================
# GROUP REGISTRY
# ============================================================

GROUP_05_RULES = {
    "R-VII-01": rule_r_vii_01,
    "R-VIII-01": rule_r_viii_01,
}