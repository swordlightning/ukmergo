"""Stop sequences (patterns) for every route, worked out from the printed
stop timetables (data/raw). A stop key is the raw file name, optionally with
'|<text>' to select only the block whose headsign contains <text>.

Trips are built by walking each pattern in order; a trip may start or end at
any position and may skip positions it does not serve. Patterns of a route
are processed in the order listed, and each printed departure can belong to
only one trip.
"""

R1_IN = ['umega-link-as', 'pramones-link-centro', 'senasis-pastas-link-centro', 'kauno-link-centro',
         'kestucio-a-link-as', 'basanaviciaus', 'kudirkos-link-as', 'anyksciu', 'ligonine-link-as']
R1_OUT_CORE = ['ligonine-link-centro', 'kudirkos-link-centro', 'autoservisas', 'kestucio-a-link-pienines',
               'kauno', 'senasis-pastas', 'pramones']

R2_LOOP_TO_BIO = ['pusu-link-centro', 'pivonijos-link-centro', 'smeliu-link-centro', 'kestucio-a-link-pienines',
                  'kauno', 'senasis-pastas', 'pramones', 'ziedo-link-narbuto', 'lytagros-centras-link-biofabriko',
                  'statikai-pries-biofabrika-link-deltuvos', 'biofabrikas-link-deltuvos',
                  'statikai-uz-biofabriko-link-deltuvos', 'sodai-link-deltuvos', 'deltuvos-kapines-link-deltuvos']
R2_FROM_BIO = ['biofabrikas-link-centro', 'statikai-uz-biofabriko-link-as', 'lytagros-centras-link-as',
               'ziedo-link-as', 'pramones-link-centro', 'senasis-pastas-link-centro', 'kauno-link-centro',
               'kestucio-a-link-as']
AS_OUT = ['as', 'as-vytauto-g-link-dukstynos', 'sodai-link-dukstynos', 'dukstynos-kaimas-link-dukstynos']
EAST_IN = ['zaliasis-vienkiemis', 'saltalankiu-link-centro', 'kreksliai-link-centro', 'vysniu-link-centro',
           'boruvka-link-centro']
EAST_OUT_WE = ['antakalnio-link-zaliojo-vnk', 'gelzbetonis-link-zaliojo-vnk', 'boruvka-link-zaliojo-vnk',
               'vysniu-9link-zaliojo-vnk', 'kreksliai-link-zaliojo-vnk', 'saltalankiu-link-zaliojo-vnk']
TO_AS_VIA_MUZIEJUS = ['muziejus-link-as', 'basanaviciaus', 'kudirkos-link-as', 'anyksciu', 'ligonine-link-as']
PASILE_IN = ['pasile', 'baznycios', 'pasiles-kryzkele', 'misku']
PASILE_OUT = ['misku-link-pasiles', 'pasiles-kryzkele-link-pasiles', 'baznycios-link-pasiles']

