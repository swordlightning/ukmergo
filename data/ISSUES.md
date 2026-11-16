# Tvarkaraščių klaidos ir neaiškumai

Šaltinis: 80 stotelių tvarkaraščių (įsigalioja nuo **2026-10-19**),
https://www.ukmergesautobusai.lt/miesto-marsrutu-failai/

Visi laikai perrašyti ranka į `data/raw/*.txt` tiksliai taip, kaip atspausdinta.
Po to programa (`tools/build_trips.py`) sujungė gretimų stotelių laikus į reisus.
Jei vienos stotelės laikas „netelpa“ tarp kaimyninių stotelių, jis pažymimas čia.

## 1. Pataisytos akivaizdžios spausdinimo klaidos (13)

Taisyta tik tada, kai **bent dvi** gretimos to paties autobuso stotelės rodo tą patį.
`timetable.json` reisuose tokie laikai turi lauką `"corrected": {stotelė: atspausdintas_laikas}`.

| Maršr. | Stotelė | Atspausdinta | Pataisyta | Įrodymas |
|---|---|---|---|---|
| 4 | Krekšliai (į Pašilę) | 17:08 | 17:03 | Šaltalankių 17:02, Vyšnių 17:04, Boruvka 17:06 |
| 6 | Šaltalankių | 8:12 | 8:02 | Žaliasis vnk. 8:00, Krekšliai 8:03, Vyšnių 8:04 |
| 6 | Šaltalankių | 15:17 | 15:27 | Žaliasis vnk. 15:25, Krekšliai 15:28, Vyšnių 15:29 |
| 6 | Šaltalankių | 16:32 | 16:02 | Žaliasis vnk. 16:00, Krekšliai 16:03, Vyšnių 16:04 |
| 2 | Žaliasis vienkiemis | 20:05 | 21:05 | Dukstynos k. 21:00, Šaltalankių 21:07, Krekšliai 21:09 |
| 2 | Anykščių | 5:18 | 4:54 | Kudirkos 4:53, Ligoninė 4:56 |
| 2 | Anykščių | 21:13 | 20:53 | Kudirkos 20:52, Ligoninė 20:55 |
| 2 | Kudirkos (į AS) | 5:37 | 6:37 | Basanavičiaus 6:35, Anykščių 6:38, Ligoninė 6:40 |
| 4 | Bažnyčios (į AS) | 6:27 | 6:21 | Pašilė 6:19, Miškų 6:24 ir dar 9 tolesnės stotelės |
| 4 | Pašilės kryžkelė (į AS) | 6:28 | 6:22 | tas pats reisas |
| 4 | Pivonijos (į Pašilę) | 5:07 | 5:09 | Smėlių 5:07, Pušų 5:10; visi kiti reisai :09 / :39 |
| 5 | Pivonijos (į Narbuto) | 0:08 | 0:11 | Miškų 0:09, Pušų 0:10, Smėlių 0:12 |
| 2 | Kęstučio a. (į Pieninę) | 21:48 | 21:53 | Smėlių 21:47 (+6 kaip visada), Kauno 21:55 |
| 2 | Koklių | 20:18* | 20:08 | Pušų 20:09, Pivonijos 20:11, Smėlių 20:12; žvaigždutė („iki Deltuvos“) pašalinta – vakare į Deltuvą reisų nėra |

## 2. Neišspręsta – reikia paklausti vežėjo (laikai palikti kaip atspausdinti)

1. **Pirmas 1 maršruto reisas (darbo d.)**: AS 4:15 → Ligoninė 4:17 → Kudirkos 4:19 → Autoservisas 4:21 →
   Kęstučio a. 4:25, bet Kauno **4:52**, Senasis paštas **4:54**, Pramonės **4:56** (turėtų būti ~4:27–4:30).
   Be to, 2 maršruto autobusas iš Biofabriko išvyksta jau 4:36. JSON'e tai du atskiri reisų fragmentai.
2. **Paryčių 2 maršrutas**: Žiedo (į Narbuto) 4:57, Statikai (už Biofabriko) 5:02, Lytagros centras 5:03 –
   neaišku, kuriam autobusui priklauso.
3. **2 maršr., AS (Vytauto g.)** 4:45 ir 5:22 – kitose stotelėse jų tęsinio nėra.
4. **2 maršr., Koklių** 5:43* ir 21:38** – tuo pat metu tas autobusas jau rodomas kelyje iš Pašilės
   (Miškų 5:43 / 21:43). Vienas iš jų klaidingas.
5. **2 maršr., Pušų 8:54 → Pivonijos 9:01** – 7 min. vietoj 1–2 min. Reisas sujungtas, laikai palikti.
6. **4 maršr., Dukstynos k. 9:53 → Žaliasis vnk. 10:05** – 12 min. vietoj 7. Sujungta, laikai palikti.
7. **4 maršr., Varinė 17:29** – Pašilėje (nuo Varinės) toliau išvyksta tik 17:40.
8. **6 maršr., AS 13:25** (darbo d.) – nėra Vytauto g. ir kitose stotelėse; panašu, kad tai 7 maršruto 13:25.
9. **1 maršr., Kudirkos 9:15*** (į AS) – kitose stotelėse tokio reiso nėra.
10. **1 maršr., Pramonės 14:39** (savaitgaliais, į AS) – Kauno stotelėje tęsinio nėra.
11. **2 maršr. savaitgaliais**: Muziejus 7:10 ir 11:50, Smėlių 7:34, Turgus 9:40 – neaišku, kaip važiuoja.
    Savaitgalio 2 maršruto kelias (Kęstučio a. → Muziejus → Smėlių → Pivonijos → Pušų → Pašilė / Koklių)
    nustatytas tik iš laikų – reikia patvirtinimo.
12. **3 maršr., Muziejus 7:35** (šeštadienį) – kitose stotelėse to reiso nėra.
13. **Išnašos**: Smėlių stotelėje (4 maršr.) visos žvaigždutės paaiškintos „važiuoja iki Koklių“, nors darbo
    dienomis jos turėtų reikšti „iki Varinės“ (taip rašo visos kaimyninės stotelės). Kęstučio a. 9:43* (3 maršr.)
    žvaigždutė be paaiškinimo – pagal Miškų stotelę šis reisas važiuoja į Pašilę.
14. **AS stotelėje**: 1 maršr. 14:45* („iš Vytauto g.“), o Vytauto g. lentelėje – 14:50.
    Tolesnės stotelės patvirtina 14:50.

Iš viso 13 atspausdintų laikų (iš 3399) nepavyko priskirti jokiam reisui – jie nėra `timetable.json`.

## 3. Ko trūksta programėlei

* **Stotelių koordinatės.** Tik 19 iš 43 stotelių rasta oficialiame GTFS faile (pagal pavadinimą, todėl
  reikia patikrinti žemėlapyje). Kitoms 24 (Pušų, Pivonijos, Smėlių, Žaliasis vienkiemis, Pašilė, Sodai...)
  koordinačių nėra. Abi gatvės pusės (pvz. „Kauno“ į centrą ir į Pieninę) kol kas turi vieną bendrą tašką.
* **Šventinės dienos** `calendar.holidays` surašytos iš atminties (2026-12 – 2027-12) – patikrinti.
* Galutinės stotelės atvykimo laikas lentelėse nespausdinamas (pvz. atvykimas į Pieninę), todėl reisas
  JSON'e baigiasi paskutine stotele, kurioje laikas atspausdintas.
