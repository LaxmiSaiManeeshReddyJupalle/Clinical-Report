"""
Mock Data Generator for UIC ATU Clinical Report Generator

Creates synthetic clinical documents for development and testing.
All patient data is COMPLETELY FICTIONAL - no real PHI is used.

Usage:
    python -m src.ingestion.mock_data_generator

This will create:
    mock_data/
    ├── FY 25/
    │   ├── Doe_John_001/
    │   │   ├── progress_note_2025-01-05.txt
    │   │   ├── admission_summary.txt
    │   │   └── discharge_plan.txt
    │   ├── Smith_Jane_002/
    │   └── ...
    └── FY 24/
        └── ...
"""

import os
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

# Synthetic data pools - ALL FICTIONAL
FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda",
    "David", "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Lisa", "Daniel", "Nancy",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker"
]

DIAGNOSES = [
    "Major Depressive Disorder, recurrent, moderate",
    "Generalized Anxiety Disorder",
    "Bipolar I Disorder, current episode manic",
    "Post-Traumatic Stress Disorder",
    "Schizophrenia, paranoid type",
    "Attention-Deficit/Hyperactivity Disorder",
    "Autism Spectrum Disorder",
    "Obsessive-Compulsive Disorder",
    "Panic Disorder with Agoraphobia",
    "Social Anxiety Disorder",
    "Borderline Personality Disorder",
    "Substance Use Disorder, alcohol, moderate"
]

MEDICATIONS = [
    ("Sertraline", "50mg", "daily"),
    ("Fluoxetine", "20mg", "daily"),
    ("Escitalopram", "10mg", "daily"),
    ("Bupropion", "150mg", "twice daily"),
    ("Venlafaxine", "75mg", "daily"),
    ("Duloxetine", "30mg", "daily"),
    ("Quetiapine", "100mg", "at bedtime"),
    ("Risperidone", "2mg", "twice daily"),
    ("Aripiprazole", "10mg", "daily"),
    ("Lamotrigine", "100mg", "daily"),
    ("Lithium", "300mg", "twice daily"),
    ("Alprazolam", "0.5mg", "as needed"),
    ("Lorazepam", "1mg", "as needed"),
    ("Methylphenidate", "20mg", "morning"),
    ("Trazodone", "50mg", "at bedtime")
]

PROVIDERS = [
    "Dr. Sarah Mitchell, MD",
    "Dr. James Peterson, MD",
    "Dr. Maria Santos, PsyD",
    "Dr. Robert Chen, MD",
    "Dr. Emily Watson, PhD",
    "Jennifer Adams, LCSW",
    "Michael Brown, LCPC",
    "Dr. Lisa Park, MD",
    "Dr. David Kim, DO",
    "Amanda Torres, MSW"
]

TREATMENT_GOALS = [
    "Reduce symptoms of depression as evidenced by PHQ-9 score < 10",
    "Improve sleep quality and establish regular sleep schedule",
    "Develop and utilize healthy coping strategies for anxiety",
    "Increase social engagement and reduce isolation",
    "Maintain medication compliance and attend all appointments",
    "Identify and challenge negative thought patterns",
    "Improve emotion regulation skills",
    "Reduce frequency and intensity of panic attacks",
    "Establish stable daily routine and self-care practices",
    "Process traumatic memories in a safe therapeutic environment"
]


def generate_ssn() -> str:
    """Generate a fake SSN (format: XXX-XX-XXXX, using invalid ranges)."""
    # Use invalid SSN ranges (900-999 are invalid)
    return f"9{random.randint(10, 99)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}"


def generate_phone() -> str:
    """Generate a fake phone number (555 exchange is reserved for fiction)."""
    return f"(555) {random.randint(100, 999)}-{random.randint(1000, 9999)}"


def generate_dob(min_age: int = 18, max_age: int = 75) -> datetime:
    """Generate a random date of birth."""
    today = datetime.now()
    age = random.randint(min_age, max_age)
    dob = today - timedelta(days=age * 365 + random.randint(0, 364))
    return dob


def generate_address() -> str:
    """Generate a fake address."""
    street_numbers = range(100, 9999)
    street_names = [
        "Oak Street", "Maple Avenue", "Elm Drive", "Pine Road", "Cedar Lane",
        "Main Street", "First Avenue", "Second Street", "Park Drive", "Lake Road"
    ]
    cities = ["Springfield", "Riverside", "Fairview", "Greenville", "Madison"]
    states = ["IL", "WI", "IN", "MI", "OH"]

    return f"{random.choice(street_numbers)} {random.choice(street_names)}, {random.choice(cities)}, {random.choice(states)} {random.randint(60000, 62999)}"


