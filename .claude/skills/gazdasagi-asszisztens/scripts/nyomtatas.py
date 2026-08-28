#!/usr/bin/env python3
"""A havi könyvelési mappából egyetlen, nyomtatásra kész PDF-et készít.

A gond, amit megold: a mappában 130+ külön fájl van, és ha egyenként nyomtatod,
az sok kattintás; ha viszont mindet egy kötegben küldöd duplexre, a nyomtató a
következő számlát az előző hátoldalára teszi, és a könyvelő két különböző számlát
kap egy lapon.

Ez a szkript összefűzi a fájlokat **a mappa sorrendjében**, és a páratlan oldalszámú
számlák után beszúr egy üres oldalt. Így duplex nyomtatásnál:

- minden számla új lap elején kezdődik,
- a két- és többoldalas számlák két oldalra kerülnek,
- az egyoldalas számla egy lapot kap, üres hátoldallal.

Egyetlen nyomtatási feladat, egyetlen beállítás: **kétoldalas, hosszú él mentén**.

    python3 nyomtatas.py --mappa "Konyveles 2026-07"
    python3 nyomtatas.py --mappa "Konyveles 2026-07" --statisztika   # csak számol
    python3 nyomtatas.py --mappa "Konyveles 2026-07" --tomor         # lásd lentebb

A `--tomor` kapcsoló elhagyja az üres oldalakat: a számlák osztozhatnak egy lapon.
Ez spórol a legtöbbet, de a könyvelőnek adott csomagban egy lap két különböző
számlát tartalmazhat — csak akkor használd, ha ezt vele egyeztetted.

A képként érkezett számlákhoz (jpg, png) Pillow kell: `pip install Pillow`.
Enélkül a szkript kihagyja és felsorolja őket, hogy kézzel pótolhasd.
"""

import argparse
import io
import logging
import math
import os
import re
import sys

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    sys.exit('Hiányzik a pypdf. Telepítsd: pip install pypdf')

try:
    from PIL import Image
    VAN_PILLOW = True
except ImportError:
    VAN_PILLOW = False

# A pypdf a sérült fájlokra a saját loggerén panaszkodik; a hibát mi soroljuk fel
# a végén, összeszedve, ezért a menet közbeni zajt elnyomjuk.
logging.getLogger('pypdf').setLevel(logging.CRITICAL)

PDF_KITERJESZTES = {'.pdf'}
KEP_KITERJESZTES = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tif', '.tiff', '.webp'}

# A4 150 DPI-n. Ez elég a számlaképekhez, és nem fújja fel a fájlt.
DPI = 150
A4_PX = (1240, 1754)
MARGO_PX = 40


