# Decora Landing

Landing page da Decora Varal de Luzes, com curadoria visual orientada por dataset local e foco em conversão.

## Visão geral

O projeto combina duas frentes:

- frontend estático (HTML, CSS e JS puro)
- pipeline local para preparar conteúdo visual e gerar payload do frontend

Principais recursos da landing:

- hero com slideshow
- seção de serviços com fundos reais
- showcase de destaques
- galeria com filtros, paginação e lightbox
- CTA para WhatsApp e Instagram
- layout responsivo com refinamento mobile

## Estrutura do projeto

- `index.html`: estrutura da landing
- `styles.css`: estilos globais e responsividade
- `script.js`: comportamento de UI, carregamento de dados e galeria
- `assets/data/frontend-content.json`: conteúdo consumido pelo frontend
- `assets/images/site/`: imagens otimizadas para a landing
- `scripts/`: scripts do pipeline local

## Pipeline local de conteúdo

Scripts:

- `scripts/build_dataset_catalog.py`
  - varredura, limpeza de legendas, deduplicação e qualidade
- `scripts/local_ai_vision.mjs`
  - classificação visual local com `@xenova/transformers`
- `scripts/merge_enriched_catalog.py`
  - fusão legenda + IA e geração do payload final do frontend

Formato esperado de diretórios do dataset (fora do escopo da publicação da landing):

- `dataset/raw/`
- `dataset/processed/`
- `dataset/images_clean/`
- `dataset/duplicates/`
- `dataset/low_quality/`
- `dataset/catalog.json`
- `dataset/catalog_enriched.json`

## Como rodar localmente

Suba um servidor estático na raiz do projeto:

```bash
python3 -m http.server 8000
```

Abra no navegador:

- `http://localhost:8000`

## Como regenerar o conteúdo (pipeline)

1. Ambiente Python

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install pillow numpy imagehash
```

2. Gerar base do dataset

```bash
python scripts/build_dataset_catalog.py --root . --dataset-dir dataset
```

3. Instalar dependência de IA local

```bash
npm install @xenova/transformers
```

4. Rodar análise visual local

```bash
node scripts/local_ai_vision.mjs --input=dataset/processed/ai_jobs.json --output=dataset/processed/ai_results.json
```

5. Gerar catálogo enriquecido e payload do frontend

```bash
python scripts/merge_enriched_catalog.py --dataset-dir dataset --ai-file dataset/processed/ai_results.json
```

## Melhorias recentes

- transições entre seções ajustadas para remover rastros visuais
- refinamento de layout mobile (espaçamento, composição e legibilidade)
- otimizações de runtime no JS (scroll com `requestAnimationFrame`, listeners passivos e observers mais eficientes)
- preload/priorização da imagem principal e `defer` no script
- favicon configurado com o logo da marca

## Auditoria de performance

Relatórios Lighthouse (local):

- `lighthouse-mobile.json`
- `lighthouse-desktop.json`

Resultado da última rodada:

- mobile: Performance 71, Accessibility 100, Best Practices 96, SEO 100
- desktop: Performance 94, Accessibility 100, Best Practices 96, SEO 100

Principais gargalos atuais no mobile:

- recursos bloqueantes (Google Fonts + CSS principal)
- imagens acima do necessário para o viewport móvel

## Publicação

Por ser frontend estático, pode ser publicado em:

- GitHub Pages
- Netlify
- Vercel (modo estático)
- qualquer servidor de arquivos estáticos