class SyntheticPatient:
    """Generates synthetic patient data."""

    def __init__(self, patient_id: int):
        self.id = patient_id
        self.first_name = random.choice(FIRST_NAMES)
        self.last_name = random.choice(LAST_NAMES)
        self.dob = generate_dob()
        self.ssn = generate_ssn()
        self.phone = generate_phone()
        self.address = generate_address()
        self.diagnoses = random.sample(DIAGNOSES, k=random.randint(1, 3))
        self.medications = random.sample(MEDICATIONS, k=random.randint(1, 4))
        self.provider = random.choice(PROVIDERS)
        self.admission_date = datetime.now() - timedelta(days=random.randint(30, 180))
        self.treatment_goals = random.sample(TREATMENT_GOALS, k=random.randint(2, 4))

    @property
    def folder_name(self) -> str:
        """Generate folder name for patient."""
        return f"{self.last_name}_{self.first_name}_{self.id:03d}"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self) -> int:
        today = datetime.now()
        return today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))


class ClinicalDocumentGenerator:
    """Generates synthetic clinical documents."""

    def __init__(self, patient: SyntheticPatient):
        self.patient = patient

    def generate_admission_summary(self) -> str:
        """Generate synthetic admission summary."""
        p = self.patient
        meds = "\n".join([f"  - {med[0]} {med[1]} {med[2]}" for med in p.medications])
        diagnoses = "\n".join([f"  - {d}" for d in p.diagnoses])
        goals = "\n".join([f"  {i+1}. {g}" for i, g in enumerate(p.treatment_goals)])

        return f"""
ADMISSION SUMMARY
================================================================================

PATIENT INFORMATION
------------------
Name: {p.full_name}
Date of Birth: {p.dob.strftime('%m/%d/%Y')}
Age: {p.age} years
SSN: {p.ssn}
Phone: {p.phone}
Address: {p.address}

ADMISSION DETAILS
-----------------
Admission Date: {p.admission_date.strftime('%m/%d/%Y')}
Admitting Provider: {p.provider}
Unit: Adult Treatment Unit (ATU)

DIAGNOSES
---------
{diagnoses}

CURRENT MEDICATIONS
------------------
{meds}

CHIEF COMPLAINT
--------------
Patient presents with {random.choice(['worsening', 'persistent', 'acute exacerbation of'])}
symptoms related to {p.diagnoses[0].split(',')[0]}. Patient reports
{random.choice(['difficulty sleeping', 'decreased appetite', 'increased anxiety', 'mood instability'])}
over the past {random.randint(2, 8)} weeks.

HISTORY OF PRESENT ILLNESS
-------------------------
{p.full_name} is a {p.age}-year-old patient with a history of {p.diagnoses[0]}
who presents for {random.choice(['voluntary', 'voluntary'])} admission to the ATU.
Patient reports {random.choice(['gradual', 'sudden'])} onset of symptoms including
{random.choice(['depressed mood', 'anxiety', 'mood swings', 'paranoid ideation'])}.
Patient denies current {random.choice(['suicidal', 'homicidal'])} ideation but reports
{random.choice(['passive thoughts of death', 'feeling hopeless', 'difficulty concentrating'])}.

MENTAL STATUS EXAMINATION
------------------------
Appearance: {random.choice(['Well-groomed', 'Disheveled', 'Appropriately dressed'])}
Behavior: {random.choice(['Cooperative', 'Guarded', 'Restless', 'Calm'])}
Speech: {random.choice(['Normal rate and rhythm', 'Soft', 'Pressured', 'Slow'])}
Mood: {random.choice(['Depressed', 'Anxious', 'Irritable', 'Euthymic'])}
Affect: {random.choice(['Constricted', 'Flat', 'Labile', 'Appropriate'])}
Thought Process: {random.choice(['Linear', 'Circumstantial', 'Tangential', 'Goal-directed'])}
Thought Content: {random.choice(['No SI/HI', 'Denies AVH', 'Preoccupied with worry'])}
Cognition: {random.choice(['Alert and oriented x4', 'Alert and oriented x3'])}
Insight: {random.choice(['Fair', 'Poor', 'Good'])}
Judgment: {random.choice(['Fair', 'Poor', 'Good'])}

TREATMENT PLAN
-------------
{goals}

ESTIMATED LENGTH OF STAY
-----------------------
{random.randint(5, 14)} days

________________________________________________________________________________
Prepared by: {p.provider}
Date: {p.admission_date.strftime('%m/%d/%Y')}
"""

    def generate_progress_note(self, days_since_admission: int) -> str:
        """Generate synthetic progress note."""
        p = self.patient
        note_date = p.admission_date + timedelta(days=days_since_admission)

        return f"""
PROGRESS NOTE
================================================================================

Patient: {p.full_name}
DOB: {p.dob.strftime('%m/%d/%Y')}
Date of Service: {note_date.strftime('%m/%d/%Y')}
Day {days_since_admission} of Admission
Provider: {p.provider}

SUBJECTIVE
----------
Patient reports {random.choice(['improved', 'stable', 'fluctuating', 'worsening'])} mood
since {random.choice(['yesterday', 'last session', 'medication adjustment'])}.
Sleep was {random.choice(['adequate (6-8 hours)', 'poor (4-5 hours)', 'disrupted', 'improved'])}.
Appetite is {random.choice(['fair', 'poor', 'good', 'improved'])}.
Patient {random.choice(['participated in', 'declined', 'actively engaged in'])} group therapy today.
Reports {random.choice(['no', 'mild', 'moderate'])} anxiety symptoms.
Denies SI/HI.

OBJECTIVE
---------
Vital Signs: BP {random.randint(110, 140)}/{random.randint(70, 90)}, HR {random.randint(60, 90)},
Temp 98.{random.randint(0, 9)}F

Mental Status:
- Appearance: {random.choice(['Well-groomed', 'Adequate hygiene', 'Casually dressed'])}
- Behavior: {random.choice(['Cooperative', 'Pleasant', 'Engaged', 'Reserved'])}
- Mood: "{random.choice(['better', 'okay', 'tired', 'frustrated', 'hopeful'])}"
- Affect: {random.choice(['Mood-congruent', 'Brighter than yesterday', 'Constricted', 'Reactive'])}
- Thought Process: {random.choice(['Logical', 'Goal-directed', 'Organized'])}
- Thought Content: No SI/HI, no AVH
- Cognition: A&Ox4

Current Medications:
{chr(10).join([f'  - {med[0]} {med[1]} {med[2]}' for med in p.medications])}

ASSESSMENT
----------
{p.age}-year-old with {p.diagnoses[0]}, day {days_since_admission} of hospitalization.
Patient showing {random.choice(['gradual improvement', 'stable symptoms', 'slow progress', 'good response to treatment'])}.
{random.choice(['Continue current treatment plan', 'Medication adjustment may be warranted', 'Patient making progress toward discharge goals'])}.

PLAN
----
1. Continue current medications
2. Continue individual therapy {random.choice(['daily', 'every other day'])}
3. Encourage group participation
4. Monitor for side effects
5. {random.choice(['Family meeting scheduled', 'Discharge planning to begin', 'Continue monitoring sleep', 'Social work consult'])}

________________________________________________________________________________
Electronically signed by: {p.provider}
Date/Time: {note_date.strftime('%m/%d/%Y')} {random.randint(8, 17)}:{random.randint(10, 59):02d}
"""

    def generate_discharge_summary(self, length_of_stay: int) -> str:
        """Generate synthetic discharge summary."""
        p = self.patient
        discharge_date = p.admission_date + timedelta(days=length_of_stay)

        return f"""
DISCHARGE SUMMARY
================================================================================

PATIENT INFORMATION
------------------
Name: {p.full_name}
DOB: {p.dob.strftime('%m/%d/%Y')}
SSN: {p.ssn}

ADMISSION/DISCHARGE DATES
------------------------
Admission Date: {p.admission_date.strftime('%m/%d/%Y')}
Discharge Date: {discharge_date.strftime('%m/%d/%Y')}
Length of Stay: {length_of_stay} days

ATTENDING PROVIDER
-----------------
{p.provider}

DISCHARGE DIAGNOSES
------------------
{chr(10).join([f'  {i+1}. {d}' for i, d in enumerate(p.diagnoses)])}

REASON FOR ADMISSION
-------------------
Patient was admitted for stabilization of {p.diagnoses[0]} with
{random.choice(['suicidal ideation', 'severe symptoms', 'medication adjustment needs', 'crisis stabilization'])}.

HOSPITAL COURSE
--------------
{p.full_name} was admitted to the Adult Treatment Unit on {p.admission_date.strftime('%m/%d/%Y')}.
During hospitalization, patient received {random.choice(['medication management', 'medication optimization',
'psychopharmacological treatment'])} and participated in {random.choice(['daily individual and group therapy',
'intensive outpatient programming', 'milieu therapy and groups'])}.

Patient showed {random.choice(['gradual', 'steady', 'significant'])} improvement in
{random.choice(['mood symptoms', 'anxiety levels', 'thought organization', 'daily functioning'])}
throughout the admission. By discharge, patient demonstrated
{random.choice(['resolution of acute symptoms', 'significant symptom reduction', 'stabilization of mood'])}
and expressed {random.choice(['readiness for discharge', 'motivation for continued outpatient treatment',
'commitment to treatment plan'])}.

DISCHARGE MEDICATIONS
--------------------
{chr(10).join([f'  - {med[0]} {med[1]} {med[2]}' for med in p.medications])}

DISCHARGE INSTRUCTIONS
---------------------
1. Take all medications as prescribed
2. Attend all follow-up appointments
3. Contact provider if symptoms worsen
4. Go to nearest ER if experiencing crisis or suicidal thoughts
5. Maintain regular sleep schedule
6. Avoid alcohol and recreational drugs

FOLLOW-UP APPOINTMENTS
---------------------
- Psychiatry: {(discharge_date + timedelta(days=7)).strftime('%m/%d/%Y')} with {p.provider}
- Therapy: {(discharge_date + timedelta(days=3)).strftime('%m/%d/%Y')} with outpatient therapist

CONDITION AT DISCHARGE
---------------------
{random.choice(['Improved', 'Stable', 'Good'])} - Patient is safe for discharge with
{random.choice(['no', 'no active'])} suicidal or homicidal ideation.

PROGNOSIS
---------
{random.choice(['Good', 'Fair', 'Guarded'])} with continued treatment compliance.

________________________________________________________________________________
Attending Physician: {p.provider}
Date: {discharge_date.strftime('%m/%d/%Y')}

This document contains Protected Health Information (PHI).
"""

    def generate_treatment_plan(self) -> str:
        """Generate synthetic treatment plan."""
        p = self.patient

        return f"""
INDIVIDUALIZED TREATMENT PLAN
================================================================================

Patient: {p.full_name}
DOB: {p.dob.strftime('%m/%d/%Y')}
Admission Date: {p.admission_date.strftime('%m/%d/%Y')}
Primary Provider: {p.provider}

DIAGNOSES
---------
{chr(10).join([f'  Axis I: {d}' for d in p.diagnoses])}

PRESENTING PROBLEMS
------------------
1. {random.choice(['Depressive symptoms affecting daily functioning', 'Anxiety interfering with social/occupational activities', 'Mood instability causing interpersonal difficulties'])}
2. {random.choice(['Sleep disturbance', 'Appetite changes', 'Concentration difficulties'])}
3. {random.choice(['Social isolation', 'Difficulty managing stress', 'Low self-esteem'])}

PATIENT STRENGTHS
----------------
- {random.choice(['Motivated for treatment', 'Supportive family', 'Good insight into illness'])}
- {random.choice(['Previous successful treatment', 'Strong coping skills when stable', 'Employment/school engagement'])}
- {random.choice(['No substance use', 'Medication compliant', 'Engaged in therapy'])}

TREATMENT GOALS
--------------
{chr(10).join([f'Goal {i+1}: {g}' for i, g in enumerate(p.treatment_goals)])}

INTERVENTIONS
------------
1. Medication Management
   - Current regimen to be monitored daily
   - Adjustment based on response and side effects

2. Individual Therapy
   - {random.choice(['CBT', 'DBT', 'Supportive therapy'])} {random.choice(['2x weekly', '3x weekly', 'daily'])}
   - Focus: {random.choice(['Cognitive restructuring', 'Emotion regulation', 'Coping skills', 'Trauma processing'])}

3. Group Therapy
   - Daily psychoeducation groups
   - {random.choice(['Process group', 'Skills group', 'Support group'])} as appropriate

4. Nursing Interventions
   - Safety monitoring per protocol
   - Medication administration and education
   - Sleep hygiene support

5. Social Work
   - Discharge planning
   - Family involvement as appropriate
   - Resource coordination

TARGET DISCHARGE DATE
--------------------
{(p.admission_date + timedelta(days=random.randint(7, 14))).strftime('%m/%d/%Y')}

DISCHARGE CRITERIA
-----------------
- Stabilization of acute symptoms
- No imminent danger to self or others
- Adequate outpatient supports in place
- Demonstrated understanding of discharge plan

________________________________________________________________________________
Treatment Team Signatures:

Psychiatrist: {p.provider}
Primary Nurse: ______________________
Social Worker: ______________________
Therapist: ______________________

Date: {p.admission_date.strftime('%m/%d/%Y')}
"""


