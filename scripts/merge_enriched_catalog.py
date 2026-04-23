#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps


def load_json(p: Path) -> Any:
    return json.loads(p.read_text(encoding='utf-8'))


def norm(s: str) -> str:
    return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')


AI_EVENT_MAP = {
    'wedding_ceremony': 'casamento',
    'mini_wedding': 'mini_wedding',
    '15th_birthday_party': 'festa_15_anos',
    'birthday_celebration_at_home': 'evento_residencial',
    'corporate_event': 'evento_corporativo',
    'social_event_reception': 'evento_social',
}

AI_INSTALL_MAP = {
    'string_lights_canopy': 'varal_de_luzes',
    'entrance_light_tunnel': 'tunel_entrada',
    'hanging_chandelier_lights': 'lustre',
    'illuminated_ceiling_with_fairy_lights': 'teto_iluminado',
    'illuminated_sign_letters': 'letreiro',
    'filament_bulb_decoration': 'filamento',
    'outdoor_perimeter_string_lights': 'varal_de_luzes',
}

AI_ENV_MAP = {
    'outdoor_garden_event': 'externo',
    'indoor_ballroom_event': 'interno',
    'residential_backyard_event': 'residencial',
    'event_entrance_corridor': 'entrada',
    'dance_floor_area': 'interno',
    'cake_table_setup': 'interno',
}

CATEGORY_FROM_FIELDS = {
    'casamento': 'cerimonia',
    'mini_wedding': 'cerimonia',
    'festa_15_anos': 'quinzeanos',
    'evento_residencial': 'residencial',
    'tunel_entrada': 'tunel',
    'lustre': 'teto',
    'teto_iluminado': 'teto',
    'varal_de_luzes': 'aoarlivre',
}


def pick_top(score_map: dict[str, float], default: str) -> str:
    if not score_map:
        return default
    return max(score_map.items(), key=lambda kv: kv[1])[0]


def merge_scores(*maps: dict[str, float]) -> dict[str, float]:
    out: dict[str, float] = defaultdict(float)
    for m in maps:
        for k, v in m.items():
            out[k] += float(v)
    return dict(out)


def to_map(preds: list[dict[str, Any]], mapping: dict[str, str]) -> dict[str, float]:
    out: dict[str, float] = defaultdict(float)
    for p in preds:
        raw = norm(p.get('label', ''))
        if raw in mapping:
            out[mapping[raw]] += float(p.get('score', 0.0))
    return dict(out)


