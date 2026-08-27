#!/usr/bin/env python3
"""Bejövő számlák sorszámozása, elnevezése és a havi köteg ellenőrzése.

A havi könyvelési mappában a számlák elnevezése:

    {sorszám}_{teljesítés dátuma}_{szállító neve}.pdf
    pl. 128_2026-07-31_GOOGLE_IRELAND_LIMITED.pdf

A dátum a **teljesítés dátuma** (a QUiCK-ben `fulfilled_at`), nem a számla kelte
és nem a fizetési határidő. A sorszám eszerint növekvő, 001-től, a hónapon belül
folytonos.

Fontos: a havi köteget rendes esetben a "Havi könyvelési csomag" n8n workflow
állítja elő a QUiCK API-ból, nem ez a szkript - lásd `references/quick-n8n.md`.
Ez a szkript a maradékra való: kézzel pótolt számla beillesztésére, és annak
ellenőrzésére, hogy a gépi köteg ép-e (a workflow részsikerrel is lefuthat, és
akkor hézag marad a számozásban).

Munkamegosztás: ha kézzel pótolsz, a szállítót és a teljesítés dátumát az agent
olvassa ki a PDF-ből (ez ítélet kérdése), és manifest JSON-ba írja. A
sorrendezés, sorszámozás, névtisztítás és az ütközések kiszűrése gépies és
hibaérzékeny, ezért van kódban.

    python3 szamla_rendez.py atnevez manifest.json --mappa ./Konyveles_2026-08
    python3 szamla_rendez.py ellenoriz --mappa ./Konyveles_2026-08
    python3 szamla_rendez.py osszesito --mappa ./Konyveles_2026-08 --csv ossz.csv
    python3 szamla_rendez.py --manifest-minta
"""
import argparse
import csv
import json
import os
import re
import sys
from collections import Counter

# Ékezet és pont marad, a szóköz aláhúzás lesz, a hosszú cégnév 60 karakternél
# levágódik - ezt a határt a "Havi könyvelési csomag" workflow szabja meg.
SZALLITO_MAX = 60
FAJLNEV_MINTA = re.compile(
    r"^(?P<sorszam>\d{3})_(?P<datum>\d{4}-\d{2}-\d{2})_(?P<szallito>.+)\.(?P<ext>[Pp][Dd][Ff])$"
)


def tisztit_szallito(nev: str) -> str:
    """Szállítónév fájlnévbe.

    Szándékosan bitre ugyanaz, mint a "Havi könyvelési csomag" n8n workflow
    `tiszta()` függvénye - a kézzel pótolt számla neve nem térhet el a gépitől,
    különben a köteg ellenőrzése hamis eltérést jelezne. Az eredeti:

        String(s||'').replace(/[\\/:*?"<>|]/g,'-').replace(/\\s+/g,'_').slice(0,60)

    Tehát: előbb a tiltott karakterek, utána a szóköz, végül vágás 60-nál -
    záró aláhúzás levágása NINCS, mert a workflow sem csinálja.
    """
    nev = str(nev or "")
    nev = re.sub(r'[/\\:*?"<>|]', "-", nev)
    nev = re.sub(r"\s+", "_", nev)
    return nev[:SZALLITO_MAX]


def uj_nev(sorszam: int, teljesites: str, szallito: str, ext: str = "pdf") -> str:
    return f"{sorszam:03d}_{teljesites}_{tisztit_szallito(szallito)}.{ext}"


def _datum_ok(d: str) -> bool:
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", d))


def _tartomanyok(szamok, max_db=12):
    """[2,3,4,7,9,10] -> '2-4, 7, 9-10'.

    Részlegesen lefutott workflow után több száz sorszám is hiányozhat; a nyers
    lista olvashatatlan, a tartományból viszont azonnal látszik, hol szakadt meg.
    """
    if not szamok:
        return ""
    szamok = sorted(szamok)
    csoportok, kezd, elozo = [], szamok[0], szamok[0]
    for n in szamok[1:]:
        if n == elozo + 1:
            elozo = n
            continue
        csoportok.append((kezd, elozo))
        kezd = elozo = n
    csoportok.append((kezd, elozo))
    reszek = [f"{a}" if a == b else f"{a}-{b}" for a, b in csoportok]
    if len(reszek) > max_db:
        marad = len(reszek) - max_db
        return ", ".join(reszek[:max_db]) + f", … (+{marad} további szakasz)"
    return ", ".join(reszek)


