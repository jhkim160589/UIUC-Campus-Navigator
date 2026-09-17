"""Parser tests. These cover facts about the API feed, not design decisions.

Scaffolding is Claude's; the test CASES for your own code are yours to choose.
Add graph and feasibility tests in Week 2-3 - see the marker at the bottom.
"""

from datetime import time

from app.ingest.parse import (
    DAY_CODES,
    _parse_time,
    parse_course_detail,
    parse_subject_listing,
)

# A trimmed real response: two sections, one with two meetings, one with none.
# Note the escaped '&' and the 'n.a.' - both are exactly how the API sends them.
COURSE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<ns2:course id="ECE 210" xmlns:ns2="http://rest.cis.illinois.edu">
  <label>Analog Signal Processing</label>
  <description>Signals and systems.</description>
  <creditHours>4 hours.</creditHours>
  <detailedSections>
    <detailedSection id="35926">
      <sectionNumber>ABC</sectionNumber>
      <statusCode>A</statusCode>
      <startDate>08-24-26Z</startDate>
      <endDate>12-09-26Z</endDate>
      <meetings>
        <meeting id="0">
          <start>11:00AM</start><end>12:50PM</end>
          <daysOfTheWeek>MWF</daysOfTheWeek>
          <roomNumber>4025</roomNumber>
          <buildingName>Electrical &amp; Computer Eng Bldg</buildingName>
          <type code="LEC">Lecture</type>
          <instructors><instructor lastName="Solomon" firstName="B">Solomon, B</instructor></instructors>
        </meeting>
        <meeting id="1">
          <start>02:00PM</start><end>02:50PM</end>
          <daysOfTheWeek>R</daysOfTheWeek>
          <roomNumber>n.a.</roomNumber>
          <buildingName>Location Pending</buildingName>
          <type code="LAB">Laboratory</type>
          <instructors/>
        </meeting>
      </meetings>
    </detailedSection>
    <detailedSection id="40001">
      <sectionNumber>ONL</sectionNumber>
      <meetings>
        <meeting id="0">
          <start>n.a.</start><end>n.a.</end>
          <daysOfTheWeek>n.a.</daysOfTheWeek>
          <buildingName>n.a.</buildingName>
          <type code="ONL">Online</type>
        </meeting>
      </meetings>
    </detailedSection>
  </detailedSections>
</ns2:course>
"""

SUBJECT_XML = """<?xml version="1.0" encoding="UTF-8"?>
<ns2:subject id="CS" xmlns:ns2="http://rest.cis.illinois.edu">
  <courses>
    <course id="225" href="https://courses.illinois.edu/x/225.xml">Data Structures</course>
    <course id="233" href="https://courses.illinois.edu/x/233.xml">Computer Architecture</course>
  </courses>
</ns2:subject>
"""


def test_parses_course_and_section_counts():
    course = parse_course_detail(COURSE_XML, "ECE", "210")
    assert course.subject == "ECE"
    assert course.number == "210"
    assert course.title == "Analog Signal Processing"
    assert course.credit_hours == "4 hours."
    assert len(course.sections) == 2


def test_a_section_can_hold_more_than_one_meeting():
    # 804 sections produced 807 meetings in the real sample. Do not collapse these.
    course = parse_course_detail(COURSE_XML, "ECE", "210")
    assert len(course.sections[0].meetings) == 2


def test_html_entities_are_decoded():
    # The API does NOT decode these. Storing the raw string would poison geocoding.
    meeting = parse_course_detail(COURSE_XML, "ECE", "210").sections[0].meetings[0]
    assert meeting.building_name == "Electrical & Computer Eng Bldg"
    assert "&amp;" not in meeting.building_name


def test_na_sentinel_becomes_none():
    online = parse_course_detail(COURSE_XML, "ECE", "210").sections[1].meetings[0]
    assert online.building_name is None
    assert online.days_raw is None
    assert online.start is None


def test_r_means_thursday():
    meetings = parse_course_detail(COURSE_XML, "ECE", "210").sections[0].meetings
    assert meetings[0].days == ["Monday", "Wednesday", "Friday"]
    assert meetings[1].days == ["Thursday"]
    assert DAY_CODES["R"] == "Thursday"
    assert DAY_CODES["T"] == "Tuesday"


def test_location_flags():
    section = parse_course_detail(COURSE_XML, "ECE", "210").sections[0]
    lecture, lab = section.meetings
    assert lecture.has_location is True
    assert lab.has_location is False          # 'Location Pending'
    assert lab.is_online is False             # pending != online - different reasons

    online = parse_course_detail(COURSE_XML, "ECE", "210").sections[1].meetings[0]
    assert online.is_online is True
    assert online.has_location is False


def test_subject_listing():
    assert parse_subject_listing(SUBJECT_XML) == ["225", "233"]


def test_time_parsing_handles_noon_and_midnight():
    assert _parse_time("11:00AM") == time(11, 0)
    assert _parse_time("12:00PM") == time(12, 0)     # noon, not 00:00
    assert _parse_time("12:30AM") == time(0, 30)     # after midnight
    assert _parse_time("1:05PM") == time(13, 5)
    assert _parse_time("99:99PM") is None
    assert _parse_time("ARRANGED") is None
    assert _parse_time(None) is None


# ---------------------------------------------------------------------------
# WEEK 2+: your tests go below. Start with paths you can verify by hand -
# two adjacent buildings where you already know which way the walk goes.
# ---------------------------------------------------------------------------