def kep_a4_pdf(ut):
    """Képet A4-es PDF-oldalra helyez, fehér háttérrel, arányt tartva."""
    kep = Image.open(ut)
    if kep.mode not in ('RGB', 'L'):
        kep = kep.convert('RGB')
    # A fekvő képek jellemzően oldalra fordított telefonfotók: állóra forgatva
    # jóval nagyobb helyet kapnak a lapon, tehát olvashatóbbak lesznek.
    forgatva = False
    if kep.width > kep.height:
        kep = kep.rotate(90, expand=True)
        forgatva = True

    max_sz = A4_PX[0] - 2 * MARGO_PX
    max_ma = A4_PX[1] - 2 * MARGO_PX
    arany = min(max_sz / kep.width, max_ma / kep.height)
    if arany < 1:
        kep = kep.resize((max(1, int(kep.width * arany)), max(1, int(kep.height * arany))),
                         Image.LANCZOS)

    lap = Image.new('RGB', A4_PX, 'white')
    lap.paste(kep, ((A4_PX[0] - kep.width) // 2, (A4_PX[1] - kep.height) // 2))
    puffer = io.BytesIO()
    lap.save(puffer, 'PDF', resolution=float(DPI))
    puffer.seek(0)
    return PdfReader(puffer), forgatva


def a4_meret(reader):
    """Az első oldal mérete pontban — az üres oldalt ehhez igazítjuk."""
    if len(reader.pages):
        doboz = reader.pages[0].mediabox
        return float(doboz.width), float(doboz.height)
    return 595.276, 841.89


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--mappa', required=True, help='a havi könyvelési mappa')
    ap.add_argument('--kimenet', help='a nyomtatható PDF neve (alapból a mappa neve)')
    ap.add_argument('--tomor', action='store_true',
                    help='üres oldalak nélkül — a számlák osztozhatnak egy lapon')
    ap.add_argument('--statisztika', action='store_true', help='csak számol, nem ír fájlt')
    a = ap.parse_args()

    if not os.path.isdir(a.mappa):
        sys.exit('Nincs ilyen mappa: %s' % a.mappa)

    fajlok = sorted(f for f in os.listdir(a.mappa)
                    if not f.startswith('.') and os.path.isfile(os.path.join(a.mappa, f)))
    if not fajlok:
        sys.exit('A mappa üres.')

    iro = PdfWriter()
    tetelek, kihagyott, forgatottak = [], [], []
    osszes_oldal = 0

    for nev in fajlok:
        ut = os.path.join(a.mappa, nev)
        kit = os.path.splitext(nev)[1].lower()

        if kit in PDF_KITERJESZTES:
            try:
                olvaso = PdfReader(ut)
                # Sok szallitoi szamla tulajdonosi jelszoval van zarva (nyomtatas ellen),
                # felhasznaloi jelszo nelkul. Ezt ures jelszoval fel lehet oldani; ha
                # valodi jelszo kell, az kivetelt dob es a fajl a kihagyottak koze kerul.
                if olvaso.is_encrypted:
                    olvaso.decrypt('')
                oldalak = list(olvaso.pages)
            except Exception as e:
                kihagyott.append((nev, 'olvashatatlan PDF: %s' % e))
                continue
        elif kit in KEP_KITERJESZTES:
            if not VAN_PILLOW:
                kihagyott.append((nev, 'kép, de nincs Pillow telepítve'))
                continue
            try:
                olvaso, forgatva = kep_a4_pdf(ut)
                oldalak = list(olvaso.pages)
                if forgatva:
                    forgatottak.append(nev)
            except Exception as e:
                kihagyott.append((nev, 'feldolgozhatatlan kép: %s' % e))
                continue
        else:
            kihagyott.append((nev, 'nem számlakép (%s)' % (kit or 'kiterjesztés nélkül')))
            continue

        if not oldalak:
            kihagyott.append((nev, 'nulla oldal'))
            continue

        for o in oldalak:
            iro.add_page(o)
        osszes_oldal += len(oldalak)

        # Páratlan oldalszám után üres oldal, hogy a következő számla új lapon kezdődjön.
        if not a.tomor and len(oldalak) % 2 == 1:
            sz, ma = a4_meret(olvaso)
            iro.add_blank_page(width=sz, height=ma)

        tetelek.append((nev, len(oldalak)))

    if not tetelek:
        sys.exit('Egyetlen fájlt sem sikerült feldolgozni.')

    ivek_egyoldalas = osszes_oldal
    ivek_ivhataros = sum(math.ceil(o / 2) for _, o in tetelek)
    ivek_tomor = math.ceil(osszes_oldal / 2)
    tobboldalas = [t for t in tetelek if t[1] > 1]

    print('Mappa:              %s' % a.mappa)
    print('Feldolgozott számla: %d db, összesen %d oldal' % (len(tetelek), osszes_oldal))
    print('Ebből többoldalas:   %d db (%d oldal)'
          % (len(tobboldalas), sum(o for _, o in tobboldalas)))
    print()
    print('Papírigény:')
    print('  egyoldalas nyomtatás            %4d ív' % ivek_egyoldalas)
    print('  kétoldalas, ívhatárral (ez)     %4d ív   (-%d ív, -%d%%)'
          % (ivek_ivhataros, ivek_egyoldalas - ivek_ivhataros,
             round((1 - ivek_ivhataros / ivek_egyoldalas) * 100)))
    print('  kétoldalas, tömören (--tomor)   %4d ív   (-%d ív, -%d%%)'
          % (ivek_tomor, ivek_egyoldalas - ivek_tomor,
             round((1 - ivek_tomor / ivek_egyoldalas) * 100)))

    if tobboldalas:
        print('\nTöbboldalas számlák:')
        for nev, o in tobboldalas:
            print('  %2d oldal  %s' % (o, nev))

    if forgatottak:
        print('\nFekvő képek állóra forgatva (%d db): %s'
              % (len(forgatottak), ', '.join(forgatottak[:5])
                 + (' …' if len(forgatottak) > 5 else '')))

    if kihagyott:
        print('\nKIMARADT %d fájl — ezeket kézzel kell nyomtatni:' % len(kihagyott))
        for nev, ok in kihagyott:
            print('  %s  (%s)' % (nev, ok))

    if a.statisztika:
        print('\n(--statisztika: fájl nem készült)')
        return

    kimenet = a.kimenet or (re.sub(r'[\\/:*?"<>|]', '-', os.path.basename(os.path.abspath(a.mappa)))
                            + (' tomor' if a.tomor else '') + ' nyomtathato.pdf')
    with open(kimenet, 'wb') as f:
        iro.write(f)

    print('\nKész: %s (%d oldal, %.1f MB)'
          % (kimenet, len(iro.pages), os.path.getsize(kimenet) / 1048576))
    print('Nyomtatás: kétoldalas, HOSSZÚ ÉL mentén fordítva, méretezés nélkül (100%).')
    if a.tomor:
        print('FIGYELEM: --tomor módban egy lapra két különböző számla is kerülhet.')


if __name__ == '__main__':
    main()
