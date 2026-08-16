async function fetchJson(path) {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`Failed to load ${path}`);
  }
  return response.json();
}

function buildCard(record) {
  const template = document.getElementById("sigil-card-template");
  const card = template.content.firstElementChild.cloneNode(true);

  card.style.borderColor = `${record.card.accent}55`;
  card.querySelector("h2").textContent = record.card.title;
  card.querySelector(".sigil-card__tier").textContent = record.metadata.tier;
  const img = card.querySelector("img");
  img.src = `../${record.metadata.svg.file}`;
  img.alt = `${record.metadata.name} preview`;
  card.querySelector(".sigil-card__summary").textContent = record.metadata.summary;

  const badgeList = card.querySelector(".sigil-card__badges");
  record.card.badges.forEach((badge) => {
    const item = document.createElement("li");
    item.textContent = badge;
    item.style.border = `1px solid ${record.card.accent}`;
    badgeList.appendChild(item);
  });

  const calloutList = card.querySelector(".sigil-card__callouts");
  record.card.callouts.forEach((callout) => {
    const item = document.createElement("li");
    item.textContent = callout;
    calloutList.appendChild(item);
  });

  const mapping = card.querySelector(".sigil-card__mapping");
  record.mapping.parameterOverrides.forEach((override) => {
    const term = document.createElement("dt");
    term.textContent = override.parameter;
    const detail = document.createElement("dd");
    detail.textContent = `${override.effect} ${override.value} ${override.unit}`;
    mapping.append(term, detail);
  });

  return card;
}

function filterRecords(records, domain) {
  if (domain === "all") {
    return records;
  }
  return records.filter((record) => record.metadata.invocationDomains.includes(domain));
}

function renderCatalog(records, domain) {
  const catalog = document.getElementById("catalog");
  catalog.replaceChildren(...filterRecords(records, domain).map(buildCard));
}

async function init() {
  const manifest = await fetchJson("../registry/manifest.json");
  const records = await Promise.all(
    manifest.sigils.map(async (entry) => {
      const [metadata, card, mapping] = await Promise.all([
        fetchJson(`../${entry.metadataPath}`),
        fetchJson(`../${entry.cardPath}`),
        fetchJson(`../${entry.mappingPath}`)
      ]);
      return { metadata, card, mapping };
    })
  );

  const domainFilter = document.getElementById("domain-filter");
  const domains = new Set(records.flatMap((record) => record.metadata.invocationDomains));
  [...domains].sort().forEach((domain) => {
    const option = document.createElement("option");
    option.value = domain;
    option.textContent = domain;
    domainFilter.appendChild(option);
  });

  domainFilter.addEventListener("change", (event) => {
    renderCatalog(records, event.target.value);
  });

  renderCatalog(records, "all");
}

init().catch((error) => {
  const catalog = document.getElementById("catalog");
  catalog.textContent = error.message;
});
