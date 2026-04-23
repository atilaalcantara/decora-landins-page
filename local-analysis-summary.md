# Local Analysis Summary (AI + Cleanup)

## Scope
Dataset analyzed locally from two sources:
- `organized_posts/*/image.* + caption.txt`
- flat export in project root (`YYYY-MM-DD_..._UTC*.jpg` + matching `.txt`)

Total scanned: **2627 images**.

## New dataset structure
Generated:
- `dataset/raw/`
- `dataset/processed/`
- `dataset/images_clean/`
- `dataset/duplicates/`
- `dataset/low_quality/`
- `dataset/catalog.json`
- `dataset/catalog_enriched.json`

## Cleanup results
From `scripts/build_dataset_catalog.py`:
- total items: **2627**
- clean candidates: **1215**
- duplicates moved/flagged: **1370**
- low quality/corrupt: **42**

## Local AI approach used
Model/runtime:
- `@xenova/transformers`
- model: `Xenova/clip-vit-base-patch32`
- task: local zero-shot image classification

Why this fits M1 Pro 16GB:
- no giant 50GB+ multimodal model
- compact CLIP-class model cached locally
- runs on-device with manageable memory
- practical for batch inference over >1k images

Tradeoff:
- CLIP gives strong semantic tags/ranking, but not deep free-form reasoning.
- mitigated by combining AI predictions with cleaned captions.

## AI inference coverage
From `scripts/local_ai_vision.mjs`:
- AI jobs processed: **1215 / 1215**
- output: `dataset/processed/ai_results.json`

Each job includes:
- `ai_description`
- `ai_predictions.event`
- `ai_predictions.installation`
- `ai_predictions.environment`
- `ai_predictions.objects`

## Caption + AI fusion
From `scripts/merge_enriched_catalog.py`, each item now has:
- `image_path`
- `cleaned_caption`
- `ai_description`
- `event_type`
- `installation_type`
- `environment`
- `quality_score`
- `usage`
- `duplicate_flag`

And enriched catalog is saved in:
- `dataset/catalog_enriched.json`

## Post-fusion distribution (clean, non-duplicate, non-low-quality)
- clean usable: **1148**

Event type:
- casamento: 680
- mini_wedding: 180
- evento_social: 171
- evento_residencial: 61
- festa_15_anos: 20
- evento_corporativo: 26

Installation type:
- varal_de_luzes: 664
- teto_iluminado: 261
- lustre: 89
- letreiro: 85
- filamento: 31
- tunel_entrada: 18

Environment:
- interno: 613
- externo: 485
- residencial: 35
- entrada: 15

## Category validation requested
Validated with combined caption + AI:
- **Casamentos**: strongly present
- **Mini weddings**: present with meaningful volume
- **15 anos**: present (smaller, but real)
- **Eventos em casa**: present and consistent

Additional recurring segments:
- teto/lustres
- varal de luzes
- entrada/túnel
- letreiro e filamento

## Frontend dataset generated
`assets/data/frontend-content.json` now contains:
- 3 hero items
- 6 showcase items
- 48 gallery items
- service image slots from enriched data

Web-optimized assets generated in:
- `assets/images/site/`

This removed generic placeholders and improved label specificity across sections.
