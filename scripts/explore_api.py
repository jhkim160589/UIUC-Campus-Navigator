"""Pull a term from the UIUC API and print what is in it. No database required.

Use this to answer Week 1 schema questions with real numbers instead of guesses.

    python scripts/explore_api.py CS ECE MATH PHYS
    python scripts/explore_api.py CS --limit 10

Prints: course/section/meeting counts, every distinct building with frequency,
daysOfTheWeek values, meeting type codes, and any rows with no usable location.
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.ingest.cis_client import CISClient          # noqa: E402
from app.ingest.parse import (                        # noqa: E402
    parse_course_detail,
    parse_subject_listing,
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("subjects", nargs="+", help="subject codes, e.g. CS ECE MATH")
    ap.add_argument("--limit", type=int, default=0,
                    help="max courses per subject (0 = all)")
    args = ap.parse_args()

    buildings: Counter[str] = Counter()
    days: Counter[str] = Counter()
    types: Counter[str] = Counter()
    n_courses = n_sections = n_meetings = 0
    unlocatable: list[str] = []

    with CISClient() as client:
        for subject in args.subjects:
            numbers = parse_subject_listing(client.fetch_subject(subject))
            if args.limit:
                numbers = numbers[: args.limit]
            print(f"{subject}: fetching {len(numbers)} courses ...", flush=True)

            for number, xml in client.iter_course_details(subject, numbers):
                course = parse_course_detail(xml, subject, number)
                n_courses += 1
                n_sections += len(course.sections)
                for section in course.sections:
                    for meeting in section.meetings:
                        n_meetings += 1
                        buildings[meeting.building_name or "(none)"] += 1
                        days[meeting.days_raw or "(none)"] += 1
                        types[meeting.type_code or "(none)"] += 1
                        if not meeting.has_location and not meeting.is_online:
                            unlocatable.append(
                                f"{subject} {number} {section.section_number} "
                                f"[{meeting.type_code}] {meeting.building_name!r}"
                            )

    print(f"\n{'=' * 60}")
    print(f"courses={n_courses}  sections={n_sections}  meetings={n_meetings}")
    print(f"http requests={client.request_count}")

    print(f"\n--- {len(buildings)} distinct buildings ---")
    for name, count in buildings.most_common():
        print(f"{count:6d}  {name}")

    print("\n--- daysOfTheWeek ---")
    for value, count in days.most_common():
        print(f"{count:6d}  {value}")

    print("\n--- meeting types ---")
    for value, count in types.most_common():
        print(f"{count:6d}  {value}")

    print(f"\n--- {len(unlocatable)} meetings with no usable location (not online) ---")
    for line in unlocatable[:25]:
        print(f"   {line}")
    if len(unlocatable) > 25:
        print(f"   ... and {len(unlocatable) - 25} more")


if __name__ == "__main__":
    main()
