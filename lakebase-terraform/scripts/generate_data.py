#!/usr/bin/env python3
"""Generate synthetic Teaching Strategies education domain data (stdlib only)."""

import csv
import random
import string
import uuid
from datetime import date, timedelta
from pathlib import Path

random.seed(42)

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# --- Configuration ---
NUM_SCHOOLS = 50
NUM_EDUCATORS = 200
NUM_CLASSROOMS = 150
NUM_STUDENTS = 1500
NUM_LEARNING_OBJECTIVES = 100
NUM_ASSESSMENTS = 5000

GRADE_LEVELS = ["PreK", "K", "1", "2", "3", "4", "5", "6"]
SCHOOL_TYPES = ["public", "private", "charter", "head_start"]
GRADE_RANGES = ["PreK-K", "PreK-3", "K-6"]
EDUCATOR_ROLES = ["lead_teacher", "assistant", "specialist", "administrator"]
CERTIFICATIONS = ["early_childhood", "elementary", "special_ed", "ESL"]
PROGRAM_TYPES = ["general", "montessori", "bilingual", "STEM"]
SUBJECTS = ["literacy", "math", "social_emotional", "science", "physical"]
STUDENT_STATUSES = ["active", "inactive", "transferred"]
EDUCATOR_STATUSES = ["active", "on_leave", "retired"]

DOMAINS = {
    "literacy": ["reading", "writing", "phonics", "vocabulary", "comprehension"],
    "math": ["counting", "geometry", "measurement", "patterns", "operations"],
    "social_emotional": ["self_regulation", "relationships", "empathy", "cooperation", "conflict_resolution"],
    "science": ["observation", "inquiry", "life_science", "physical_science", "earth_science"],
    "physical": ["gross_motor", "fine_motor", "balance", "coordination", "health"],
}

CLASSROOM_NAMES = [
    "Butterflies", "Sunflowers", "Starfish", "Ladybugs", "Dolphins",
    "Pandas", "Owls", "Turtles", "Rainbows", "Fireflies",
    "Hummingbirds", "Acorns", "Dragonflies", "Penguins", "Cubs",
]

FIRST_NAMES = [
    "Emma", "Liam", "Olivia", "Noah", "Ava", "Elijah", "Sophia", "James",
    "Isabella", "William", "Mia", "Benjamin", "Charlotte", "Lucas", "Amelia",
    "Henry", "Harper", "Alexander", "Evelyn", "Mason", "Luna", "Ethan",
    "Camila", "Daniel", "Gianna", "Michael", "Abigail", "Sebastian", "Ella",
    "Jack", "Aria", "Owen", "Scarlett", "Theodore", "Penelope", "Aiden",
    "Layla", "Samuel", "Chloe", "Ryan", "Victoria", "Leo", "Madison",
    "Thomas", "Eleanor", "Jackson", "Grace", "Logan", "Nora", "Caleb",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
    "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
    "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts",
]

CITIES = [
    "Springfield", "Riverside", "Fairview", "Madison", "Georgetown",
    "Franklin", "Clinton", "Greenville", "Bristol", "Oxford",
    "Arlington", "Burlington", "Chester", "Dover", "Easton",
    "Freeport", "Hampton", "Jackson", "Kingston", "Lakewood",
]

STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
]

SCHOOL_SUFFIXES = ["Academy", "Elementary", "Learning Center", "School", "Prep"]

SENTENCES = [
    "Student showed strong engagement during the assessment.",
    "Demonstrated improvement from the previous period.",
    "Needs additional support with foundational concepts.",
    "Excellent progress in peer collaboration activities.",
    "Shows creative problem-solving approaches.",
    "Consistent performance across multiple attempts.",
    "Responded well to scaffolded instruction.",
    "Demonstrates age-appropriate skill development.",
    "Making steady progress toward learning objectives.",
    "Shows enthusiasm for hands-on learning activities.",
]

_email_counter = 0


def _random_date(start_date: date, end_date: date) -> date:
    delta = (end_date - start_date).days
    return start_date + timedelta(days=random.randint(0, max(0, delta)))


def _random_email(first: str, last: str) -> str:
    global _email_counter
    _email_counter += 1
    domain = random.choice(["example.com", "school.edu", "education.org"])
    return f"{first.lower()}.{last.lower()}{_email_counter}@{domain}"


def write_csv(filename: str, rows: list[dict]) -> None:
    filepath = DATA_DIR / filename
    if not rows:
        return
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Generated {len(rows):,} rows -> {filepath}")


def generate_schools() -> list[dict]:
    rows = []
    for _ in range(NUM_SCHOOLS):
        rows.append({
            "school_id": str(uuid.uuid4()),
            "name": f"{random.choice(LAST_NAMES)} {random.choice(SCHOOL_SUFFIXES)}",
            "district": f"{random.choice(CITIES)} Unified School District",
            "state": random.choice(STATES),
            "school_type": random.choice(SCHOOL_TYPES),
            "grade_range": random.choice(GRADE_RANGES),
            "student_capacity": random.randint(50, 500),
        })
    return rows


