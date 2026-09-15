# Data Steward Suite — Steward Session MVP

Agentická aplikace pro vedení strukturované seance s data stewardem. Výstupem je
potvrzený popis datové oblasti jako markdown soubory ve vaultu (Obsidian-kompatibilní
git repozitář). Viz zadání: `Zadání: Steward Session — MVP`.

Pilotní domény: **Měření (MEAS)** a **Nákup / TenderBox (procurement)** —
`config/domains/*.yaml`.

## Stav

**Milestones 1–5 jsou hotové.**

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
- **5 (nasazení):** hardened `Dockerfile`/`docker-compose.prod.yml`, IAM policy
  dokumenty a EC2 `user-data.sh` bootstrap, sekrety vždy z AWS Secrets Manageru
  (nikdy na disku ani v repozitáři — viz `scripts/entrypoint.sh`), plný runbook níže.
  **Neprovedeno živě** — tato relace neměla připojený AWS účet, takže žádná reálná
  infrastruktura nebyla vytvořena ani otestována; jde o připravené artefakty a
  postup ze zadání sekce 12 ("docker-compose, EC2, SSM, README s postupem").

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

## Nasazení (EC2 + SSM)

**Bezpečnostní blocker platí i tady** — bez veřejné IP, bez SSH, jediný přístup je
přes SSM Session Manager. Postup je ruční (MVP: "rychle a ručně", ne Terraform) —
`deploy/user-data.sh` dělá zbytek automaticky při startu instance.

1. **Secrets Manager** — vytvoř secret `steward-session/prod` (typ "Other", jako
   JSON). Obsahuje **jen** Redshift přihlašovací údaje — viz
   `deploy/secret-shape.example.json` pro přesný tvar (odstraň `_comment` klíč před
   uploadem). Bedrock nepotřebuje statické klíče — autentizace jde přes IAM roli
   instance.

   ```bash
   aws secretsmanager create-secret --name steward-session/prod \
     --secret-string file://secret.json --region eu-central-1
   ```

2. **IAM role** — vytvoř roli s trust policy `deploy/iam-trust-policy.json`, přilož
   dvě policy:
   - vlastní `deploy/iam-instance-policy.json` (nejdřív doplň `REPLACE_REGION`,
     `REPLACE_ACCOUNT_ID`, `REPLACE_DOCS_BUCKET` — přesně tři oprávnění dle zadání
     sekce 8: Bedrock invoke, Secrets Manager read, S3 read na adresář podkladů,
     nic víc),
   - AWS-managed `AmazonSSMManagedInstanceCore` (pro Session Manager — není součástí
     aplikačních oprávnění, je to samostatný požadavek SSM).

   Vytvoř z role instance profile a přiřaď ho EC2 instanci.

3. **Síť** — instance v privátní síti (nebo veřejné podsíti bez veřejné IP),
   security group **bez jakéhokoli inbound pravidla** (SSM funguje čistě přes
   outbound HTTPS na SSM endpointy — buď NAT gateway, nebo VPC endpointy pro `ssm`,
   `ssmmessages`, `ec2messages`, pokud je podsíť plně privátní).

4. **EC2 instance** — Amazon Linux 2023 nebo Ubuntu, žádná veřejná IP, IAM instance
   profile z kroku 2, jako User data vlož `deploy/user-data.sh` (uprav proměnné
   `REPO_URL`/`AWS_REGION`/`BEDROCK_MODEL_ID`/`SECRETS_ID` na začátku souboru, nebo
   je předej jako proměnné prostředí instance). Skript nainstaluje Docker, stáhne
   repozitář do `/opt/steward-session`, napíše ne-tajný `.env` a spustí
   `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build ui`.

   Pokud je repozitář privátní, uprav `REPO_URL` na variantu s deploy klíčem nebo
   tokenem — `user-data.sh` to samo neřeší.

5. **Ověření SSM konektivity:**

   ```bash
   aws ssm describe-instance-information --region eu-central-1
   ```

   Instance by se měla objevit se stavem `Online` (typicky do pár minut po startu).

6. **Port forwarding a otevření UI:**

   ```bash
   aws ssm start-session --target <instance-id> \
     --document-name AWS-StartPortForwardingSession \
     --parameters '{"portNumber":["8501"],"localPortNumber":["8501"]}' \
     --region eu-central-1
   ```

   Pak otevři `http://localhost:8501` v prohlížeči — tunelováno přes SSM, žádný
   veřejný port na instanci.

7. **Aktualizace po nasazení** — přes stejný SSM tunel se lze připojit i k shellu
   (`aws ssm start-session --target <instance-id>`) a spustit:

   ```bash
   cd /opt/steward-session && git pull && \
     docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build ui
   ```

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
scripts/           entrypoint.sh + fetch_secrets.py (Secrets Manager -> env, nikdy na disk)
deploy/            IAM policy dokumenty, EC2 user-data.sh, tvar secretu (nasazení)
tests/
```
