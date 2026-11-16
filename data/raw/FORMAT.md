# Raw stop timetables

One file per stop image from https://www.ukmergesautobusai.lt/miesto-marsrutu-failai/
(timetable valid from 2026-10-19). Transcribed by hand, exactly as printed.

```
stop: <name printed on the sign>
source: <image file name>
route <nr> | <headsign as printed>
  <daytype>: H:MM H:MM ...      times may carry footnote marks (*, **, ***)
  note <mark>: <footnote text, verbatim>
  remark: <my own comment about how a cell was read>
```

Times after midnight are written as 24:MM (the sign shows an "00" hour row).
Day types: `workday` = "Darbo dienomis", `weekend` = "Savaitgaliais ir švenčių dienomis",
`saturday` = "Šeštadieniais", `sunday` = "Sekmadieniais".