def generate_educators(schools: list[dict]) -> list[dict]:
    rows = []
    for _ in range(NUM_EDUCATORS):
        today = date.today()
        hire_date = _random_date(today - timedelta(days=3650), today)
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        rows.append({
            "educator_id": str(uuid.uuid4()),
            "first_name": first,
            "last_name": last,
            "email": _random_email(first, last),
            "role": random.choice(EDUCATOR_ROLES),
            "certification": random.choice(CERTIFICATIONS),
            "school_id": random.choice(schools)["school_id"],
            "hire_date": hire_date.isoformat(),
            "status": random.choices(EDUCATOR_STATUSES, weights=[85, 10, 5])[0],
        })
    return rows


def generate_classrooms(schools: list[dict], educators: list[dict]) -> list[dict]:
    lead_teachers = [e for e in educators if e["role"] == "lead_teacher"]
    rows = []
    for i in range(NUM_CLASSROOMS):
        school = random.choice(schools)
        teacher = random.choice(lead_teachers) if lead_teachers else random.choice(educators)
        room_num = random.randint(100, 399)
        name_suffix = CLASSROOM_NAMES[i % len(CLASSROOM_NAMES)]
        rows.append({
            "classroom_id": str(uuid.uuid4()),
            "name": f"Room {room_num} - {name_suffix}",
            "grade_level": random.choice(GRADE_LEVELS),
            "school_id": school["school_id"],
            "educator_id": teacher["educator_id"],
            "capacity": random.randint(8, 30),
            "program_type": random.choice(PROGRAM_TYPES),
        })
    return rows


def generate_students(schools: list[dict], classrooms: list[dict]) -> list[dict]:
    rows = []
    today = date.today()
    for _ in range(NUM_STUDENTS):
        classroom = random.choice(classrooms)
        age_years = random.randint(3, 12)
        dob = today - timedelta(days=age_years * 365 + random.randint(0, 364))
        enrollment_date = _random_date(today - timedelta(days=1095), today)
        rows.append({
            "student_id": str(uuid.uuid4()),
            "first_name": random.choice(FIRST_NAMES),
            "last_name": random.choice(LAST_NAMES),
            "date_of_birth": dob.isoformat(),
            "grade_level": classroom["grade_level"],
            "school_id": classroom["school_id"],
            "classroom_id": classroom["classroom_id"],
            "enrollment_date": enrollment_date.isoformat(),
            "status": random.choices(STUDENT_STATUSES, weights=[85, 10, 5])[0],
        })
    return rows


def generate_learning_objectives() -> list[dict]:
    rows = []
    for _ in range(NUM_LEARNING_OBJECTIVES):
        subject = random.choice(SUBJECTS)
        domain = random.choice(DOMAINS[subject])
        grade = random.choice(GRADE_LEVELS)
        prefix = subject[:3].upper()
        code = f"{prefix}.{random.randint(1, 9)}.{random.randint(1, 9)}"
        rows.append({
            "objective_id": str(uuid.uuid4()),
            "subject": subject,
            "domain": domain,
            "description": f"Student demonstrates proficiency in {domain} within {subject} for grade {grade}",
            "grade_level": grade,
            "standard_code": code,
        })
    return rows


def generate_assessments(
    students: list[dict],
    educators: list[dict],
    learning_objectives: list[dict],
) -> list[dict]:
    rows = []
    today = date.today()
    for _ in range(NUM_ASSESSMENTS):
        student = random.choice(students)
        educator = random.choice(educators)
        objective = random.choice(learning_objectives)
        assessment_date = _random_date(today - timedelta(days=730), today)
        month = assessment_date.month
        if month <= 3:
            period = "winter"
        elif month <= 7:
            period = "spring"
        else:
            period = "fall"
        rows.append({
            "assessment_id": str(uuid.uuid4()),
            "student_id": student["student_id"],
            "educator_id": educator["educator_id"],
            "subject": objective["subject"],
            "domain": objective["domain"],
            "score": round(random.uniform(1.0, 9.0), 1),
            "assessment_date": assessment_date.isoformat(),
            "assessment_period": period,
            "learning_objective_id": objective["objective_id"],
            "notes": random.choice(SENTENCES) if random.random() < 0.3 else "",
        })
    return rows


def main():
    print("Generating synthetic Teaching Strategies data...")
    print()

    schools = generate_schools()
    write_csv("schools.csv", schools)

    educators = generate_educators(schools)
    write_csv("educators.csv", educators)

    classrooms = generate_classrooms(schools, educators)
    write_csv("classrooms.csv", classrooms)

    students = generate_students(schools, classrooms)
    write_csv("students.csv", students)

    learning_objectives = generate_learning_objectives()
    write_csv("learning_objectives.csv", learning_objectives)

    assessments = generate_assessments(students, educators, learning_objectives)
    write_csv("assessments.csv", assessments)

    print()
    print("Done! CSV files written to:", DATA_DIR)


if __name__ == "__main__":
    main()
