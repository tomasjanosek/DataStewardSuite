# Data Steward Suite — Steward Session MVP

Agentická aplikace pro vedení strukturované seance s data stewardem. Výstupem je
potvrzený popis datové oblasti jako markdown soubory ve vaultu (Obsidian-kompatibilní
git repozitář). Viz zadání: `Zadání: Steward Session — MVP`.

Pilotní doména: **Měření (MEAS)**.

## Stav

**Milestone 1 (skelet a schémata) je hotový.** Pydantic modely artefaktů, deterministický
renderer (Pydantic → markdown) a `VaultWriter`, pokryté snapshot testy. Žádné volání LLM,
žádní agenti — ty přijdou v milestonu 2+.

Zbývající milníky (2–5: prep pipeline, seance/UI, analytik/Redshift, nasazení) viz zadání
sekce 12.

## Bezpečnostní blocker pro produkci

MVP nemá žádnou autentizaci v aplikaci — počítá se s přístupem přes SSM port forwarding
na EC2 bez veřejné IP. **Toto musí být vyřešeno (SSO) před jakýmkoli rozšířením mimo
pilotní skupinu.**

## Vývoj

Repozitář neobsahuje Python runtime — spouští se v Dockeru:

```bash
cp .env.example .env
docker compose run --rm app pytest -q
```

Vault (`./vault`, gitignored zde) je samostatný lokální git repozitář, do kterého
`VaultWriter` commituje. Aplikace ho při prvním běhu sama inicializuje (`git init`).
Otevři nad ním pracovní kopii v Obsidianu.

## Struktura

```
src/
  models/          Pydantic schémata artefaktů (Provenance, DomainCard, Entity, ...)
  render/          deterministický renderer Pydantic -> markdown
  tools/           vault_writer (hotovo); model_loader, doc_loader, redshift (TODO)
  orchestration/   CrewAI Flow — jediné místo s `from crewai import ...` (TODO)
  agents/          prompty a role agentů (TODO)
  ui/              Streamlit (TODO)
  profiling/       CLI pro předvýpočet profilu dat (TODO)
config/domains/    brief domény (meas.yaml)
data/              fyzický model + podkladové dokumenty (TODO: naplnit v milestonu 2)
vault/             git repo se seance výstupy (vzniká za běhu, gitignored)
tests/
```
