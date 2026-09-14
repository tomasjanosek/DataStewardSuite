Doména: {domain_name}
Cíl seance: {domain_goal}

Níže je deterministicky vyfiltrovaný výřez fyzického modelu datového skladu pro tuto
doménu — tabulky napříč vrstvami L0 (landing/trusted), L1 (core/CDM) a L2 (datamart),
jejich sloupce s byznysovými komentáři, a lineage (ze kterých tabulek se která tabulka
plní):

{physical_model_slice}

Navrhni konceptuální model domény ve **dvou variantách** abstrakce:

1. Pro každou variantu urči kandidátní entity — název, `grain` (co představuje jeden
   řádek), fyzické mapování (kódy tabulek) a zdůvodnění (`rationale`).
2. U každé varianty popiš `consequences` — co steward tou volbou získá a co ztratí,
   jak blízko/daleko je varianta od fyzického modelu, jak snadno se bude stewardovi
   vysvětlovat.
3. Každé zdůvodnění musí mít `source="physical_model"`, `ref` = kód tabulky nebo
   sloupce a `confidence`.

Pokud v modelu chybí informace nutná pro jednoznačné rozhodnutí, nehádej — nech to na
stewardovi a promítni to do nižší `confidence` daného tvrzení.