# ------------------------------------------------------------------ átnevezés

def atnevez(manifest_ut, mappa, szimulacio=False, kezdo=1):
    with open(manifest_ut, encoding="utf-8") as f:
        tetelek = json.load(f)
    if isinstance(tetelek, dict):
        tetelek = tetelek.get("szamlak", [])

    hibak = []
    for i, t in enumerate(tetelek):
        for kulcs in ("fajl", "teljesites", "szallito"):
            if not t.get(kulcs):
                hibak.append(f"[{i}] hiányzó mező: {kulcs}")
        if t.get("teljesites") and not _datum_ok(t["teljesites"]):
            hibak.append(f"[{i}] rossz dátumformátum: {t['teljesites']!r} (kell: ÉÉÉÉ-HH-NN)")
        if t.get("fajl") and not os.path.exists(os.path.join(mappa, t["fajl"])):
            hibak.append(f"[{i}] nincs meg a fájl: {t['fajl']}")
    if hibak:
        sys.exit("A manifest hibás, nem nyúlok a fájlokhoz:\n  " + "\n  ".join(hibak))

    # Teljesítés szerint növekvő; azonos napon a manifest sorrendje dönt (stabil
    # rendezés). A workflow ilyenkor a QUiCK expense id-ja szerint dönt.
    tetelek = sorted(tetelek, key=lambda t: t["teljesites"])

    tervek = []
    for n, t in enumerate(tetelek, start=kezdo):
        ext = os.path.splitext(t["fajl"])[1].lstrip(".") or "pdf"
        tervek.append((t["fajl"], uj_nev(n, t["teljesites"], t["szallito"], ext)))

    utkozes = [nev for nev, db in Counter(uj for _, uj in tervek).items() if db > 1]
    if utkozes:
        sys.exit("Névütközés lenne:\n  " + "\n  ".join(utkozes))

    for regi, uj in tervek:
        print(f"{regi}\n  -> {uj}")
        if not szimulacio:
            os.rename(os.path.join(mappa, regi), os.path.join(mappa, uj))
    print(f"\n{len(tervek)} számla {'(szimuláció, semmi nem változott)' if szimulacio else 'átnevezve'}")


# ----------------------------------------------------------------- ellenőrzés

def _beolvas_mappa(mappa):
    tetelek, ismeretlen = [], []
    for f in sorted(os.listdir(mappa)):
        if f.startswith("."):
            continue
        m = FAJLNEV_MINTA.match(f)
        if m:
            tetelek.append({
                "fajl": f,
                "sorszam": int(m.group("sorszam")),
                "teljesites": m.group("datum"),
                "szallito": m.group("szallito").replace("_", " "),
            })
        elif os.path.isfile(os.path.join(mappa, f)):
            ismeretlen.append(f)
    return tetelek, ismeretlen


