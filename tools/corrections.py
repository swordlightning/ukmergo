"""Printed times that are provably misprinted.

Key: (stop file, route, day type, printed minutes since midnight)
Value: corrected minutes since midnight.
Every entry lists the neighbouring stops that prove it; see data/ISSUES.md.
"""
def m(hhmm):
    h, mi = hhmm.split(':')
    return int(h) * 60 + int(mi)

CORRECTIONS = {}

# (stop file, route, day, printed) -> corrected.  Evidence = neighbouring stops of the same bus.
CORRECTIONS.update({
    # Krekšliai: Šaltalankių 17:02, Vyšnių 17:04, Boruvka 17:06 -> 17:03
    ('kreksliai-link-centro', '4', 'workday', m('17:08')): m('17:03'),
    # Šaltalankių: Žaliasis vnk. 8:00/15:25/16:00, Krekšliai 8:03/15:28/16:03, Vyšnių 8:04/15:29/16:04
    ('saltalankiu-link-centro', '6', 'workday', m('8:12')): m('8:02'),
    ('saltalankiu-link-centro', '6', 'workday', m('15:17')): m('15:27'),
    ('saltalankiu-link-centro', '6', 'workday', m('16:32')): m('16:02'),
    # Žaliasis vienkiemis: Dukstynos kaimas 21:00, Šaltalankių 21:07, Krekšliai 21:09 (printed in the 20 h row)
    ('zaliasis-vienkiemis', '2', 'workday', m('20:05')): m('21:05'),
    # Anykščių: Kudirkos 4:53 / 20:52 and Ligoninė 4:56 / 20:55
    ('anyksciu', '2', 'workday', m('5:18')): m('4:54'),
    ('anyksciu', '2', 'workday', m('21:13')): m('20:53'),
    # Kudirkos: Basanavičiaus 6:35, Anykščių 6:38, Ligoninė 6:40 (printed in the 5 h row)
    ('kudirkos-link-as', '2', 'workday', m('5:37')): m('6:37'),
    # Bažnyčios / Pašilės kryžkelė: Pašilė 6:19, Miškų 6:24, Pušų 6:25 ... (9 later stops agree)
    ('baznycios', '4', 'workday', m('6:27')): m('6:21'),
    ('pasiles-kryzkele', '4', 'workday', m('6:28')): m('6:22'),
    # Pivonijos (route 4 to Pašilė): Smėlių 5:07, Pušų 5:10; every other trip is :09 / :39
    ('pivonijos', '4', 'workday', m('5:07')): m('5:09'),
    # Pivonijos (route 5 night): Pašilės kr. 24:08, Miškų 24:09, Pušų 24:10, Smėlių 24:12
    ('pivonijos-link-centro', '5', 'workday', m('24:08')): m('24:11'),
    # Kęstučio a. (route 2 night): Smėlių 21:47 (+6 as on every other trip) and Kauno 21:55 (-2)
    ('kestucio-a-link-pienines', '2', 'workday', m('21:48')): m('21:53'),
    # Koklių: Pušų 20:09, Pivonijos 20:11, Smėlių 20:12, Kęstučio a. 20:18 (printed equal to Kęstučio)
    ('kokliu', '2', 'workday', m('20:18')): m('20:08'),
})

# Two printed departures that belong to the same bus even though the running
# time between them is unusual (the bus evidently waits). Times are kept as printed.
FORCED_LINKS = {
    # route 4: Dukstynos kaimas 9:53 -> Žaliasis vnk. 10:05 (all other trips: 7 min, this one 12)
    ('4', 'workday', 'dukstynos-kaimas-link-dukstynos', m('9:53')): ('zaliasis-vienkiemis', m('10:05')),
    # route 2: Pušų 8:54 -> Pivonijos 9:01 (only bus between 7:4x and 10:1x)
    ('2', 'workday', 'pusu-link-centro', m('8:54')): ('pivonijos-link-centro', m('9:01')),
    # route 5 night bus skips the Linų / Gėlių / Gamyklų loop: Pivonijos 24:11 -> Smėlių 24:12
    ('5', 'workday', 'pivonijos-link-centro', m('24:11')): ('smeliu-link-centro', m('24:12')),
    # route 5 first bus skips Gelžbetonis..Pivonijos: Boruvka 5:01 -> Pušų 5:05
    ('5', 'workday', 'boruvka-link-centro', m('5:01')): ('pusu', m('5:05')),
}

# Corrections that also remove a footnote mark that cannot apply.
DROP_MARK = {
    ('kokliu', '2', 'workday', m('20:08')),  # "iki Deltuvos": no evening trip goes to Deltuva
}

# Printed departures whose trip is doubtful (data/ISSUES.md, section 2). Trips that
# contain one of them are marked "uncertain" and shown with (?) in the app.
UNCERTAIN = {
    ('as', '1', 'workday', m('4:15')): 'Pirmo reiso laikai nesutampa: Kęstučio a. 4:25, bet Kauno 4:52 (lentelėse).',
    ('kauno', '1', 'workday', m('4:52')): 'Pirmo reiso laikai nesutampa: Kęstučio a. 4:25, bet Kauno 4:52 (lentelėse).',
    ('statikai-uz-biofabriko-link-as', '2', 'workday', m('5:02')): 'Neaišku, kuriam autobusui priklauso šie paryčių laikai.',
    ('dukstynos-kaimas-link-dukstynos', '4', 'workday', m('9:53')): 'Tarp Dukstynos kaimo 9:53 ir Žaliojo vnk. 10:05 – 12 min. vietoj įprastų 7.',
    ('pusu-link-centro', '2', 'workday', m('8:54')): 'Tarp Pušų 8:54 ir Pivonijos 9:01 – 7 min. vietoj įprastų 1–2.',
    ('varine', '4', 'workday', m('17:29')): 'Iš Varinės 17:29 – Pašilėje toliau išvyksta tik 17:40.',
    ('as-vytauto-g-link-dukstynos', '4', 'workday', m('4:45')): 'Lentelėse 4:45 išvykimas pažymėtas ir kaip Nr. 4, ir kaip Nr. 5.',
    ('as-vytauto-g-link-dukstynos', '5', 'workday', m('4:45')): 'Lentelėse 4:45 išvykimas pažymėtas ir kaip Nr. 4, ir kaip Nr. 5.',
    ('dukstyna', '1', 'workday', m('14:45')): 'AS lentelėje šis reisas – 14:45, Vytauto g. ir kitose – 14:50.',
}
# All weekend trips of route 2: the route on weekends was worked out from times only.
UNCERTAIN_PATTERN_DAYS = {('2', 'weekend'): 'Savaitgalio 2 maršruto kelias nustatytas tik iš laikų – nepatvirtintas.'}
