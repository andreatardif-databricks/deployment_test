#!/usr/bin/env python3
"""Generate synthetic Teaching Strategies education domain data using Faker."""

import csv
import os
import random
import uuid
from datetime import date, timedelta
from pathlib import Path

from faker import Faker

fake = Faker()
Faker.seed(42)
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
ASSESSMENT_PERIODS = ["fall", "winter", "spring"]
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


def write_csv(filename: str, rows: list[dict]) -> None:
    """Write rows to a CSV file in the data directory."""
    filepath = DATA_DIR / filename
    if not rows:
        return
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Generated {len(rows):,} rows → {filepath}")


def generate_schools() -> list[dict]:
    rows = []
    for _ in range(NUM_SCHOOLS):
        rows.append({
            "school_id": str(uuid.uuid4()),
            "name": f"{fake.last_name()} {random.choice(['Academy', 'Elementary', 'Learning Center', 'School', 'Prep'])}",
            "district": f"{fake.city()} Unified School District",
            "state": fake.state_abbr(),
            "school_type": random.choice(SCHOOL_TYPES),
            "grade_range": random.choice(GRADE_RANGES),
            "student_capacity": random.randint(50, 500),
        })
    return rows


def generate_educators(schools: list[dict]) -> list[dict]:
    rows = []
    for _ in range(NUM_EDUCATORS):
        hire_date = fake.date_between(start_date="-10y", end_date="today")
        rows.append({
            "educator_id": str(uuid.uuid4()),
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.unique.email(),
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
    for _ in range(NUM_STUDENTS):
        classroom = random.choice(classrooms)
        age_years = random.randint(3, 12)
        dob = date.today() - timedelta(days=age_years * 365 + random.randint(0, 364))
        enrollment_date = fake.date_between(start_date="-3y", end_date="today")
        rows.append({
            "student_id": str(uuid.uuid4()),
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
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
    for _ in range(NUM_ASSESSMENTS):
        student = random.choice(students)
        educator = random.choice(educators)
        objective = random.choice(learning_objectives)
        assessment_date = fake.date_between(start_date="-2y", end_date="today")
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
            "notes": fake.sentence() if random.random() < 0.3 else "",
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
