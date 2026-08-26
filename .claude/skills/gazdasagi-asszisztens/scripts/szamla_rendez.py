#!/usr/bin/env python3
"""Bejövő számlák sorszámozása, elnevezése és a havi köteg ellenőrzése.

A havi könyvelési mappában a számlák elnevezése:

    {sorszám}_{számla kelte}_{szállító neve}.pdf     pl. 128_2026-07-31_GOOGLE_IRELAND_LIMITED.pdf

A sorszám a számla kelte szerint növekvő, 001-től, a hónapon belül folytonos.

Munkamegosztás: a PDF-ből a szállítót és a keltet kiolvasni ítélet kérdése
(sokféle számlakép, idegen nyelv, dátumformátumok) - azt az agent végzi, és egy
manifest JSON-ba írja. A sorrendezés, sorszámozás, névtisztítás és az ütközések
kiszűrése viszont gépies és hibaérzékeny, ezért az itt van, kódban.

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

# A Drive-on lévő tényleges fájlnevek alapján: ékezet és pont marad, a szóköz
# aláhúzás lesz, a hosszú cégneveket a forrásrendszer ~60 karakternél levágja.
SZALLITO_MAX = 60
FAJLNEV_MINTA = re.compile(
    r"^(?P<sorszam>\d{3})_(?P<datum>\d{4}-\d{2}-\d{2})_(?P<szallito>.+)\.(?P<ext>[Pp][Dd][Ff])$"
)


def tisztit_szallito(nev: str) -> str:
    """Szállítónév fájlnévbe. Ékezetet szándékosan megtartunk."""
    nev = nev.strip()
    nev = re.sub(r"\s+", "_", nev)
    # Ami fájlnévben tilos vagy zavaró; a pont és a vessző maradhat.
    nev = re.sub(r'[/\\:*?"<>|]', "-", nev)
    return nev[:SZALLITO_MAX].rstrip("_")


def uj_nev(sorszam: int, datum: str, szallito: str, ext: str = "pdf") -> str:
    return f"{sorszam:03d}_{datum}_{tisztit_szallito(szallito)}.{ext}"


def _datum_ok(d: str) -> bool:
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", d))


# ------------------------------------------------------------------ átnevezés

def atnevez(manifest_ut, mappa, szimulacio=False, kezdo=1):
    with open(manifest_ut, encoding="utf-8") as f:
        tetelek = json.load(f)
    if isinstance(tetelek, dict):
        tetelek = tetelek.get("szamlak", [])

    hibak = []
    for i, t in enumerate(tetelek):
        for kulcs in ("fajl", "datum", "szallito"):
            if not t.get(kulcs):
                hibak.append(f"[{i}] hiányzó mező: {kulcs}")
        if t.get("datum") and not _datum_ok(t["datum"]):
            hibak.append(f"[{i}] rossz dátumformátum: {t['datum']!r} (kell: ÉÉÉÉ-HH-NN)")
        if t.get("fajl") and not os.path.exists(os.path.join(mappa, t["fajl"])):
            hibak.append(f"[{i}] nincs meg a fájl: {t['fajl']}")
    if hibak:
        sys.exit("A manifest hibás, nem nyúlok a fájlokhoz:\n  " + "\n  ".join(hibak))

    # Kelt szerint növekvő; azonos napon a manifest sorrendje dönt (stabil rendezés).
    tetelek = sorted(tetelek, key=lambda t: t["datum"])

    tervek = []
    for n, t in enumerate(tetelek, start=kezdo):
        ext = os.path.splitext(t["fajl"])[1].lstrip(".") or "pdf"
        tervek.append((t["fajl"], uj_nev(n, t["datum"], t["szallito"], ext)))

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
                "datum": m.group("datum"),
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
        baj.append(f"Kimaradt sorszám: {hianyzo}")
    if min(sorszamok) != 1:
        baj.append(f"A számozás nem 1-gyel kezdődik, hanem {min(sorszamok)}-vel")

    # A sorszámnak a kelt szerint növekvőnek kell lennie.
    rendezett = sorted(tetelek, key=lambda t: t["sorszam"])
    for elozo, kovetkezo in zip(rendezett, rendezett[1:]):
        if kovetkezo["datum"] < elozo["datum"]:
            baj.append(f"Dátumsorrend törik: {elozo['fajl']} után {kovetkezo['fajl']}")
            break

    # Ugyanaz a szállító + ugyanaz a nap többször: lehet jogos (Meta napi számlák),
    # de lehet duplán lementett PDF is - ezért figyelmeztetés, nem hiba.
    parok = Counter((t["szallito"], t["datum"]) for t in tetelek)
    gyanus = [f"{sz} — {d} ({db}×)" for (sz, d), db in parok.items() if db > 1]

    honapok = sorted({t["datum"][:7] for t in tetelek})
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
    print("\nA köteg rendben: folytonos számozás, dátum szerinti sorrend.")
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
            w.writerow(["sorszám", "számla kelte", "szállító", "fájlnév"])
            for t in sorted(tetelek, key=lambda t: t["sorszam"]):
                w.writerow([t["sorszam"], t["datum"], t["szallito"], t["fajl"]])
        print(f"\nCSV kiírva: {csv_ut}")


MANIFEST_MINTA = [
    {"fajl": "letoltott_szamla_1.pdf", "datum": "2026-08-03", "szallito": "GOOGLE IRELAND LIMITED"},
    {"fajl": "meta_aug.pdf", "datum": "2026-08-01", "szallito": "Meta Platforms Ireland Limited"},
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
