#!/usr/bin/env python3
"""Szám -> magyar betűs alak, a TIG-eken használt helyesírás szerint.

Miért van erre külön modul: a TIG-en az összeg betűvel kiírva is szerepel, és ez az
a mező, amit kézzel a legkönnyebb elrontani. A Drive-on lévő korábbi TIG-ek között
van is elgépelés ("kétezer-nyolcszásznyolcvan"), ami pont azt mutatja, hogy ezt
nem érdemes fejben csinálni.

A két szabály, ami számít:

1. Kötőjel: 2000-ig egybeírjuk ("ezerkilencszázkilencvenkilenc"), 2000 fölött
   viszont a hármas számcsoportok határán kötőjel jön ("kétezer-egy",
   "nyolcszázkilencezer-kilencszáznyolcvanöt"). A kerek 2000 még egybe: "kétezer".

2. A 2 szorzóként "két", önállóan "kettő": 2 -> "kettő", de 2000 -> "kétezer",
   200 -> "kétszáz", 32 -> "harminckettő".

Használat:
    from szamnev import szamnev
    szamnev(809985)  -> 'nyolcszázkilencezer-kilencszáznyolcvanöt'

    python3 szamnev.py 809985
"""

EGYESEK = ["", "egy", "kettő", "három", "négy", "öt", "hat", "hét", "nyolc", "kilenc"]
# Szorzós alak: a 2 ilyenkor "két" (kétszáz, kétezer), a többi változatlan.
EGYESEK_SZORZO = ["", "egy", "két", "három", "négy", "öt", "hat", "hét", "nyolc", "kilenc"]
TIZESEK = ["", "tizen", "huszon", "harminc", "negyven", "ötven",
           "hatvan", "hetven", "nyolcvan", "kilencven"]

# 10 és 20 önmagában "tíz"/"húsz", összetételben "tizen"/"huszon" - ezért külön.
KEREK_TIZ = {1: "tíz", 2: "húsz"}

NAGYSAGRENDEK = [
    (10**9, "milliárd"),
    (10**6, "millió"),
    (10**3, "ezer"),
]


def _szazon_beluli(n: int) -> str:
    """1..999 közötti szám egybeírt alakja."""
    if n == 0:
        return ""
    out = ""
    szaz, maradek = divmod(n, 100)
    if szaz:
        # 100 = "száz", nem "egyszáz"
        out += ("" if szaz == 1 else EGYESEK_SZORZO[szaz]) + "száz"
    if maradek:
        tiz, egy = divmod(maradek, 10)
        if tiz:
            if egy == 0 and tiz in KEREK_TIZ:
                out += KEREK_TIZ[tiz]
            else:
                out += TIZESEK[tiz]
        out += EGYESEK[egy]
    return out


def _csoport(ertek: int, egyseg: str) -> str:
    """Egy hármas csoport szava, pl. (809, 'ezer') -> 'nyolcszázkilencezer'."""
    if ertek == 0:
        return ""
    if egyseg == "":
        return _szazon_beluli(ertek)
    if egyseg == "ezer" and ertek == 1:
        # 1000 = "ezer", nem "egyezer"
        return "ezer"
    # Millió/milliárd elé viszont kell az "egy": "egymillió".
    if ertek == 1:
        return "egy" + egyseg
    if ertek == 2:
        return "két" + egyseg
    return _szazon_beluli(ertek) + egyseg


def szamnev(n: int) -> str:
    """Egész szám magyar betűs alakja, TIG-en használható helyesírással.

    >>> szamnev(809985)
    'nyolcszázkilencezer-kilencszáznyolcvanöt'
    >>> szamnev(2000)
    'kétezer'
    >>> szamnev(2001)
    'kétezer-egy'
    """
    if not isinstance(n, int):
        raise TypeError(f"egész számot vártam, ez jött: {n!r}")
    if n < 0:
        return "mínusz " + szamnev(-n)
    if n == 0:
        return "nulla"
    if n == 2:
        return "kettő"  # önállóan "kettő", nem "két"

    csoportok = []  # (érték, egység) párok a legnagyobbtól
    maradek = n
    for oszto, egyseg in NAGYSAGRENDEK:
        ertek, maradek = divmod(maradek, oszto)
        if ertek:
            csoportok.append((ertek, egyseg))
    if maradek:
        csoportok.append((maradek, ""))

    szavak = [_csoport(ertek, egyseg) for ertek, egyseg in csoportok]

    # 2000-ig egybe, fölötte a csoporthatárokon kötőjel.
    if n <= 2000:
        return "".join(szavak)
    return "-".join(sz for sz in szavak if sz)


def penz_szoveg(osszeg: int, penznem: str = "forint") -> str:
    """A TIG-en szereplő 'azaz ...' rész, pl. 'nyolcszázkilencezer-... forint'."""
    return f"{szamnev(osszeg)} {penznem}"


def ezres(osszeg: int) -> str:
    """Számjegyes alak ezres tagolással, ahogy a TIG-en áll: '809 985'.

    Sima szóközt használ, nem NBSP-t, mert a Word-sablonokban is az van.
    """
    return f"{osszeg:,}".replace(",", " ")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            n = int(arg.replace(" ", "").replace(".", "").replace(",", ""))
            print(f"{ezres(n)} -> {szamnev(n)}")
    else:
        # Önteszt a Drive-on talált valódi TIG-ek alapján.
        esetek = {
            809985: "nyolcszázkilencezer-kilencszáznyolcvanöt",
            490423: "négyszázkilencvenezer-négyszázhuszonhárom",
            103500: "százháromezer-ötszáz",
            37856: "harminchétezer-nyolcszázötvenhat",
            2880: "kétezer-nyolcszáznyolcvan",
            738000: "hétszázharmincnyolcezer",
            288000: "kétszáznyolcvannyolcezer",
            0: "nulla",
            1: "egy",
            2: "kettő",
            10: "tíz",
            20: "húsz",
            21: "huszonegy",
            100: "száz",
            101: "százegy",
            200: "kétszáz",
            1000: "ezer",
            1500: "ezerötszáz",
            2000: "kétezer",
            2001: "kétezer-egy",
            1999: "ezerkilencszázkilencvenkilenc",
            1000000: "egymillió",
            1234567: "egymillió-kétszázharmincnégyezer-ötszázhatvanhét",
        }
        hiba = 0
        for n, vart in esetek.items():
            kapott = szamnev(n)
            jel = "ok " if kapott == vart else "HIBA"
            if kapott != vart:
                hiba += 1
                print(f"{jel} {n:>10} -> {kapott!r}  (várt: {vart!r})")
            else:
                print(f"{jel} {n:>10} -> {kapott}")
        print(f"\n{len(esetek) - hiba}/{len(esetek)} rendben")
        sys.exit(1 if hiba else 0)
