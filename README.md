# Data Steward Suite — Steward Session MVP

Agentická aplikace pro vedení strukturované seance s data stewardem. Výstupem je
potvrzený popis datové oblasti jako markdown soubory ve vaultu (Obsidian-kompatibilní
git repozitář). Viz zadání: `Zadání: Steward Session — MVP`.

Pilotní domény: **Měření (MEAS)** a **Nákup / TenderBox (procurement)** —
`config/domains/*.yaml`.

## Stav

**Milestones 1–3 jsou hotové.**

- **1 (skelet a schémata):** Pydantic modely artefaktů, deterministický renderer,
  `VaultWriter`, snapshot testy.
- **2 (prep pipeline):** `model_loader`/`doc_loader`, architect + domain_expert crews
  (CrewAI), strawman generation. Ověřeno živě proti reálnému katalogu (109+ tabulek na
  doménu) a proti Anthropic API.
- **3 (seance):** konverzační `SessionFlow` (CrewAI Flow), persistence a resume
  (`sessions/{id}/state.json` + `events.jsonl`), deterministické potvrzování/zamítání
  jednotlivých prvků (nikdy LLM), Streamlit UI (REVIEW brána → souhlas → konverzace +
  živý artefakt → finalizace do vaultu). Ověřeno živě v prohlížeči end-to-end včetně
  reloadu stránky (resume).

Milestone 4 (analytik, Redshift, baseline pro pravidla kvality) a 5 (nasazení na EC2)
zbývají — viz zadání sekce 12.

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

Testy, které volají živý LLM (`tests/test_orchestration/test_*_crew.py`,
`test_session_flow.py`), se automaticky přeskočí bez `ANTHROPIC_API_KEY` v `.env`.

### Spuštění UI

```bash
docker compose up ui
```

Otevři `http://localhost:8501`. Vyber doménu a `session_id`. Pro novou seanci musí
napřed existovat strawman (výstup PREP fáze):

```bash
docker compose run --rm app python -m src.orchestration.prep --domain meas --model-path data/physical_model.json
```

Vault (`./vault`, gitignored zde) je samostatný lokální git repozitář, do kterého
`VaultWriter` commituje. Aplikace ho při prvním běhu sama inicializuje (`git init`).
Otevři nad ním pracovní kopii v Obsidianu.

## Struktura

```
src/
  models/          Pydantic schémata artefaktů (Provenance, DomainCard, Entity,
                    Strawman, SessionState, ...)
  render/          deterministický renderer Pydantic -> markdown (entity, domain
                    card, strawman)
  tools/           vault_writer, model_loader, doc_loader, domain_config, event_log;
                    redshift (TODO, milestone 4)
  orchestration/   CrewAI — jediné místo s `from crewai import ...`: architect/
                    domain_expert/lead crews, PREP pipeline, SessionFlow, persistence
  agents/prompts/  prompty (česky, mimo kód)
  ui/              Streamlit app (REVIEW gate, konverzační seance)
  profiling/       CLI pro předvýpočet profilu dat (TODO, milestone 4)
config/domains/    briefy domén (meas.yaml, procurement.yaml)
data/              fyzický model + podkladové dokumenty (lokální, gitignored —
                    obsahuje interní schéma a byznys logiku)
sessions/          stav seancí a strawmany (lokální, gitignored)
vault/             git repo se seance výstupy (vzniká za běhu, gitignored)
tests/
```
