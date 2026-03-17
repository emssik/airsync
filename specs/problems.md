# Code Review: airsync

## KRYTYCZNE BUGI

### 1. SQL Injection — brak quotowania identyfikatorów
`src/emsairtable/schema_sync.py:88-92` i `src/emsairtable/data_sync.py:100-104`

Nazwy tabel i kolumn są wstawiane bezpośrednio do SQL przez f-stringi. Dane pochodzą z Airtable (zewnętrzne źródło) — wystarczy tabela/pole z nazwą zawierającą `); DROP TABLE ...` żeby uzyskać injection. Trzeba używać `psycopg2.sql.Identifier()`.

### 2. Nieokreślona kolejność kolumn w upsert — potencjalnie mieszane dane
`src/emsairtable/data_sync.py:70-76`

```python
all_fields = set()  # set() nie gwarantuje kolejności!
...
columns = [self.schema_sync.clean_name(k) for k in all_fields]  # iteracja 1
...
for field_name in all_fields:  # iteracja 2
```

Kolumny i wartości budowane z `set()` — choć w CPython kolejność iteracji seta jest stabilna w ramach jednego przebiegu, to jest kruche i niebezpieczne. Należy użyć listy.

### 3. Masowe redundantne wywołania API Airtable
`src/emsairtable/data_sync.py:150-158`

`sync_base_data()` wywołuje `get_base_schema()` (linia 154), a potem dla KAŻDEJ tabeli wywołuje `sync_table_data()`, który PONOWNIE wywołuje `get_base_schema()` (linia 129). Każde `get_base_schema()` z kolei wywołuje `list_bases()` (airtable_client.py:29) — osobny request API. Przy 10 tabelach to minimum 20 zbędnych requestów do API.

### 4. `_batch_upsert_records` nie jest batchowy
`src/emsairtable/data_sync.py:108-110`

Nazwa mówi "batch", ale wewnątrz jest pętla `for values in values_list` z osobnym `execute_modification` (i osobnym commitem) per rekord. To nie jest batch — to pojedyncze inserty w pętli.

### 5. Niespójność mapowania kolumn między `create_table` a `_batch_upsert_records`
`schema_sync.py:71-77` vs `data_sync.py:76`

`create_table` dodaje numerację do zduplikowanych nazw (`field`, `field_1`, `field_2`), ale `_batch_upsert_records` tego nie robi — po prostu wywołuje `clean_name`. Jeśli dwa pola w Airtable dają tę samą nazwę po clean (np. "Field!" i "Field?"), upsert trafi w złą kolumnę lub się wysypie.

---

## BUGI / PROBLEMY

### 6. Niekompletna lista reserved words
`src/emsairtable/schema_sync.py:124-127`

Tylko 9 słów. Brakuje wielu ważnych: `order`, `group`, `table`, `index`, `type`, `name`, `value`, `key`, `primary`, `default`, `create`, `drop`, `alter`, `column`, `limit`, `offset`, `between`...

### 7. `get_connection` context manager jest mylący
`src/database/postgresql.py:24-39`

Nazywa się "context manager do zarządzania połączeniem", ale nie zamyka połączenia. W przypadku błędu robi rollback, ale połączenie zostaje w potencjalnie niestabilnym stanie. Nie sprawdza też czy połączenie jest zamknięte (`self._conn.closed`).

### 8. Ścieżka do `config.yaml` jest relatywna
`src/main.py:12`, `sync_mentoring_schema.py:10`

`open('config.yaml', 'r')` — zadziała tylko jeśli CWD = root projektu. W Dockerze lub przy uruchomieniu z innego katalogu się wysypie.

---

## DRY — Powtórzony kod

### 9. `load_config()` i `pg_config` — kopiuj-wklej między dwoma skryptami
`src/main.py:11-36` ≈ `sync_mentoring_schema.py:9-33`

Identyczny kod konfiguracyjny w dwóch plikach. Powinien być wydzielony do wspólnego modułu.

### 10. `SchemaPrinter.print_schema()` i `get_schema_str()` — zduplikowana logika
`src/emsairtable/schema_printer.py:23-53` vs `56-92`

Te dwie metody mają identyczną logikę iteracji/formatowania. Różnica to `print()` vs `lines.append()`. `print_schema` powinien po prostu wywołać `print(self.get_schema_str(...))`.

### 11. Podwójne mapowanie typów
`airtable_client.py:57-78` (`_normalize_field_type`) + `schema_sync.py:17-40` (`type_mapping`)

Dwa osobne systemy mapowania typów, które muszą być ze sobą spójne. `airtable_client` mapuje np. `phoneNumber` → `phone`, potem `schema_sync` mapuje `phone` → `TEXT`. Działa "przypadkiem", bo nieznane typy defaultują do `TEXT`. Powinno być jedno mapowanie.

### 12. Częściowo zduplikowane czyszczenie nazw
`airtable_client.py:30`: `base_name = bases.get(base_id, base_id).lower().replace(' ', '_')`
`schema_sync.py:115-139`: pełna metoda `clean_name()`

Dwie logiki czyszczenia nazw, które mogą dać różne wyniki.

---

## KISS — Zbyt skomplikowane / Niepotrzebne

### 13. `sync_mentoring_schema.py` — cały plik jest zbędny
To kopia `main.py` z hardkodowanym `base_id`. Wystarczyłby parametr CLI do main.

### 14. `SchemaPrinter` — klasa niepotrzebna
Klasa z samymi `@staticmethod` i `@classmethod` — to po prostu dwie funkcje. Klasa nic tu nie wnosi.

### 15. `DataSync` tworzy wewnętrznie `SchemaSync`
`data_sync.py:19`: `self.schema_sync = SchemaSync(airtable_client, postgres_client)`

A w `main.py` tworzy się osobno `SchemaSync` i `DataSync`. `DataSync` tworzy więc drugą instancję SchemaSync, zamiast przyjmować ją jako dependency.

### 16. Nadmiarowy verbose output w `main.py`
Numerowane kroki (3, 4, 5, 6...) z komentarzami w printach, podwójne wypisywanie schematów (raz w main, raz w sync) — utrudnia czytanie i debugowanie zamiast pomagać. Logger z poziomami byłby lepszy.

---

## Podsumowanie priorytetów

| Priorytet | Problem | Ryzyko |
|-----------|---------|--------|
| P0 | SQL Injection (#1) | Bezpieczeństwo |
| P0 | Niespójność kolumn create vs upsert (#5) | Dane mogą trafić w złe kolumny |
| P1 | Redundantne API calls (#3) | Wydajność, rate limiting |
| P1 | Set ordering (#2) | Potencjalne pomieszanie danych |
| P2 | DRY violations (#9-12) | Utrzymywalność |
| P2 | KISS violations (#13-16) | Złożoność |
| P3 | Pozostałe (#6-8) | Niezawodność |
