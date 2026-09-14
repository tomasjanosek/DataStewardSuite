---
id: meas.mereni-mista
name: Měření místa
domain: meas
identifier: mereni_mista.id
status: confirmed
physical_mapping:
- meas.mereni_mista
---

# Měření místa

[[index|← zpět na doménu]]

## Definice

Fyzické místo, kde se instalací měřicího zařízení odečítá spotřeba.

## Granularita

Jeden řádek = jedno měřicí místo.

## Identifikátor

`mereni_mista.id`

## Fyzické mapování

- meas.mereni_mista

## Atributy

- **Stav měřicího místa** (`stav`, povinný) — Zda je místo aktivní, zrušené nebo v přípravě. Zdroj pravdy: AVE.

## Proces vzniku dat

1. **Technik** v systému **AVE** — Instalace měřicího zařízení: Založí nové měřicí místo a napojí ho na zařízení.

## Pravidla kvality

- **qr-mereni-mista-1**: Aktivní měřicí místo musí mít přiřazené zařízení.
  - Baseline: 12 z 10 482 aktivních míst bez zařízení
  - Navržený práh: 0 míst bez zařízení
  - Vlastník: Martin Vala

## Známé problémy

- Historická data před rokem 2018 nemají vyplněný stav.

## Otevřené otázky

- Co se stane se stavem místa při výměně zařízení?
