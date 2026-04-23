# Decora Varal de Luzes — Landing Premium Orientada por Dados

## Visão geral
Este projeto combina pipeline local de análise de conteúdo + landing page premium para portfólio e conversão.

Melhorias desta versão:
- seção de Instagram reformulada (mais estilosa e claramente clicável)
- galeria com filtros + paginação (não carrega tudo de uma vez)
- títulos e cópias menos técnicas e mais comerciais
- ordem de seções reorganizada para narrativa de conversão
- correção do header no desktop (alinhamento central)
- correção das imagens faltantes em serviços (`lustre` e `teto_iluminado`)
- imagens do frontend convertidas para WebP

## Estrutura de dataset (pipeline local)
O pipeline organiza e enriquece o dataset em:

- `dataset/raw/`
- `dataset/processed/`
- `dataset/images_clean/`
- `dataset/duplicates/`
- `dataset/low_quality/`
- `dataset/catalog.json`
- `dataset/catalog_enriched.json`

## Pipeline local e ferramentas
### Escolha técnica
Para rodar bem no MacBook Pro M1 Pro 16GB sem downloads absurdos:
- Python (heurísticas + qualidade + deduplicação)
- Node.js + `@xenova/transformers`
- modelo local: `Xenova/clip-vit-base-patch32`

Motivo:
- leve/médio, viável em Apple Silicon
- sem modelos de dezenas de GB
- bom equilíbrio entre custo computacional e ganho de classificação

### Scripts
- `scripts/build_dataset_catalog.py`
  - varredura, limpeza de legendas, deduplicação, qualidade
- `scripts/local_ai_vision.mjs`
  - classificação visual local (evento/instalação/ambiente/objetos)
- `scripts/merge_enriched_catalog.py`
  - fusão legenda + IA, geração do catálogo final e payload do frontend
  - exporta imagens otimizadas em **WebP** para `assets/images/site/`

## Como rodar de novo
### 1) Ambiente Python
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install pillow numpy imagehash
```

### 2) Gerar base do dataset
```bash
source .venv/bin/activate
python scripts/build_dataset_catalog.py --root . --dataset-dir dataset
```

### 3) Dependência de IA local
```bash
npm install @xenova/transformers
```

### 4) Rodar análise visual local
```bash
node scripts/local_ai_vision.mjs --input=dataset/processed/ai_jobs.json --output=dataset/processed/ai_results.json
```

### 5) Gerar catálogo enriquecido e frontend
```bash
source .venv/bin/activate
python scripts/merge_enriched_catalog.py --dataset-dir dataset --ai-file dataset/processed/ai_results.json
```

## Integração no frontend
A landing consome:
- `assets/data/frontend-content.json`

A página usa esses dados para renderizar:
- hero dinâmico
- transformação (showcase)
- cards de serviços com fundo real
- galeria filtrável com paginação
- lightbox fullscreen com navegação lateral

## Rodar localmente
Use servidor estático (necessário para `fetch` do JSON):

```bash
python3 -m http.server 8000
```

Abra:
- `http://localhost:8000`

## Publicação
Como é frontend puro:
- GitHub Pages
- Netlify
- Vercel (static)
- qualquer host de arquivos estáticos

## Pasta enxuta para Git
Foi criada uma versão pronta para subir em:
- `project/decora-landing/`

Ela contém apenas o necessário para versionar e publicar a landing sem o dataset bruto gigante.

## Tradeoffs
- classificação local por CLIP é robusta para tags, mas não substitui descrição humana completa
- as regras de fusão (legenda + IA) são determinísticas para facilitar manutenção
- categorias com pouca ocorrência real podem ficar naturalmente menores
# decora-landins-page
