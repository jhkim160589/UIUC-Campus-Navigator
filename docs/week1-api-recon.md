# Week 1 — UIUC Course API Recon

**Date probed:** 2026-09-17
**Verdict:** API is live, public, no authentication. Week 1 risk #1 (data acquisition) is cleared.

---

## 1. Endpoint shape

Base: `https://courses.illinois.edu/cisapp/explorer/schedule`

The API is a hierarchy of XML documents, each level linking to the next:

| Level | URL | Returns |
|---|---|---|
| Years | `/schedule.xml` | 2004–2027 |
| Terms | `/schedule/2026.xml` | winter / spring / summer / fall |
| Subjects | `/schedule/2026/fall.xml` | **186 subjects** (CS, ECE, MATH, …) |
| Courses | `/schedule/2026/fall/CS.xml` | **97 course refs** (id + href only) |
| Sections | `/schedule/2026/fall/CS/225.xml` | section refs (id + href only) |
| Section | `/schedule/2026/fall/CS/225/35926.xml` | full section incl. meetings |

Status 200, `Content-Type: application/xml`, no API key.

## 2. The `?mode=detail` shortcut — use this

`/schedule/2026/fall/CS/225.xml?mode=detail` replaces the `<sections>` ref list with
`<detailedSections>`, expanding **every section and its meetings inline**.

One request per course instead of one request per section.
For CS 225 that is 1 request instead of 13.

`?mode=cascade` returns byte-identical output. Either works.

**It does not cascade at the subject level.** `/2026/fall/CS.xml?mode=detail` still returns
only the 97 course refs. So the ingest path is fixed:

```
subject listing  ->  per-course ?mode=detail
```

**Measured throughput:** 48 courses in 11.5s = **0.24 s/course** (with a 0.15s politeness sleep).
CS+ECE+MATH+PHYS is ~331 courses ≈ 80 s for a full pull. Cheap.

## 3. What a meeting actually looks like

```xml
<detailedSection id="35926">
  <sectionNumber>ABC</sectionNumber>
  <statusCode>A</statusCode>
  <partOfTerm>1</partOfTerm>
  <startDate>08-24-26Z</startDate>
  <endDate>12-09-26Z</endDate>
  <meetings>
    <meeting id="0">
      <start>11:00AM</start>
      <end>12:50PM</end>
      <daysOfTheWeek>R</daysOfTheWeek>
      <roomNumber>4025</roomNumber>
      <buildingName>Campus Instructional Facility</buildingName>
      <type code="LBD">Laboratory-Discussion</type>
      <instructors>
        <instructor lastName="Solomon" firstName="B">Solomon, B</instructor>
      </instructors>
    </meeting>
  </meetings>
</detailedSection>
```

Everything the router needs — time, day, building — is here. Nothing else has to be scraped.

## 4. Confirmed: one section CAN have multiple meetings

Sample of 48 courses: **804 sections, 807 meetings**.

Almost every section has exactly one meeting, but not all. The 1-to-many
section→meeting relationship is real, just rare. A schema that collapses meeting
into section will silently drop rows.

## 5. Dirty data found in the sample — decide how to handle before designing tables

35 distinct building names appeared across only 48 courses.

**Not a real campus location:**

| Value | Count | What it is |
|---|---|---|
| `n.a.` | 17 | no location assigned |
| `Location Pending` | 10 | room not yet assigned |
| `200 S Wacker` | 2 | Chicago — not Urbana campus |
| `1203 1/2 W Nevada` | 5 | street address, not a named building |

Meeting `type` codes `ONL` (6) and `OLC` (4) are online — no physical location by definition.

**HTML entities are NOT decoded by the API:**
`Electrical &amp; Computer Eng Bldg`, `Materials Science &amp; Eng Bld`,
`Literatures, Cultures, &amp; Ling`. These must be unescaped before they are
stored or sent to a geocoder.

**Names are abbreviated and inconsistent:** `Bldg` / `Bld` / `Building` all appear.
Geocoding `Materials Science & Eng Bld` verbatim is unlikely to resolve well —
plan on appending `, Urbana, IL` and spot-checking results by hand.

**`daysOfTheWeek` can also be `n.a.`** (19 of 807).

## 6. `daysOfTheWeek` encoding

A compact string, one char per day. **`R` = Thursday**, `T` = Tuesday.

Observed values and frequency:

```
R 177   F 150   W 118   T 110   TR 105   M 34   WF 33
MW 27   MWF 24  n.a. 19  MTWF 8  MF 1     MTWR 1
```

Note `TR` and `MWF` are single values covering multiple days — a meeting row
with `daysOfTheWeek = "MWF"` is three calendar events. Whether you expand this
at ingest time or at query time is a schema decision.

## 7. Meeting type codes observed

```
DIS 407   LAB 174   LBD 112   LEC 77   LCD 14
ONL 6     OLC 4     IND 3     CNF 1
E3 E4 E5 E6 E7 E10 E12 L2 L3  (1 each — exam/lab overflow codes)
```

## 8. Building shortlist

Top buildings by meeting count in the CS/ECE/MATH/PHYS sample — these are
the ones worth geocoding first. The brief caps the graph at 20–30 buildings;
this sample says the head of the distribution is short, which supports that cap.

```
186  Campus Instructional Facility
160  Loomis Laboratory
 94  Electrical & Computer Eng Bldg
 41  David Kinley Hall
 40  Davenport Hall
 28  Sidney Lu Mech Engr Bldg
 28  Siebel Center for Comp Sci
 22  Everitt Laboratory
 22  Engineering Hall
 21  Henry Administration Bldg
 20  Armory
 19  Gregory Hall
 16  Literatures, Cultures, & Ling
 11  English Building
  9  Materials Science & Eng Bld
  9  Wohlers Hall
  7  Noyes Laboratory
  7  Lincoln Hall
```

## 9. Open decisions (Week 1, still yours)

- [ ] Schema: how to model `daysOfTheWeek` — expand to one row per day, or store the string?
- [ ] Schema: where do unlocatable meetings (`n.a.`, `Location Pending`, `ONL`) go —
      filtered at ingest, or stored with a null building FK?
- [ ] Which subjects to ingest. CS+ECE+MATH+PHYS covers your own schedule; more is optional.
- [ ] Map library: Leaflet vs Google Maps JS.
- [ ] Building coordinates: Google Geocoding on these names, or hand-place 20–30 buildings?
      Hand-placing 25 buildings is ~30 minutes and gives exact door locations, which
      matters for the Week 5 Directions comparison.
