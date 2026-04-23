const FRONTEND_DATA_PATH = "./assets/data/frontend-content.json";

if ("scrollRestoration" in history) {
  history.scrollRestoration = "manual";
}
window.addEventListener("load", () => {
  window.scrollTo({ top: 0, left: 0, behavior: "instant" });
});

const topbar = document.querySelector(".topbar");
const heroMedia = document.getElementById("heroMedia");
const heroSlides = Array.from(document.querySelectorAll(".hero-slide"));
const heroEntranceItems = Array.from(
  document.querySelectorAll(".hero-entrance"),
);
const showcaseGrid = document.getElementById("showcaseGrid");
const galleryGrid = document.getElementById("galleryGrid");
const galleryPagination = document.getElementById("galleryPagination");
const gallerySummary = document.getElementById("gallerySummary");
const serviceCards = Array.from(document.querySelectorAll(".service-card"));
const serviceButtons = Array.from(document.querySelectorAll(".service-link"));
const gallerySection = document.getElementById("galeria");

const chips = Array.from(document.querySelectorAll(".chip"));
const prefersReducedMotion = window.matchMedia(
  "(prefers-reduced-motion: reduce)",
).matches;
let galleryData = [];
let heroIndex = 0;
let currentFilter = "all";
let currentPage = 1;
let pageSize = 12;

const lightbox = document.getElementById("lightbox");
const lightboxImage = document.getElementById("lightboxImage");
const lightboxTitle = document.getElementById("lightboxTitle");
const lightboxClose = document.getElementById("lightboxClose");
const lightboxPrev = document.getElementById("lightboxPrev");
const lightboxNext = document.getElementById("lightboxNext");
let activeFilteredIndex = 0;

const titleCase = (value) =>
  value
    .replace(/_/g, " ")
    .split(" ")
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");

const humanTitle = (item) => {
  if (!item) return "Projeto de iluminação";
  if (item.title) return item.title;
  if (item.installation_type) return titleCase(item.installation_type);
  if (item.event_type) return titleCase(item.event_type);
  return "Projeto de iluminação";
};

const humanSubtitle = (item) => {
  if (!item) return "";
  if (item.subtitle) return item.subtitle;
  if (item.ai_description) return item.ai_description;
  return "Projeto de iluminação decorativa";
};

const labelForFilter = (filter) => {
  const labels = {
    all: "todos os estilos",
    cerimonia: "casamentos",
    tunel: "túnel e entrada",
    teto: "teto e lustres",
    aoarlivre: "ao ar livre",
    residencial: "eventos em casa",
    quinzeanos: "15 anos",
  };
  return labels[filter] || "seleção";
};

const getPageSize = () => {
  const width = window.innerWidth;
  if (width <= 760) return 6;
  if (width <= 1160) return 8;
  return 12;
};

const setupHeroEntrance = () => {
  if (prefersReducedMotion) {
    heroEntranceItems.forEach((item) => item.classList.add("visible"));
    return;
  }
  heroEntranceItems.forEach((item, index) => {
    setTimeout(() => item.classList.add("visible"), 140 + index * 120);
  });
};

const activateSlide = (index) => {
  heroSlides.forEach((slide, i) => {
    slide.classList.toggle("is-active", i === index);
  });
};

const startHeroCycle = () => {
  if (heroSlides.length <= 1 || prefersReducedMotion) return;
  setInterval(() => {
    heroIndex = (heroIndex + 1) % heroSlides.length;
    activateSlide(heroIndex);
  }, 5600);
};

const getItemPrimaryFilter = (item) => {
  const categories = item?.categories || [];
  if (categories.includes("cerimonia")) return "cerimonia";
  if (categories.includes("tunel")) return "tunel";
  if (categories.includes("teto")) return "teto";
  if (categories.length) return categories[0];
  return "all";
};

const renderShowcase = (items = []) => {
  if (!showcaseGrid) return;
  showcaseGrid.innerHTML = "";

  const seenInstallations = new Set();
  const curated = [];
  items.forEach((item) => {
    const key = item.installation_type || item.id;
    if (seenInstallations.has(key)) return;
    seenInstallations.add(key);
    curated.push(item);
  });

  curated.slice(0, 6).forEach((item) => {
    const card = document.createElement("article");
    const targetFilter = getItemPrimaryFilter(item);
    card.className = "showcase-card";
    card.innerHTML = `
      <img src="${item.src}" alt="${humanTitle(item)}" loading="lazy" decoding="async" />
      <div class="showcase-content">
        <h3>${humanTitle(item)}</h3>
        <p>${humanSubtitle(item)}</p>
        <button class="showcase-action" type="button" data-filter="${targetFilter}">
          Ver mais desse estilo
        </button>
      </div>
    `;
    showcaseGrid.appendChild(card);
  });

  Array.from(document.querySelectorAll(".showcase-action")).forEach(
    (button) => {
      button.addEventListener("click", () => {
        const filter = button.dataset.filter || "all";
        setGalleryFilterAndGo(filter);
      });
    },
  );
};

