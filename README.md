# Data Steward Suite — Steward Session MVP

Agentická aplikace pro vedení strukturované seance s data stewardem. Výstupem je
potvrzený popis datové oblasti jako markdown soubory ve vaultu (Obsidian-kompatibilní
git repozitář). Viz zadání: `Zadání: Steward Session — MVP`.

Pilotní domény: **Měření (MEAS)** a **Nákup / TenderBox (procurement)** —
`config/domains/*.yaml`.

## Stav

**Milestones 1–4 jsou hotové.**

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
- **4 (analytik):** `DataSource` abstrakce se dvěma backendy za stejným rozhraním —
  **Excel/pandas** (ověřený, offline, pro demo bez Redshiftu) a **Redshift**
  (produkční cesta ze zadání, strukturálně hotová, ale bez přístupu ke clusteru
  nebylo možné živě otestovat — viz `src/tools/redshift_source.py`). Analytik navrhuje
  strukturovaný dotaz (nikdy SQL/kód přímo z LLM), steward ho vidí a schvaluje před
  spuštěním, nález se ukládá jako `QualityRule` s naměřenou baseline. Profiling CLI
  pro předpočet statistik. Ověřeno živě end-to-end v UI proti syntetickým datům
  (`data/meas_demo.xlsx`).

Milestone 5 (nasazení na EC2, SSM) zbývá — viz zadání sekce 12.

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

### Spuštění UI (demo bez Redshiftu)

`.env.example` už je nastaven na offline demo cestu (`DATA_SOURCE_PROVIDER=excel`,
`EXCEL_DATA_PATH=data/meas_demo.xlsx`). Pro reálné demo si nejdřív vygeneruj syntetická
demo data (nebo tam dej vlastní `.xlsx` — každý list = jedna tabulka):

```bash
docker compose run --rm app python -c "
import pandas as pd
pd.DataFrame({'id': [1,2,3], 'stav': ['aktivni','aktivni',None]}).to_excel('data/meas_demo.xlsx', sheet_name='mereni_mista', index=False)
"
docker compose run --rm app python -m src.profiling.profile --domain meas
docker compose run --rm app python -m src.orchestration.prep --domain meas --model-path data/physical_model.json
docker compose up ui
```

Otevři `http://localhost:8501`, vyber doménu a `session_id`, projdi REVIEW branou a
seancí. V sekci **„Ověření hypotézy (analytik)"** napiš hypotézu (např. *„Aktivní
měřicí místo musí mít vždy přiřazené zařízení."*) — dotaz se navrhne, ukáže k
schválení, spustí se proti Excel datům, interpretuje a lze ho uložit jako pravidlo
kvality s naměřenou baseline.

Pro produkční Redshift cestu přepni `DATA_SOURCE_PROVIDER=redshift` a vyplň
`REDSHIFT_*` proměnné v `.env` — viz `src/tools/redshift_source.py` (strukturálně
hotovo, ale neověřeno živě proti clusteru).

Vault (`./vault`, gitignored zde) je samostatný lokální git repozitář, do kterého
`VaultWriter` commituje. Aplikace ho při prvním běhu sama inicializuje (`git init`).
Otevři nad ním pracovní kopii v Obsidianu.

## Struktura

```
src/
  models/          Pydantic schémata artefaktů (Provenance, DomainCard, Entity,
                    Strawman, SessionState, HypothesisQuery, DataProfile, ...)
  render/          deterministický renderer Pydantic -> markdown (entity, domain
                    card, strawman)
  tools/           vault_writer, model_loader, doc_loader, domain_config, event_log,
                    data_source (+ excel_source, redshift_source, factory)
  orchestration/   CrewAI — jediné místo s `from crewai import ...`: architect/
                    domain_expert/lead/analyst crews, PREP pipeline, SessionFlow,
                    persistence, session_actions (jediné místo, které smí nastavit
                    status="confirmed")
  agents/prompts/  prompty (česky, mimo kód)
  ui/              Streamlit app (REVIEW gate, konverzační seance, ověření hypotéz)
  profiling/       CLI pro předpočet profilu dat (offline, nikdy živě v seanci)
config/domains/    briefy domén (meas.yaml, procurement.yaml)
data/              fyzický model, podkladové dokumenty, demo Excel, profily (lokální,
                    gitignored — obsahuje interní schéma a byznys logiku)
sessions/          stav seancí a strawmany (lokální, gitignored)
vault/             git repo se seance výstupy (vzniká za běhu, gitignored)
tests/
```
