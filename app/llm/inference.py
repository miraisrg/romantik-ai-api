# ============================================================
# ROMANTIK AI API
# LLM INFERENCE
# ============================================================

from __future__ import annotations

import os
from typing import Any


MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"

CONTEXT_LIMIT = 8192

MAX_NEW_TOKENS = 1024


_model = None
_tokenizer = None


def get_adapter_path() -> str:
    """
    Ambil lokasi adapter fine-tuned dari environment.

    Contoh:
    ROMANTIK_ADAPTER_PATH=D:/model/final_model
    """

    adapter_path = os.getenv(
        "ROMANTIK_ADAPTER_PATH"
    )

    if not adapter_path:
        raise RuntimeError(
            "Environment variable "
            "ROMANTIK_ADAPTER_PATH belum diatur."
        )

    return adapter_path


def is_model_loaded() -> bool:
    """
    Cek apakah model dan tokenizer
    sudah dimuat ke memory.
    """

    return (
        _model is not None
        and _tokenizer is not None
    )


def load_model() -> None:
    """
    Muat tokenizer, base model Qwen2.5-7B-Instruct,
    dan adapter QLoRA ke GPU.

    Fungsi ini hanya dijalankan pada environment
    yang memiliki CUDA, misalnya Google Colab GPU.

    Model hanya dimuat sekali selama service hidup.
    """

    global _model
    global _tokenizer

    if is_model_loaded():
        return


    # ========================================================
    # 1. Import dependency secara lazy
    # ========================================================

    try:
        import torch

        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
        )

        from peft import PeftModel

    except ImportError as exc:

        raise RuntimeError(
            "Dependency inference belum tersedia. "
            "Environment GPU membutuhkan torch, "
            "transformers, peft, accelerate, "
            "dan bitsandbytes."
        ) from exc


    # ========================================================
    # 2. Pastikan GPU tersedia
    # ========================================================

    if not torch.cuda.is_available():

        raise RuntimeError(
            "CUDA GPU tidak tersedia. "
            "Model ROMANTIK 7B dirancang untuk "
            "dijalankan pada environment GPU."
        )


    # ========================================================
    # 3. Adapter path
    # ========================================================

    adapter_path = get_adapter_path()

    adapter_config = os.path.join(
        adapter_path,
        "adapter_config.json",
    )

    if not os.path.isfile(
        adapter_config
    ):

        raise RuntimeError(
            "adapter_config.json tidak ditemukan "
            f"di: {adapter_path}"
        )


    # ========================================================
    # 4. Tokenizer
    # ========================================================

    tokenizer = AutoTokenizer.from_pretrained(
        adapter_path,
        use_fast=True,
    )

    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = (
            tokenizer.eos_token
        )

    tokenizer.padding_side = "left"


    # ========================================================
    # 5. Compute dtype
    # ========================================================

    if torch.cuda.is_bf16_supported():
        compute_dtype = torch.bfloat16
    else:
        compute_dtype = torch.float16


    # ========================================================
    # 6. 4-bit QLoRA quantization
    # ========================================================

    quant_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=compute_dtype,
    )


    # ========================================================
    # 7. Load base model
    # ========================================================

    base_model = (
        AutoModelForCausalLM
        .from_pretrained(
            MODEL_ID,
            quantization_config=quant_config,
            dtype=compute_dtype,
            device_map={"": 0},
            attn_implementation="sdpa",
        )
    )


    # ========================================================
    # 8. Load QLoRA adapter
    # ========================================================

    model = PeftModel.from_pretrained(
        base_model,
        adapter_path,
        is_trainable=False,
    )

    model.eval()

    model.config.use_cache = True

    model.config.pad_token_id = (
        tokenizer.pad_token_id
    )

    model.config.bos_token_id = (
        tokenizer.bos_token_id
    )

    model.config.eos_token_id = (
        tokenizer.eos_token_id
    )


    # ========================================================
    # 9. Store globally
    # ========================================================

    _tokenizer = tokenizer
    _model = model

def generate_review(
    prompt_messages: list[dict[str, str]],
) -> dict[str, Any]:
    """
    Generate catatan pemeriksaan dari prompt messages.

    Tidak melakukan truncation diam-diam.
    Jika input melebihi context limit,
    fungsi mengembalikan status input_too_long.

    Return berisi:
    - status
    - review_html
    - input_tokens
    - generated_tokens
    - output_budget
    - hit_token_limit
    """

    global _model
    global _tokenizer


    # ========================================================
    # 1. Pastikan model tersedia
    # ========================================================

    if not is_model_loaded():
        load_model()


    import torch


    tokenizer = _tokenizer
    model = _model


    # ========================================================
    # 2. Render chat template
    # ========================================================

    rendered_prompt = (
        tokenizer.apply_chat_template(
            prompt_messages,
            tokenize=False,
            add_generation_prompt=True,
        )
    )


    # ========================================================
    # 3. Hitung panjang input
    # ========================================================

    input_ids = tokenizer(
        rendered_prompt,
        add_special_tokens=False,
    )["input_ids"]

    input_tokens = len(
        input_ids
    )


    # ========================================================
    # 4. Hitung output budget
    # ========================================================

    output_budget = max(
        0,
        min(
            MAX_NEW_TOKENS,
            CONTEXT_LIMIT
            - input_tokens,
        ),
    )


    # ========================================================
    # 5. Input terlalu panjang
    # ========================================================

    if output_budget <= 0:

        return {
            "status":
                "input_too_long",

            "review_html":
                "",

            "input_tokens":
                input_tokens,

            "generated_tokens":
                0,

            "output_budget":
                0,

            "hit_token_limit":
                False,
        }


    # ========================================================
    # 6. Tokenize prompt untuk GPU
    # ========================================================

    batch = tokenizer(
        rendered_prompt,
        add_special_tokens=False,
        return_tensors="pt",
    ).to("cuda")


    # ========================================================
    # 7. Generation configuration
    # ========================================================

    eos = (
        model.base_model
        .generation_config
        .eos_token_id
    )

    if eos is None:
        eos = tokenizer.eos_token_id


    eos_ids = set(
        eos
        if isinstance(
            eos,
            list,
        )
        else [eos]
    )


    # ========================================================
    # 8. Generate
    # ========================================================

    with torch.inference_mode():

        output = model.generate(
            **batch,
            max_new_tokens=output_budget,
            do_sample=False,
            num_beams=1,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=eos,
            use_cache=True,
        )


    # ========================================================
    # 9. Ambil hanya token jawaban
    # ========================================================

    generated_token_ids = output[
        0,
        input_tokens:
    ].tolist()


    generated_tokens = len(
        generated_token_ids
    )


    # ========================================================
    # 10. Detect token limit
    # ========================================================

    hit_token_limit = (
        generated_tokens
        >= output_budget
        and not any(
            token_id in eos_ids
            for token_id
            in generated_token_ids
        )
    )


    # ========================================================
    # 11. Decode output
    # ========================================================

    review_html = tokenizer.decode(
        generated_token_ids,
        skip_special_tokens=True,
    ).strip()


    # ========================================================
    # 12. Return result
    # ========================================================

    return {
        "status":
            "generated",

        "review_html":
            review_html,

        "input_tokens":
            input_tokens,

        "generated_tokens":
            generated_tokens,

        "output_budget":
            output_budget,

        "hit_token_limit":
            hit_token_limit,
    }