const applyServiceBackgrounds = (services = {}) => {
  serviceCards.forEach((card) => {
    const key = card.dataset.service;
    const data = services[key];
    if (data?.src) {
      card.style.backgroundImage = `linear-gradient(165deg, rgba(6, 9, 14, 0.76), rgba(6, 9, 14, 0.26)), url('${data.src}')`;
      const paragraph = card.querySelector("p");
      if (paragraph && data.subtitle) paragraph.textContent = data.subtitle;
    }
  });
};

const applyHeroSlides = (hero = []) => {
  heroSlides.forEach((slide, index) => {
    const item = hero[index];
    if (!item) return;
    slide.src = item.src;
    slide.alt = humanTitle(item);
  });
};

const getFilteredGalleryItems = () => {
  if (currentFilter === "all") return galleryData;
  return galleryData.filter((item) =>
    (item.categories || []).includes(currentFilter),
  );
};

const renderGalleryPagination = (totalItems) => {
  if (!galleryPagination) return;

  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  galleryPagination.innerHTML = "";

  const createButton = (label, page, disabled = false, active = false) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `page-btn${active ? " is-active" : ""}`;
    button.textContent = label;
    button.disabled = disabled;
    button.addEventListener("click", () => {
      currentPage = page;
      renderGalleryCurrentPage();
    });
    return button;
  };

  galleryPagination.appendChild(
    createButton("Anterior", Math.max(1, currentPage - 1), currentPage === 1),
  );

  const visiblePages = [];
  for (let page = 1; page <= totalPages; page += 1) {
    if (
      page === 1 ||
      page === totalPages ||
      Math.abs(page - currentPage) <= 1
    ) {
      visiblePages.push(page);
    }
  }

  let previous = 0;
  visiblePages.forEach((page) => {
    if (previous && page - previous > 1) {
      const dots = document.createElement("span");
      dots.className = "page-dots";
      dots.textContent = "...";
      galleryPagination.appendChild(dots);
    }
    galleryPagination.appendChild(
      createButton(String(page), page, false, page === currentPage),
    );
    previous = page;
  });

  galleryPagination.appendChild(
    createButton(
      "Próxima",
      Math.min(totalPages, currentPage + 1),
      currentPage === totalPages,
    ),
  );
};

const renderGallerySummary = (totalItems, from, to) => {
  if (!gallerySummary) return;
  if (!totalItems) {
    gallerySummary.textContent = "Nenhuma imagem encontrada para este filtro.";
    return;
  }

  gallerySummary.textContent = `Mostrando ${from}-${to} de ${totalItems} imagens em ${labelForFilter(currentFilter)}.`;
};

const renderGalleryCurrentPage = () => {
  if (!galleryGrid) return;

  const filtered = getFilteredGalleryItems();
  const totalItems = filtered.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  currentPage = Math.min(Math.max(1, currentPage), totalPages);

  const start = (currentPage - 1) * pageSize;
  const end = start + pageSize;
  const pageItems = filtered.slice(start, end);

  galleryGrid.innerHTML = "";

  pageItems.forEach((item, pageIndex) => {
    const absoluteFilteredIndex = start + pageIndex;
    const figure = document.createElement("figure");
    figure.className = "gallery-item";
    figure.dataset.filteredIndex = String(absoluteFilteredIndex);
    figure.dataset.title = humanTitle(item);
    figure.dataset.subtitle = humanSubtitle(item);
    figure.innerHTML = `<img src="${item.src}" alt="${humanTitle(item)}" loading="lazy" decoding="async" />`;
    figure.addEventListener("click", () => {
      openLightboxByFilteredIndex(absoluteFilteredIndex);
    });
    galleryGrid.appendChild(figure);
  });

  const from = totalItems ? start + 1 : 0;
  const to = Math.min(end, totalItems);
  renderGallerySummary(totalItems, from, to);
  renderGalleryPagination(totalItems);
};

const setGalleryFilter = (filter = "all") => {
  currentFilter = filter;
  currentPage = 1;
  chips.forEach((chip) => {
    chip.classList.toggle("is-active", chip.dataset.filter === filter);
  });
  renderGalleryCurrentPage();
};

const setGalleryFilterAndGo = (filter = "all") => {
  setGalleryFilter(filter);
  gallerySection?.scrollIntoView({ behavior: "smooth", block: "start" });
};

chips.forEach((chip) => {
  chip.addEventListener("click", () => {
    setGalleryFilter(chip.dataset.filter || "all");
  });
});

serviceButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const filter = button.dataset.filter || "all";
    setGalleryFilterAndGo(filter);
  });
});

