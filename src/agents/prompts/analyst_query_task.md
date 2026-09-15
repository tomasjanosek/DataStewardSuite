Hypotéza k ověření (od stewarda/leada): {hypothesis}

Dostupné tabulky a jejich profil (název, počet řádků, sloupce s null% a rozsahem):

{tables_summary}

Navrhni **jeden strukturovaný dotaz** (`HypothesisQuery` — tabulka, volitelné filtry,
volitelné seskupení, agregace), který tuto hypotézu otestuje. Použij pouze tabulky a
sloupce uvedené výše. Nepiš SQL ani kód — jen strukturovaná pole.

Výsledný JSON má na nejvyšší úrovni VŽDY přesně dva klíče, `query` a `rationale` —
`rationale` NIKDY nesmí chybět, i kdyby se zdálo zřejmé z `query.description`. Příklad
tvaru (hodnoty jsou jen ilustrace, nepřebírej je):

```json
{
  "query": {
    "table": "mereni_mista",
    "description": "Aktivní místa bez přiřazeného zařízení.",
    "filters": [
      {"column": "stav", "op": "eq", "value": "aktivni"},
      {"column": "zarizeni_id", "op": "is_null"}
    ],
    "aggregate": "count"
  },
  "rationale": "Hypotéza tvrdí, že aktivní místo má vždy zařízení — tento dotaz spočítá výjimky, tedy přímo ji testuje."
}
```
