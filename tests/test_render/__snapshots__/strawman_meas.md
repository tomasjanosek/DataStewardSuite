# Strawman: meas

*Návrh k revizi před seancí. Nic zde není potvrzeno.*

## Návrh konceptuálního modelu

### Varianta A: entity podle fyzických tabulek

Každá core tabulka odpovídá jedné entitě 1:1.

| Entita | Grain | Fyzické mapování | Zdůvodnění |
|---|---|---|---|
| Měřicí místo | Jeden řádek = jedno měřicí místo. | MEAS_VAR | MEAS_VAR nese jednoznačný identifikátor a typ měření. (physical_model:MEAS_VAR, high) |

**Důsledky:** Rychlé na vytvoření, ale blízko fyzickému modelu.

## Kandidátní pojmy

- **Odečet**: Naměřená hodnota spotřeby k danému měřicímu místu a času. (document:meas-proces-popis.md, high)

## Kandidátní proces vzniku dat

1. **Technik** v systému **AVE** — Instalace zařízení: Založí nové měřicí místo. (document:meas-proces-popis.md, medium)

## Kandidátní pravidla

- Aktivní měřicí místo musí mít přiřazené zařízení. (document:meas-proces-popis.md, medium)

## Otázky pro stewarda (2)

- (architect, medium) Je MEAS_VAR skutečně 1:1 s byznysovým pojmem měřicí místo? [zdroj: physical_model:MEAS_VAR]
- (domain_expert, low) Co se stane se stavem místa při výměně zařízení? [zdroj: document:meas-proces-popis.md]