def create_mock_data(
    base_path: str = "./mock_data",
    fiscal_years: List[str] = None,
    patients_per_year: int = 5
) -> Dict[str, Any]:
    """
    Create mock data directory structure with synthetic documents.

    Args:
        base_path: Root directory for mock data
        fiscal_years: List of fiscal year folders to create
        patients_per_year: Number of synthetic patients per fiscal year

    Returns:
        Dictionary with creation statistics
    """
    if fiscal_years is None:
        fiscal_years = ["FY 25", "FY 24", "FY 23"]

    base_dir = Path(base_path)
    base_dir.mkdir(parents=True, exist_ok=True)

    stats = {
        "base_path": str(base_dir.absolute()),
        "fiscal_years": [],
        "total_patients": 0,
        "total_documents": 0
    }

    patient_id = 1

    for fy in fiscal_years:
        fy_dir = base_dir / fy
        fy_dir.mkdir(exist_ok=True)

        fy_stats = {"name": fy, "patients": [], "document_count": 0}

        for _ in range(patients_per_year):
            # Create synthetic patient
            patient = SyntheticPatient(patient_id)
            patient_dir = fy_dir / patient.folder_name
            patient_dir.mkdir(exist_ok=True)

            # Generate documents
            doc_gen = ClinicalDocumentGenerator(patient)
            documents_created = 0

            # Admission summary
            (patient_dir / "admission_summary.txt").write_text(doc_gen.generate_admission_summary())
            documents_created += 1

            # Treatment plan
            (patient_dir / "treatment_plan.txt").write_text(doc_gen.generate_treatment_plan())
            documents_created += 1

            # Progress notes (variable number based on length of stay)
            los = random.randint(5, 14)
            for day in [1, 3, 5, 7]:
                if day <= los:
                    note_date = (patient.admission_date + timedelta(days=day)).strftime('%Y-%m-%d')
                    (patient_dir / f"progress_note_{note_date}.txt").write_text(
                        doc_gen.generate_progress_note(day)
                    )
                    documents_created += 1

            # Discharge summary (if stay complete - for most patients)
            if random.random() > 0.2:  # 80% have discharge summaries
                (patient_dir / "discharge_summary.txt").write_text(
                    doc_gen.generate_discharge_summary(los)
                )
                documents_created += 1

            fy_stats["patients"].append({
                "folder": patient.folder_name,
                "documents": documents_created
            })
            fy_stats["document_count"] += documents_created
            stats["total_patients"] += 1
            stats["total_documents"] += documents_created

            patient_id += 1

        stats["fiscal_years"].append(fy_stats)

    return stats


def main():
    """Main function to generate mock data."""
    print("=" * 60)
    print("UIC ATU Clinical Report Generator - Mock Data Generator")
    print("=" * 60)
    print("\nGenerating synthetic clinical documents...")
    print("NOTE: All data is COMPLETELY FICTIONAL for development only.\n")

    stats = create_mock_data(
        base_path="./mock_data",
        fiscal_years=["FY 25", "FY 24", "FY 23"],
        patients_per_year=5
    )

    print(f"Mock data created at: {stats['base_path']}")
    print(f"\nStatistics:")
    print(f"  - Fiscal years: {len(stats['fiscal_years'])}")
    print(f"  - Total patients: {stats['total_patients']}")
    print(f"  - Total documents: {stats['total_documents']}")

    print("\nBreakdown by fiscal year:")
    for fy in stats['fiscal_years']:
        print(f"\n  {fy['name']}:")
        print(f"    Patients: {len(fy['patients'])}")
        print(f"    Documents: {fy['document_count']}")
        for p in fy['patients']:
            print(f"      - {p['folder']}: {p['documents']} docs")

    print("\n" + "=" * 60)
    print("Mock data generation complete!")
    print("You can now run the app with: streamlit run src/ui/app.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