def ellenoriz(mappa):
    tetelek, ismeretlen = _beolvas_mappa(mappa)
    if not tetelek:
        sys.exit(f"Nincs konvenció szerinti fájl itt: {mappa}")

    baj = []
    if ismeretlen:
        baj.append("Nem a konvenció szerinti fájl:\n    " + "\n    ".join(ismeretlen))

    sorszamok = [t["sorszam"] for t in tetelek]
    dupla = [s for s, db in Counter(sorszamok).items() if db > 1]
    if dupla:
        baj.append(f"Ismétlődő sorszám: {sorted(dupla)}")

    hianyzo = sorted(set(range(min(sorszamok), max(sorszamok) + 1)) - set(sorszamok))
    if hianyzo:
        baj.append(f"Kimaradt sorszám ({len(hianyzo)} db): {_tartomanyok(hianyzo)}"
                   "\n    Hézag jellemzően részlegesen lefutott workflow-t jelent, "
                   "nem hiányzó számlát.")
    if min(sorszamok) != 1:
        baj.append(f"A számozás nem 1-gyel kezdődik, hanem {min(sorszamok)}-vel")

    # A sorszámnak a teljesítés dátuma szerint növekvőnek kell lennie.
    rendezett = sorted(tetelek, key=lambda t: t["sorszam"])
    for elozo, kovetkezo in zip(rendezett, rendezett[1:]):
        if kovetkezo["teljesites"] < elozo["teljesites"]:
            baj.append(f"Teljesítés szerinti sorrend törik: {elozo['fajl']} után {kovetkezo['fajl']}")
            break

    # Ugyanaz a szállító + ugyanaz a nap többször: lehet jogos (Meta napi számlák),
    # de lehet duplán lementett PDF is - ezért figyelmeztetés, nem hiba.
    parok = Counter((t["szallito"], t["teljesites"]) for t in tetelek)
    gyanus = [f"{sz} — {d} ({db}×)" for (sz, d), db in parok.items() if db > 1]

    honapok = sorted({t["teljesites"][:7] for t in tetelek})
    print(f"{len(tetelek)} számla | hónap: {', '.join(honapok)} "
          f"| sorszámok: {min(sorszamok):03d}–{max(sorszamok):03d}")
    if len(honapok) > 1:
        baj.append(f"Több hónap keveredik egy mappában: {honapok}")

    if gyanus:
        print("\nEllenőrizd (azonos szállító, azonos nap — lehet jogos is):")
        for g in gyanus:
            print("   ", g)

    if baj:
        print("\nHIBÁK:")
        for b in baj:
            print("  -", b)
        return 1
    print("\nA köteg rendben: folytonos számozás, teljesítés szerinti sorrend.")
    return 0


def osszesito(mappa, csv_ut=None):
    """Szállítónkénti összesítő - ezzel gyorsan látszik, mi hiányzik a hónapból."""
    tetelek, _ = _beolvas_mappa(mappa)
    szamlalo = Counter(t["szallito"] for t in tetelek)
    sorok = sorted(szamlalo.items(), key=lambda x: (-x[1], x[0]))
    print(f"{len(tetelek)} számla, {len(szamlalo)} szállító\n")
    for nev, db in sorok:
        print(f"  {db:>3}×  {nev}")
    if csv_ut:
        with open(csv_ut, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["sorszám", "teljesítés dátuma", "szállító", "fájlnév"])
            for t in sorted(tetelek, key=lambda t: t["sorszam"]):
                w.writerow([t["sorszam"], t["teljesites"], t["szallito"], t["fajl"]])
        print(f"\nCSV kiírva: {csv_ut}")


MANIFEST_MINTA = [
    {"fajl": "letoltott_szamla_1.pdf", "teljesites": "2026-08-03", "szallito": "GOOGLE IRELAND LIMITED"},
    {"fajl": "meta_aug.pdf", "teljesites": "2026-08-01", "szallito": "Meta Platforms Ireland Limited"},
]


def main():
    ap = argparse.ArgumentParser(description="Bejövő számlák rendezése")
    ap.add_argument("parancs", nargs="?", choices=["atnevez", "ellenoriz", "osszesito"])
    ap.add_argument("manifest", nargs="?", help="manifest JSON (atnevez esetén)")
    ap.add_argument("--mappa", default=".", help="a havi könyvelési mappa")
    ap.add_argument("--csv", help="összesítő CSV útvonala")
    ap.add_argument("--kezdo", type=int, default=1, help="kezdő sorszám")
    ap.add_argument("--szimulacio", action="store_true", help="csak mutatja, mit tenne")
    ap.add_argument("--manifest-minta", action="store_true")
    args = ap.parse_args()

    if args.manifest_minta:
        print(json.dumps(MANIFEST_MINTA, ensure_ascii=False, indent=2))
        return
    if not args.parancs:
        ap.error("adj meg parancsot: atnevez / ellenoriz / osszesito")

    if args.parancs == "atnevez":
        if not args.manifest:
            ap.error("az atnevez parancshoz kell manifest JSON")
        atnevez(args.manifest, args.mappa, args.szimulacio, args.kezdo)
    elif args.parancs == "ellenoriz":
        sys.exit(ellenoriz(args.mappa))
    else:
        osszesito(args.mappa, args.csv)


if __name__ == "__main__":
    main()
