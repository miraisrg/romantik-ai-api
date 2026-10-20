# ROMANTIK AI API

API pemeriksaan formulir rekomendasi kegiatan statistik ROMANTIK BPS menggunakan model **Hybrid AI** yang mengintegrasikan **Rule-Based System (RBS)** dan **fine-tuned Large Language Model (LLM)**.

Repositori ini merupakan produk skripsi:

> **Pengembangan Model Hybrid AI Berbasis Fine-Tuned LLM dan Rule-Based System untuk Otomatisasi Pemeriksaan Formulir Kegiatan Statistik (Studi Kasus: ROMANTIK BPS)**
>
> Amir Mumtaz Siregar (222212493), D-IV Komputasi Statistik, Politeknik Statistika STIS
> Dosen pembimbing: Prof. Setia Pramana, S.Si., M.Sc., Ph.D.

> **Catatan:** Sistem ini merupakan *proof of concept* alat bantu pemeriksa, bukan pengganti keputusan pemeriksa.

## Cara Kerja

Setiap formulir yang dikirim ke API diproses melalui *pipeline* berikut:

1. **Canonicalization**: menyeragamkan struktur JSON formulir ROMANTIK.
2. **Rule-Based System**: memeriksa formulir dengan 40 unit aturan dan memberi status `pass`, `violation`, atau `not_evaluable` beserta *evidence*.
3. **Hybrid Interface**: menyusun hasil RBS menjadi konteks terstruktur yang ringkas.
4. **Prompt Construction**: membentuk *prompt* dari formulir dan konteks RBS.
5. **LLM Inference**: Qwen2.5-7B-Instruct dengan adapter QLoRA menghasilkan catatan pemeriksaan.

## Struktur Repositori

```
app/
├── main.py                  # Inisialisasi FastAPI
├── api/routes.py            # Endpoint API
├── schemas/review.py        # Skema request dan response
├── services/review_service.py  # Orkestrasi pipeline
├── preprocessing/canonicalizer.py
├── rbs/
│   ├── engine.py            # Mesin eksekusi aturan
│   ├── base.py, helpers.py
│   ├── hybrid.py            # Penyusunan konteks RBS untuk LLM
│   └── rules/group_01–11.py # Aturan per kelompok
└── llm/
    ├── prompt_builder.py
    └── inference.py         # Pemuatan model dan generasi
data/
├── sample_input/            # Contoh formulir (data anonim)
└── sample_output/
tests/
```

## Kebutuhan

- Python 3.10 atau lebih baru
- Untuk inferensi LLM: GPU CUDA (misalnya Google Colab GPU) dan adapter QLoRA hasil *fine-tuning*

Bobot adapter **tidak** disertakan di repositori ini karena ukurannya besar.

## Instalasi

```bash
git clone https://github.com/miraisrg/romantik-ai-api.git
cd romantik-ai-api

# Dependensi API dan RBS
pip install -r requirements.txt

# Dependensi inferensi LLM (khusus environment GPU)
pip install -r requirements-gpu.txt
```

## Konfigurasi

Atur lokasi folder adapter QLoRA (folder yang berisi `adapter_config.json`):

```bash
# Linux / macOS / Google Colab
export ROMANTIK_ADAPTER_PATH=/path/ke/final_model

# Windows (PowerShell)
$env:ROMANTIK_ADAPTER_PATH="D:/model/final_model"
```

Model dasar `Qwen/Qwen2.5-7B-Instruct` diunduh otomatis dari Hugging Face dan dimuat dalam kuantisasi 4-bit. Model dimuat sekali saat permintaan pertama, sehingga permintaan pertama memerlukan waktu lebih lama.

## Menjalankan API

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Dokumentasi interaktif tersedia di `http://localhost:8000/docs`.

Pada penelitian ini, API dijalankan di Google Colab GPU dan diakses oleh aplikasi web melalui Cloudflare Tunnel.

## Endpoint

| Method | Endpoint | Keterangan |
|---|---|---|
| GET | `/` | Pesan bahwa API berjalan |
| GET | `/health` | Pemeriksaan status layanan |
| POST | `/api/v1/review` | Pemeriksaan satu formulir ROMANTIK |

### Contoh request

```bash
curl -X POST http://localhost:8000/api/v1/review \
  -H "Content-Type: application/json" \
  -d '{"form": { ...JSON formulir ROMANTIK... }}'
```

Contoh isi `form` tersedia di `data/sample_input/`.

### Struktur response

```json
{
  "status": "success",
  "metadata": {
    "id_trans": "...",
    "nama_kegiatan": "...",
    "tahun_kegiatan": 2026,
    "instansi": "..."
  },
  "rbs": {
    "n_findings": 2,
    "n_not_evaluable": 3,
    "findings": [
      {"rule_id": "...", "severity": "...", "message": "...", "evidence": "..."}
    ],
    "not_evaluable": [
      {"rule_id": "...", "status": "not_evaluable", "applicability": "...", "reason": "...", "message": "...", "evidence": "..."}
    ]
  },
  "hybrid_review": "<p>Catatan pemeriksaan Hybrid AI...</p>",
  "processing_time_seconds": 12.345
}
```

## Pengujian

```bash
python -m unittest discover tests
```

Pengujian endpoint memakai *mock* untuk LLM, sehingga dapat dijalankan tanpa GPU.

## Keterbatasan

- Endpoint `/api/v1/review` memerlukan GPU CUDA dan adapter QLoRA. Tanpa keduanya, pemuatan model gagal dan permintaan mengembalikan error.
- Kualitas catatan yang dihasilkan LLM masih perlu dikembangkan sebelum digunakan secara operasional.