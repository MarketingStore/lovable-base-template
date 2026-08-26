# Drive-térkép

Minden a közös Google Drive-on van (tulajdonos: `board.marketingstore@gmail.com`),
a Drive connectoron keresztül éred el. A mappa-ID-kkal közvetlenül tudsz keresni:

```
parentId = '<mappa-ID>'
```

Ez sokkal megbízhatóbb, mint névre keresni, mert több hasonló nevű mappa is van
(pl. három különböző „Számlatörténet").

## Bejövő számlák — könyvelési anyag

| Mappa | ID |
|---|---|
| `0Könyvelési anyag` (gyökér) | `1s2wPzRFCf5qbGPZAP-iD8J1Xoak5kqle` |
| └ `Konyveles 2026-07` | `12GopEsI_hC4u28NKTQt82h17HtWSSnLH` |

A havi mappák neve **ékezet nélkül**: `Konyveles ÉÉÉÉ-HH`. Új hónapnál ugyanezt a
mintát kövesd, ne írd át „Könyvelés"-re — a meglévő mappa így néz ki.

### Fájlnév-konvenció

```
{sorszám}_{számla kelte}_{szállító neve}.pdf
```

Példák valós fájlokból:

```
001_2026-07-01_Bihari_Miklós,_32404094.pdf
037_2026-07-12_Adobe_Systems_Software_Ireland_Ltd.PDF
118_2026-07-31_I.T._Magyar_Cinema_Kft..pdf
049_2026-07-15_MAGYAR_POSTA_ZÁRTKÖRŰEN_MŰKÖDŐ_RÉSZVÉNYTÁRSASÁG_ÁLTAL_KÉPVIS.pdf
```

Amit ezekből tudni kell:

- A sorszám **három számjegy**, `001`-től, a hónapon belül folytonos.
- A rendezés a **számla kelte** szerint növekvő — nem a letöltés vagy a beérkezés
  szerint. Egy napon belül a sorrend szabad.
- A dátum `ÉÉÉÉ-HH-NN`.
- A szállítónévben a **szóköz aláhúzásra** cserélődik, az **ékezet marad**, a pont és
  a vessző is marad. Ezért lesz `Kft..pdf` — dupla pont, ez így helyes.
- A hosszú cégnév **~60 karakternél levágódik** (lásd a Magyar Posta példát).
- A kiterjesztés lehet `.pdf` és `.PDF` is, mindkettő előfordul. Ne írd át.

A `scripts/szamla_rendez.py` pontosan ezt a konvenciót valósítja meg, tehát ha
szkripttel nevezel át, ezzel nem kell foglalkoznod.

## Kimenő oldal — ERSTE TIG-ek

```
Erste/                                     1dBM7vR2VI8oJe6DCr7ki_LscwckgFKs1
├── Napfény Park/                          1hGQOoaEJTx0OMDEI3N8RzY8ZWr0CSqFb
│   └── 2026/                              1SybRQnCPGcYKVJc1YgQ-DT1UTa1xePsV
├── Target Center/                         1dJUO0q4Uwc1rwArQNsni6FG-onKcH_3-
│   └── 2026/                              1WAOKoKQlERWuAV65HreZOfZ0mAL7-XTo
└── Corso Kaposvár/                        1uVK_ZrCU9G2zGITSW_ij29RGvh7KY3JT
    └── 2026/                              1hnxKKP5Wzn5vIjIO9TWTrSHbRELzcMG4
```

TIG fájlnév-minta: `{hó}_{ügyfélkód}_marketing_TIG_{év}.docx`, pl.
`03_NFP_marketing_TIG_2026.docx`. A hónap **kétjegyű**, és **a teljesítés hónapja**,
nem a kiállításé — a márciusi teljesítésről április 1-jén kelt TIG neve `03_...`.

Minden TIG-ből `.docx` és `.pdf` is van a mappában. A docx a szerkeszthető, a pdf megy
ki aláírásra.

### Megtakarítás-variáns

Néhány hónapban ügyfelenként **két** TIG készül:

```
03_NFP_marketing_TIG_2026.docx           ← a havi keret
03_NFP_marketing_TIG_2026_megtak.docx    ← az előző évi maradvány felhasználása
```

A `_megtak` fájl mindenben azonos, egyetlen eltéréssel: a teljesítési időszak sora
kiegészül azzal, hogy `- 2025. évi költségvetés megtakarításainak felhasználása`.
Ez két külön számlát is jelent. Ha egy hónapban van megtakarítás-felhasználás, kérdezz
rá, hogy melyik ügyfélnél és mennyi — ez nem vezethető le a korábbi hónapokból.

## Egyéb TIG-ek

Az általános sablonnal készült TIG-ek szétszórtan, ügyfélmappákban vannak, nem egy
központi helyen. Példák (Arcideál):

| Fájl | Mappa-ID |
|---|---|
| `Arcideál TIG - Havidíj 2026.01. hó.docx` | `1f-lyQ7vWke4rlH3hkkmS9asgVKFYdnI5` |
| `TIG Dobó István EV - Arcideál_Marketing együttműködés 2026.01.hó.docx` | `12eIFoWEWA-Jcj-iwnsN0OGYiDXr_z6-T` |
| `TIG Kurucsai János EV - Arcideál_linképítés 2026.01..docx` | `1_VU10H8ZRuhVricleLw2t6gaawlbxEEV` |
| `Arcideál TIG - Weboldal programozás.docx` | `154fTTHG3NfSiah5rQ0lpQmTxLuqVq4r_` |

Itt a fájlnév nem szigorú konvenció. Új TIG-nél a legutóbbi hónap nevét vedd mintának
ugyanabban a mappában, ne találj ki újat.

## Pályázati / projekt TIG-ek

Van egy harmadik, ritkább forma is: pályázati projekteknél (pl. ROHU00291 „ROLE-ART")
a partner saját TIG-formáját használjuk, ami sem az általánossal, sem az ERSTE-ssel nem
egyezik — más a fejléc, és EUR összeg szerepel rajta. Ezekhez **nincs sablon a
skillben**; ha ilyen jön, kérd el az adott projekt korábbi TIG-jét mintának.

Példák: `MS TIG szállás ROHU.pdf`, `TIG MS fesztivalszervezes.pdf` — a
`17zoZb1sObSkAorAcHE4bxzs_xs1S3NE9` és `1CJUFSw12iRj5RUz25uee0gWLs8iA1MZi` mappákban.

## Ha egy ID nem működik

A mappák átszervezhetők, az ID-k elavulhatnak. Ilyenkor keress névre:

```
title contains 'Konyveles' and mimeType = 'application/vnd.google-apps.folder'
```

és **frissítsd ezt a fájlt** az új ID-vel, hogy legközelebb ne kelljen újra keresni.
