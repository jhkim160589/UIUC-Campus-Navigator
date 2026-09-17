"""XML -> Python objects for the UIUC CIS API.

This module is deliberately dumb. It decodes what the API sent and nothing more.
It does NOT decide what to keep, how to normalize building names, or how to lay
out tables - those are schema decisions and they are yours.

What it does handle, because these are facts about the feed rather than design
choices (see docs/week1-api-recon.md):
  - the API does not decode HTML entities, so 'Eng &amp; Sci' arrives escaped
  - 'R' means Thursday
  - absent values arrive as the literal string 'n.a.'
"""

from dataclasses import dataclass, field
from datetime import time as Time
from html import unescape
from xml.etree import ElementTree as ET

NS = {"ns2": "http://rest.cis.illinois.edu"}

# Literal strings the API uses for "no value". Not errors - they are in the feed.
NULL_SENTINELS = frozenset({"n.a.", "N.A.", ""})

# buildingName values seen that are not a locatable Urbana campus building.
# Filtering policy is a schema decision - this is exposed, not applied.
NON_BUILDING_VALUES = frozenset({"Location Pending", "ARRANGED"})

# Meeting type codes with no physical location by definition.
ONLINE_TYPE_CODES = frozenset({"ONL", "OLC"})

# daysOfTheWeek is one character per day. R is Thursday, T is Tuesday.
DAY_CODES = {
    "M": "Monday",
    "T": "Tuesday",
    "W": "Wednesday",
    "R": "Thursday",
    "F": "Friday",
    "S": "Saturday",
    "U": "Sunday",
}


@dataclass
class Meeting:
    meeting_id: str
    start: Time | None
    end: Time | None
    days_raw: str | None          # e.g. "MWF", "TR", or None when 'n.a.'
    room_number: str | None
    building_name: str | None     # entity-decoded; may still be 'Location Pending'
    type_code: str | None         # DIS, LAB, LEC, LBD, ONL, ...
    type_label: str | None
    instructors: list[str] = field(default_factory=list)

    @property
    def days(self) -> list[str]:
        """['Monday', 'Wednesday', 'Friday'] for days_raw == 'MWF'. [] if unknown."""
        if not self.days_raw:
            return []
        return [DAY_CODES[c] for c in self.days_raw if c in DAY_CODES]

    @property
    def is_online(self) -> bool:
        return self.type_code in ONLINE_TYPE_CODES

    @property
    def has_location(self) -> bool:
        """True if building_name looks like a real, named campus building."""
        return bool(self.building_name) and self.building_name not in NON_BUILDING_VALUES


@dataclass
class Section:
    crn: str                      # the numeric id, e.g. "35926"
    section_number: str | None    # the letter code, e.g. "ABC"
    status_code: str | None
    part_of_term: str | None
    start_date: str | None        # raw, e.g. "08-24-26Z"
    end_date: str | None
    meetings: list[Meeting] = field(default_factory=list)


@dataclass
class Course:
    subject: str                  # "CS"
    number: str                   # "225"
    title: str | None             # "Data Structures"
    description: str | None
    credit_hours: str | None      # raw, e.g. "4 hours."
    sections: list[Section] = field(default_factory=list)


def _text(element: ET.Element | None) -> str | None:
    """Element text, entity-decoded, with API null sentinels mapped to None."""
    if element is None or element.text is None:
        return None
    value = unescape(element.text).strip()
    return None if value in NULL_SENTINELS else value


def _parse_time(raw: str | None) -> Time | None:
    """'11:00AM' -> time(11, 0). Returns None for anything unparseable."""
    if not raw:
        return None
    cleaned = raw.strip().upper().replace(" ", "")
    clock, meridiem = cleaned[:-2], cleaned[-2:]
    if meridiem not in ("AM", "PM") or ":" not in clock:
        return None
    try:
        hour, minute = (int(part) for part in clock.split(":", 1))
    except ValueError:
        return None
    if hour == 12:          # 12AM -> 0, 12PM -> 12 after the += below
        hour = 0
    if meridiem == "PM":
        hour += 12
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None
    return Time(hour, minute)


def parse_subject_listing(xml: str) -> list[str]:
    """Course numbers offered under a subject, e.g. ['100', '101', '124', ...]."""
    root = ET.fromstring(xml)
    return [
        el.get("id", "")
        for el in root.iter("course")
        if el.get("id") and el.get("href")
    ]


def parse_term_listing(xml: str) -> list[tuple[str, str]]:
    """[('CS', 'Computer Science'), ...] for every subject in the term."""
    root = ET.fromstring(xml)
    out: list[tuple[str, str]] = []
    for el in root.iter("subject"):
        code = el.get("id")
        if code and el.get("href"):
            out.append((code, unescape((el.text or "").strip())))
    return out


def _parse_meeting(el: ET.Element) -> Meeting:
    type_el = el.find("type")
    return Meeting(
        meeting_id=el.get("id", ""),
        start=_parse_time(_text(el.find("start"))),
        end=_parse_time(_text(el.find("end"))),
        days_raw=_text(el.find("daysOfTheWeek")),
        room_number=_text(el.find("roomNumber")),
        building_name=_text(el.find("buildingName")),
        type_code=type_el.get("code") if type_el is not None else None,
        type_label=_text(type_el),
        instructors=[
            unescape((i.text or "").strip())
            for i in el.iter("instructor")
            if (i.text or "").strip()
        ],
    )


def _parse_section(el: ET.Element) -> Section:
    meetings_el = el.find("meetings")
    return Section(
        crn=el.get("id", ""),
        section_number=_text(el.find("sectionNumber")),
        status_code=_text(el.find("statusCode")),
        part_of_term=_text(el.find("partOfTerm")),
        start_date=_text(el.find("startDate")),
        end_date=_text(el.find("endDate")),
        meetings=(
            [_parse_meeting(m) for m in meetings_el.findall("meeting")]
            if meetings_el is not None
            else []
        ),
    )


def parse_course_detail(xml: str, subject: str, number: str) -> Course:
    """Parse a `?mode=detail` course document into a Course with sections+meetings."""
    root = ET.fromstring(xml)
    detailed = root.find("detailedSections")
    return Course(
        subject=subject,
        number=number,
        title=_text(root.find("label")),
        description=_text(root.find("description")),
        credit_hours=_text(root.find("creditHours")),
        sections=(
            [_parse_section(s) for s in detailed.findall("detailedSection")]
            if detailed is not None
            else []
        ),
    )