const renderLightboxItem = (item) => {
  if (!lightboxImage || !lightboxTitle) return;
  lightboxImage.classList.remove("loaded");
  lightboxImage.src = item.src;
  lightboxImage.alt = humanTitle(item);
  lightboxTitle.textContent = `${humanTitle(item)}${humanSubtitle(item) ? " · " + humanSubtitle(item) : ""}`;
};

const openLightboxByFilteredIndex = (filteredIndex) => {
  const filtered = getFilteredGalleryItems();
  if (!filtered.length) return;
  activeFilteredIndex = Math.min(
    Math.max(0, filteredIndex),
    filtered.length - 1,
  );
  renderLightboxItem(filtered[activeFilteredIndex]);
  lightbox?.classList.add("is-open");
  lightbox?.setAttribute("aria-hidden", "false");
  document.body.classList.add("lightbox-open");
};

const closeLightbox = () => {
  lightbox?.classList.remove("is-open");
  lightbox?.setAttribute("aria-hidden", "true");
  document.body.classList.remove("lightbox-open");
};

const changeLightbox = (direction) => {
  const filtered = getFilteredGalleryItems();
  if (!filtered.length) return;
  activeFilteredIndex =
    (activeFilteredIndex + direction + filtered.length) % filtered.length;
  renderLightboxItem(filtered[activeFilteredIndex]);
};

lightboxImage?.addEventListener("load", () => {
  lightboxImage.classList.add("loaded");
});

lightboxClose?.addEventListener("click", closeLightbox);
lightboxPrev?.addEventListener("click", () => changeLightbox(-1));
lightboxNext?.addEventListener("click", () => changeLightbox(1));

lightbox?.addEventListener("click", (event) => {
  if (event.target === lightbox) closeLightbox();
});

window.addEventListener("keydown", (event) => {
  if (!lightbox?.classList.contains("is-open")) return;
  if (event.key === "Escape") closeLightbox();
  if (event.key === "ArrowRight") changeLightbox(1);
  if (event.key === "ArrowLeft") changeLightbox(-1);
});

const updateScrollEffects = () => {
  const y = window.scrollY || 0;
  topbar?.classList.toggle("scrolled", y > 20);
  if (heroMedia) {
    const offset = Math.min(y * 0.08, 34);
    heroMedia.style.transform = `translate3d(0, ${offset}px, 0)`;
  }
};

let isTickingScroll = false;
window.addEventListener(
  "scroll",
  () => {
    if (isTickingScroll) return;
    isTickingScroll = true;
    requestAnimationFrame(() => {
      updateScrollEffects();
      isTickingScroll = false;
    });
  },
  { passive: true },
);
updateScrollEffects();

const revealTargets = document.querySelectorAll(".reveal");
const timelineSteps = document.querySelectorAll(".timeline-step");

const revealObserver = new IntersectionObserver(
  (entries, observer) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add("visible");
      observer.unobserve(entry.target);
    });
  },
  { threshold: 0.15, rootMargin: "0px 0px -8% 0px" },
);

revealTargets.forEach((target) => revealObserver.observe(target));

const timelineObserver = new IntersectionObserver(
  (entries, observer) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      const delay = Number(entry.target.dataset.delay || 0);
      if (delay > 0 && !prefersReducedMotion) {
        setTimeout(() => entry.target.classList.add("visible"), delay);
      } else {
        entry.target.classList.add("visible");
      }
      observer.unobserve(entry.target);
    });
  },
  { threshold: 0.28, rootMargin: "0px 0px -10% 0px" },
);

timelineSteps.forEach((step, index) => {
  step.dataset.delay = String(index * 95);
  timelineObserver.observe(step);
});

const handleResize = () => {
  const nextPageSize = getPageSize();
  if (nextPageSize === pageSize) return;
  pageSize = nextPageSize;
  currentPage = 1;
  renderGalleryCurrentPage();
};

window.addEventListener("resize", handleResize, { passive: true });

const bootstrapContent = async () => {
  try {
    const response = await fetch(FRONTEND_DATA_PATH, { cache: "default" });
    if (!response.ok) throw new Error("frontend-content unavailable");
    const data = await response.json();

    applyHeroSlides(data.hero || []);
    renderShowcase(data.showcase || []);
    galleryData = data.gallery || [];
    applyServiceBackgrounds(data.services || {});
  } catch (error) {
    const fallback = {
      src: "./assets/images/logo.webp",
      title: "Decora Varal de Luzes",
      subtitle: "Portfólio local indisponível no momento",
      categories: ["all"],
    };

    renderShowcase([fallback]);
    galleryData = [fallback];
  } finally {
    pageSize = getPageSize();
    setGalleryFilter("all");
    setupHeroEntrance();
    startHeroCycle();
  }
};

bootstrapContent();
