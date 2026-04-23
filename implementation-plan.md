# Plano de Implementação — Landing Page Decora Varal de Luzes

## 1) Arquitetura da landing
- Stack: HTML + CSS + JS puro (sem build).
- Estrutura de arquivos:
  - `index.html`
  - `styles.css`
  - `script.js`
  - `assets/images/` (imagens otimizadas em WebP a partir do acervo real)
- Motivo da escolha:
  - hospedagem simples (Netlify, Vercel estático, GitHub Pages, servidor comum);
  - performance e manutenção fáceis;
  - controle visual total para uma estética autoral (sem aparência de template).

## 2) Mapa de seções
1. Hero imersivo
2. Proposta de valor
3. Transformação de ambientes (before/after interativo)
4. Serviços (baseados em legendas reais)
5. Storytelling do processo
6. Galeria premium por categorias
7. Atendimento regional (Goiânia e cidades próximas)
8. CTA WhatsApp
9. Rodapé refinado

## 3) Recursos interativos escolhidos
- Hero com slideshow cinematográfico e transição suave.
- Animações de entrada por scroll (IntersectionObserver) com timing elegante.
- Componente before/after com slider para mostrar transformação real.
- Galeria filtrável por categoria:
  - Casamentos ao ar livre
  - Túnel e MicroLED
  - Teto e Lustres
  - Passarela e Cerimônia
- Showcase imersivo (lightbox) para ampliar fotos com navegação.
- Microinterações premium:
  - hover com brilho sutil;
  - botões com feedback tátil leve;
  - indicadores de estado nos filtros.

## 4) Direção visual baseada na análise dos posts
- Base escura/azul-noturna para valorizar brilho âmbar.
- Dourado quente/champanhe como cor de destaque da iluminação.
- Verde profundo como referência aos cenários externos da marca.
- Tipografia elegante e expressiva (serif para títulos + sans para leitura).
- Elementos gráficos com curvas e gradientes de luz para reforçar sensação de encantamento.
- Fotos reais do acervo como protagonistas em todos os blocos-chave.

## 5) Conteúdo textual (tom de voz)
- Linguagem emocional e sofisticada.
- Ênfase em:
  - transformação;
  - sonho/encanto;
  - responsabilidade na entrega;
  - atendimento regional.
- CTA comercial direto, porém com acabamento premium.

## 6) Estratégia de performance
- Conversão das imagens selecionadas para WebP.
- `loading="lazy"` fora do hero.
- Dimensões e recortes planejados para evitar layout shift.
- CSS/JS enxutos sem dependências pesadas.

## 7) Ordem de execução
1. Curadoria final e otimização das imagens.
2. Estrutura HTML semântica completa.
3. Construção visual em CSS (tema, responsividade, animações).
4. Implementação de interações JS (filtros, lightbox, before/after, reveals).
5. Revisão responsiva (mobile/tablet/desktop).
6. Documentação final no `README.md`.