PATTERNS = {
    '1': [
        ('narbuto', ['narbuto'] + R1_IN[1:]),
        ('pienine', ['pienine'] + R1_IN + ['as-vytauto-g-link-dukstynos', 'sodai-link-dukstynos',
                                            'dukstynos-kaimas-link-dukstynos']),
        ('dukstyna', ['dukstyna', 'dukstyvos-kaimas-link-centro', 'sodai-link-centro', 'as-vytauto-g-link-centro']
                     + R1_OUT_CORE + ['umega-link-pienines']),
        ('as', ['as'] + R1_OUT_CORE + ['umega-link-pienines']),
    ],
    '2': [
        ('pasile', PASILE_IN + R2_LOOP_TO_BIO),
        ('kokliu', ['kokliu'] + R2_LOOP_TO_BIO),
        ('deltuva', ['deltuva', 'deltuvos-kapines-link-centro', 'sodai-link-as', 'statikai-link-as'] + R2_FROM_BIO
                    + ['basanaviciaus', 'kudirkos-link-as', 'anyksciu', 'ligonine-link-as'] + AS_OUT
                    + EAST_IN + ['gelzbetonis-dariaus-ir-gireno', 'pusu|Koklių']),
        # weekends: after Kęstučio a. the bus turns to Muziejus and runs to Pušų / Pašilė
        ('weekend-east', R2_FROM_BIO + ['muziejus', 'smeliu', 'pivonijos', 'pusu|Pašilė']
                         + ['pasiles-kryzkele-link-pasiles', 'baznycios-link-pasiles']),
    ],
    '3': [
        ('to-zaliasis', ['turgus', 'kestucio-a-link-as', 'muziejus'] + EAST_OUT_WE),
        ('to-turgus', EAST_IN + ['gelzbetonis-link-centro', 'antakalnio-link-centro', 'muziejus-link-as',
                                 'kestucio-a-link-as', 'misku-link-pasiles']),
    ],
    '4': [
        ('out-workday', AS_OUT + ['dukstyna', 'zaliasis-vienkiemis', 'saltalankiu-link-centro',
                                  'kreksliai-link-centro', 'vysniu-link-centro', 'boruvka-link-centro',
                                  'gelzbetonis-link-centro', 'antakalnio-link-centro', 'smeliu', 'pivonijos',
                                  'pusu'] + PASILE_OUT),
        ('out-weekend', ['as', 'ligonine-link-centro', 'kudirkos-link-centro', 'autoservisas', 'muziejus',
                         'smeliu', 'pivonijos', 'pusu'] + PASILE_OUT),
        ('in-varine', ['varine', 'pasile-is-varines'] + PASILE_IN + ['pusu-link-centro',
                       'pivonijos-link-centro', 'smeliu-link-centro'] + TO_AS_VIA_MUZIEJUS),
        ('in', PASILE_IN + ['pusu-link-centro', 'pivonijos-link-centro', 'smeliu-link-centro']
               + TO_AS_VIA_MUZIEJUS),
    ],
    '5': [
        ('to-pasile', ['narbuto', 'pramones-link-centro', 'senasis-pastas-link-centro', 'kauno-link-centro',
                       'kestucio-a-link-as', 'basanaviciaus', 'kudirkos-link-as', 'anyksciu', 'ligonine-link-as']
                      + AS_OUT + EAST_IN + ['gelzbetonis-link-centro', 'antakalnio-link-centro', 'smeliu',
                                            'linu-link-gamyklu|Pašilė', 'geliu-link-gamyklu|Pašilė',
                                            'gamyklu|Pašilė', 'geliu-link-pivonijos|Pašilė',
                                            'linu-link-pivonijos|Pašilė', 'pivonijos', 'pusu'] + PASILE_OUT),
        ('to-narbuto', PASILE_IN + ['pusu-link-centro', 'pivonijos-link-centro', 'linu-link-gamyklu|Narbuto',
                                    'geliu-link-gamyklu|Narbuto', 'gamyklu|Narbuto', 'geliu-link-pivonijos|Narbuto',
                                    'linu-link-pivonijos|Narbuto', 'smeliu-link-centro', 'kestucio-a-link-pienines',
                                    'kauno', 'senasis-pastas', 'pramones', 'ziedo-link-narbuto']),
    ],
    '6': [
        ('out-workday', AS_OUT),
        ('out-weekend', ['dukstyna', 'dukstyvos-kaimas-link-centro', 'sodai-link-centro', 'as-vytauto-g-link-centro',
                         'as', 'ligonine-link-centro', 'kudirkos-link-centro', 'autoservisas', 'muziejus']
                        + EAST_OUT_WE),
        ('in', EAST_IN + ['gelzbetonis-link-centro', 'antakalnio-link-centro'] + TO_AS_VIA_MUZIEJUS
               + ['as-vytauto-g-link-dukstynos|Dukstyna', 'sodai-link-dukstynos|Dukstyna',
                  'dukstynos-kaimas-link-dukstynos|Dukstyna']),
    ],
    '7': [
        ('narbuto', AS_OUT + EAST_IN + ['gelzbetonis-link-centro', 'antakalnio-link-centro'] + TO_AS_VIA_MUZIEJUS
                    + ['ligonine-link-centro', 'kudirkos-link-centro', 'autoservisas', 'kestucio-a-link-pienines',
                       'kauno', 'senasis-pastas', 'pramones', 'ziedo-link-narbuto']),
    ],
}

# Departures printed at the main bus-station sign (as.jpg) that the sign itself
# says leave from the Vytauto g. stop: they are the same departures as the ones
# printed on the Vytauto g. sign, so they are not separate trips.
AS_FROM_VYTAUTO_NOTE = 'važiuoja iš Vytauto g.'

# Patterns that only apply on some day types (default: all day types).
PATTERN_DAYS = {
    ('2', 'deltuva'): ['workday'],
    ('2', 'weekend-east'): ['weekend'],
    ('4', 'out-workday'): ['workday'],
    ('4', 'out-weekend'): ['weekend'],
    ('6', 'out-workday'): ['workday'],
    ('6', 'out-weekend'): ['weekend'],
}
