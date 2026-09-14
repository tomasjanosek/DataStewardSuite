Doména: {domain_name}
Cíl seance: {domain_goal}

Níže je deterministicky vyfiltrovaný výřez fyzického modelu datového skladu pro tuto
doménu — tabulky napříč vrstvami L0 (landing/trusted), L1 (core/CDM) a L2 (datamart),
jejich sloupce s byznysovými komentáři, a lineage (ze kterých tabulek se která tabulka
plní):

{physical_model_slice}

Navrhni konceptuální model domény ve **dvou variantách** abstrakce. Konceptuální
model NENÍ přemapování katalogu 1:1 — je to abstrakce. Typická varianta má
**5 až 15 entit**, i když výřez obsahuje desítky nebo stovky fyzických tabulek:
jedna konceptuální entita typicky spojuje víc souvisejících fyzických tabulek napříč
vrstvami (např. L0 zdrojová tabulka + L1 core tabulka + L2 datamart fakt, které
modelují tentýž byznysový koncept). Pokud varianta vychází s desítkami entit, je
příliš doslovná — sluč to, co představuje stejný koncept.

1. Pro každou variantu urči kandidátní entity — název, `grain` (co představuje jeden
   řádek), fyzické mapování (kódy VŠECH tabulek, které do entity spadají) a
   zdůvodnění (`rationale`).
2. U každé varianty popiš `consequences` — co steward tou volbou získá a co ztratí,
   jak blízko/daleko je varianta od fyzického modelu, jak snadno se bude stewardovi
   vysvětlovat.
3. Každé zdůvodnění musí mít `source="physical_model"`, `ref` = kód tabulky nebo
   sloupce a `confidence`.
4. Tabulky, které jsou čistě technické/referenční (překladové číselníky, audit
   sloupce) nemusí dostat vlastní entitu — zmiň je jako atributy nebo referenční
   data v rámci entity, které patří, nebo je vynech a zmiň v otázce, pokud si
   nejsi jistý, kam patří.

Pokud v modelu chybí informace nutná pro jednoznačné rozhodnutí, nehádej — nech to na
stewardovi a promítni to do nižší `confidence` daného tvrzení.