def usage_for(item: dict[str, Any]) -> str:
    if item.get('duplicate_flag'):
        return 'discard'
    if item.get('low_quality_flag'):
        return 'discard'

    q = float(item.get('quality_score', 0.0))
    event_type = item.get('event_type')
    install = item.get('installation_type')
    env = item.get('environment')

    if q >= 0.78 and event_type in {'casamento', 'mini_wedding'} and env in {'externo', 'interno'}:
        return 'hero'
    if q >= 0.62 and install in {'tunel_entrada', 'lustre', 'teto_iluminado', 'varal_de_luzes'}:
        return 'gallery'
    if q >= 0.5:
        return 'supporting'
    return 'discard'


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset-dir', default='dataset')
    parser.add_argument('--ai-file', default='dataset/processed/ai_results.json')
    args = parser.parse_args()

    dataset_dir = Path(args.dataset_dir)
    base = load_json(dataset_dir / 'catalog_base.json')
    ai_results_list = load_json(Path(args.ai_file)) if Path(args.ai_file).exists() else []

    ai_by_id = {x['id']: x for x in ai_results_list}

    enriched_items: list[dict[str, Any]] = []
    for item in base['items']:
        ai = ai_by_id.get(item['id'], {'ai_description': 'AI analysis unavailable for this image.', 'ai_predictions': {}})

        cap_scores = item.get('caption_scores', {})
        cap_event = cap_scores.get('event', {})
        cap_install = cap_scores.get('installation', {})
        cap_env = cap_scores.get('environment', {})

        ai_event = to_map(ai.get('ai_predictions', {}).get('event', []), AI_EVENT_MAP)
        ai_install = to_map(ai.get('ai_predictions', {}).get('installation', []), AI_INSTALL_MAP)
        ai_env = to_map(ai.get('ai_predictions', {}).get('environment', []), AI_ENV_MAP)

        event_scores = merge_scores(cap_event, ai_event)
        install_scores = merge_scores(cap_install, ai_install)
        env_scores = merge_scores(cap_env, ai_env)

        event_type = pick_top(event_scores, 'evento_social')
        installation_type = pick_top(install_scores, 'decoracao_luminosa')
        environment = pick_top(env_scores, 'indefinido')

        categories = []
        for key in [event_type, installation_type, environment]:
            if key in CATEGORY_FROM_FIELDS:
                categories.append(CATEGORY_FROM_FIELDS[key])
        categories = sorted(set(categories)) or ['portfolio_geral']

        quality = float(item.get('quality_score', 0.0))
        usage = usage_for({**item, 'event_type': event_type, 'installation_type': installation_type, 'environment': environment})

        enriched = {
            'id': item['id'],
            'image_path': item.get('dataset_image_path'),
            'source_image_path': item.get('image_path'),
            'cleaned_caption': item.get('cleaned_caption', ''),
            'ai_description': ai.get('ai_description', 'AI analysis unavailable for this image.'),
            'event_type': event_type,
            'installation_type': installation_type,
            'environment': environment,
            'quality_score': round(quality, 4),
            'usage': usage,
            'duplicate_flag': bool(item.get('duplicate_flag')),
            'low_quality_flag': bool(item.get('low_quality_flag')),
            'categories': categories,
            'orientation': item.get('orientation'),
            'width': item.get('width'),
            'height': item.get('height'),
            'ai_predictions': ai.get('ai_predictions', {}),
            'caption_scores': cap_scores,
        }
        enriched_items.append(enriched)

    out = {
        'summary': {
            'total_items': len(enriched_items),
            'clean_items': sum(1 for x in enriched_items if x['usage'] != 'discard' and not x['duplicate_flag'] and not x['low_quality_flag']),
            'discarded_items': sum(1 for x in enriched_items if x['usage'] == 'discard'),
        },
        'items': enriched_items,
    }

    (dataset_dir / 'catalog_enriched.json').write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')
    (dataset_dir / 'catalog.json').write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')

    # frontend payload
    clean = [x for x in enriched_items if x['usage'] != 'discard' and not x['duplicate_flag'] and not x['low_quality_flag']]
    clean.sort(key=lambda x: x['quality_score'], reverse=True)

    hero = [x for x in clean if x['usage'] == 'hero'][:3]
    if len(hero) < 3:
        hero = clean[:3]

    showcase = [x for x in clean if x['installation_type'] in {'tunel_entrada', 'lustre', 'teto_iluminado', 'varal_de_luzes'}][:6]

    def title_for(x: dict[str, Any]) -> str:
        mapping = {
            'casamento': 'Casamento',
            'mini_wedding': 'Mini wedding',
            'festa_15_anos': '15 anos',
            'evento_residencial': 'Evento em casa',
            'tunel_entrada': 'Túnel de entrada',
            'varal_de_luzes': 'Varal de luzes',
            'lustre': 'Lustre de luz',
            'teto_iluminado': 'Teto iluminado',
            'letreiro': 'Letreiro iluminado',
            'filamento': 'Lâmpadas de filamento',
        }
        return mapping.get(x['installation_type'], mapping.get(x['event_type'], 'Projeto de iluminação'))

    subtitle_for = {
        'varal_de_luzes': 'Composição de varal para cerimônia e recepção',
        'tunel_entrada': 'Entrada cênica com condução visual',
        'lustre': 'Ponto de destaque para pista ou mesa principal',
        'teto_iluminado': 'Cobertura luminosa para atmosfera imersiva',
        'letreiro': 'Assinatura visual para momentos de foto',
        'filamento': 'Luz quente com estética retrô',
        'decoracao_luminosa': 'Projeto de iluminação decorativa',
    }

    gallery = []
    target_order = ['cerimonia', 'aoarlivre', 'teto', 'tunel', 'residencial', 'quinzeanos', 'portfolio_geral']
    used = set()
    for cat in target_order:
        cat_items = [x for x in clean if cat in x['categories']]
        for c in cat_items[:12]:
            if c['id'] in used:
                continue
            used.add(c['id'])
            gallery.append(c)
            if len(gallery) >= 48:
                break
        if len(gallery) >= 48:
            break

    services = {}
    for key in ['varal_de_luzes', 'tunel_entrada', 'lustre', 'teto_iluminado']:
        cand = next((x for x in clean if x['installation_type'] == key), None)
        if cand:
            services[key] = cand

    site_img_dir = Path('assets/images/site')
    if site_img_dir.exists():
        import shutil
        shutil.rmtree(site_img_dir)
    site_img_dir.mkdir(parents=True, exist_ok=True)

    def export_web_image(x: dict[str, Any], prefix: str, max_side: int) -> str:
        src = Path(x['source_image_path'])
        safe = f"{prefix}-{x['id']}.webp"
        dst = site_img_dir / safe
        with Image.open(src) as im:
            im = ImageOps.exif_transpose(im).convert('RGB')
            im.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
            im.save(dst, format='WEBP', quality=84, method=6)
        return f"./assets/images/site/{safe}"

    cache = {}
    def rel_src(x: dict[str, Any], prefix: str, max_side: int = 1500) -> str:
        key = (x['id'], prefix, max_side)
        if key not in cache:
            cache[key] = export_web_image(x, prefix, max_side)
        return cache[key]

    frontend = {
        'hero': [
            {
                'id': x['id'], 'src': rel_src(x, f"hero-{i+1}", 1900), 'title': title_for(x),
                'subtitle': subtitle_for.get(x['installation_type'], 'Projeto de iluminação decorativa'),
                'categories': x['categories'], 'event_type': x['event_type'],
                'installation_type': x['installation_type'], 'environment': x['environment'],
                'quality_score': x['quality_score'], 'ai_description': x['ai_description']
            }
            for i, x in enumerate(hero)
        ],
        'showcase': [
            {
                'id': x['id'], 'src': rel_src(x, f"showcase-{i+1}", 1600), 'title': title_for(x),
                'subtitle': subtitle_for.get(x['installation_type'], 'Projeto de iluminação decorativa'),
                'categories': x['categories'], 'event_type': x['event_type'],
                'installation_type': x['installation_type'], 'environment': x['environment'],
                'quality_score': x['quality_score'], 'ai_description': x['ai_description']
            }
            for i, x in enumerate(showcase)
        ],
        'gallery': [
            {
                'id': x['id'], 'src': rel_src(x, f"gallery-{i+1}", 1500), 'title': title_for(x),
                'subtitle': subtitle_for.get(x['installation_type'], 'Projeto de iluminação decorativa'),
                'categories': x['categories'], 'event_type': x['event_type'],
                'installation_type': x['installation_type'], 'environment': x['environment'],
                'quality_score': x['quality_score'], 'ai_description': x['ai_description']
            }
            for i, x in enumerate(gallery)
        ],
        'services': {
            k: {
                'id': v['id'], 'src': rel_src(v, f"service-{k}", 1600), 'title': title_for(v),
                'subtitle': subtitle_for.get(v['installation_type'], 'Projeto de iluminação decorativa'),
                'event_type': v['event_type'], 'installation_type': v['installation_type'], 'environment': v['environment'],
                'quality_score': v['quality_score'], 'ai_description': v['ai_description']
            }
            for k, v in services.items()
        }
    }
    assets_data = Path('assets/data')
    assets_data.mkdir(parents=True, exist_ok=True)
    (assets_data / 'frontend-content.json').write_text(json.dumps(frontend, indent=2, ensure_ascii=False), encoding='utf-8')

    print(json.dumps(out['summary'], indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
