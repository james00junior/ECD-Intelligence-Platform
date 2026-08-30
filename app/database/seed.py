from datetime import date
import random

from app.database.database import Base
from app.database.database import SessionLocal
from app.database.database import engine

from app.database.models import Attendance
from app.database.models import Child
from app.database.models import Coach
from app.database.models import Franchisee
from app.database.models import LocalMunicipality
from app.database.models import MainPlace
from app.database.models import MonthlyMetric
from app.database.models import Municipality
from app.database.models import Organisation
from app.database.models import PopulationSnapshot
from app.database.models import Province
from app.database.models import SmallArea
from app.database.models import SubPlace


# -------------------------------------------------------------
# REPRODUCIBILITY
# -------------------------------------------------------------

random.seed(42)


# -------------------------------------------------------------
# DATABASE SETUP
# -------------------------------------------------------------

def create_tables() -> None:
    """
    Create all database tables defined by the SQLAlchemy models.
    """
    Base.metadata.create_all(bind=engine)


# -------------------------------------------------------------
# SEED DATABASE
# -------------------------------------------------------------

def seed_database() -> None:
    """
    Populate PostgreSQL with a synthetic ECD intelligence dataset.

    Important design principles:

    1. Organisation-owned operational data is synthetic.
    2. Geography uses realistic South African administrative levels.
    3. Children represent actual organisational enrolments.
    4. Population data is demographic data and is NOT enrolment data.
    5. A child's residential geography is independent of the
       franchisee location.
    6. Franchisees have operational lifecycle dates.
    7. Inactive franchisees have an inactive_date.
    8. Active franchisees have inactive_date = NULL.
    """

    db = SessionLocal()

    try:

        # ---------------------------------------------------------
        # PREVENT DUPLICATE SEEDING
        # ---------------------------------------------------------

        existing_count = db.query(Organisation).count()

        if existing_count > 0:
            print(
                "Database already contains ECD data."
            )
            return

        # ---------------------------------------------------------
        # ORGANISATION
        # ---------------------------------------------------------

        organisation = Organisation(
            name="BrightStart ECD Network",
            country="South Africa",
        )

        db.add(organisation)
        db.flush()

        # ---------------------------------------------------------
        # GEOGRAPHY
        #
        # Province
        #     ↓
        # Municipality
        #     ↓
        # Local Municipality
        #     ↓
        # Main Place
        #     ↓
        # Sub Place
        #     ↓
        # Small Area
        #
        # Geographic names are realistic.
        # Operational data is synthetic.
        # ---------------------------------------------------------

        geography = {

            "Gauteng": {
                "municipality": "City of Johannesburg",
                "municipality_type": "METROPOLITAN",
                "local_municipality": "Johannesburg",
                "main_places": [
                    "Soweto",
                    "Roodepoort",
                    "Johannesburg",
                ],
            },

            "Western Cape": {
                "municipality": "City of Cape Town",
                "municipality_type": "METROPOLITAN",
                "local_municipality": "Cape Town",
                "main_places": [
                    "Khayelitsha",
                    "Mitchells Plain",
                    "Bellville",
                ],
            },

            "KwaZulu-Natal": {
                "municipality": "eThekwini",
                "municipality_type": "METROPOLITAN",
                "local_municipality": "eThekwini",
                "main_places": [
                    "Umlazi",
                    "KwaMashu",
                    "Pinetown",
                ],
            },
        }

        provinces = {}

        for province_name, data in geography.items():

            # -----------------------------------------------------
            # PROVINCE
            # -----------------------------------------------------

            province = Province(
                name=province_name,
            )

            db.add(province)
            db.flush()

            provinces[province_name] = province

            # -----------------------------------------------------
            # MUNICIPALITY
            # -----------------------------------------------------

            municipality = Municipality(
                province_id=province.id,
                name=data["municipality"],
                municipality_type=data["municipality_type"],
            )

            db.add(municipality)
            db.flush()

            # -----------------------------------------------------
            # LOCAL MUNICIPALITY
            # -----------------------------------------------------

            local_municipality = LocalMunicipality(
                municipality_id=municipality.id,
                name=data["local_municipality"],
            )

            db.add(local_municipality)
            db.flush()

            # -----------------------------------------------------
            # MAIN PLACES
            # -----------------------------------------------------

            for main_place_name in data["main_places"]:

                main_place = MainPlace(
                    local_municipality_id=local_municipality.id,
                    name=main_place_name,
                )

                db.add(main_place)
                db.flush()

                # -------------------------------------------------
                # SUB PLACES
                # -------------------------------------------------

                for sub_index in range(1, 4):

                    sub_place = SubPlace(
                        main_place_id=main_place.id,
                        name=(
                            f"{main_place_name} "
                            f"Subplace {sub_index}"
                        ),
                    )

                    db.add(sub_place)
                    db.flush()

                    # ---------------------------------------------
                    # SMALL AREAS
                    # ---------------------------------------------

                    for area_index in range(1, 4):

                        small_area = SmallArea(
                            sub_place_id=sub_place.id,

                            name=(
                                f"{main_place_name} "
                                f"Small Area {area_index}"
                            ),

                            census_code=(
                                f"{province.id:02d}"
                                f"{main_place.id:03d}"
                                f"{sub_place.id:03d}"
                                f"{area_index:02d}"
                            ),

                            area_km2=round(
                                random.uniform(
                                    0.5,
                                    3.0,
                                ),
                                2,
                            ),
                        )

                        db.add(small_area)

        db.flush()

        # ---------------------------------------------------------
        # COACHES
        # ---------------------------------------------------------

        coaches = []

        for i in range(1, 13):

            coach = Coach(
                organisation_id=organisation.id,
                name=f"Coach {i:02d}",
            )

            db.add(coach)
            coaches.append(coach)

        db.flush()

        # ---------------------------------------------------------
        # FRANCHISEES
        #
        # Lifecycle:
        #
        # start_date
        #     ↓
        # active period
        #     ↓
        # inactive_date (only if inactive)
        #
        # Active franchisee:
        #
        #     status = ACTIVE
        #     inactive_date = NULL
        #
        # Inactive franchisee:
        #
        #     status = INACTIVE
        #     inactive_date > start_date
        # ---------------------------------------------------------

        small_areas = db.query(SmallArea).all()

        franchisees = []

        for i in range(1, 61):

            franchisee_small_area = random.choice(
                small_areas
            )

            coach = random.choice(
                coaches
            )

            status = random.choices(
                [
                    "ACTIVE",
                    "INACTIVE",
                ],
                weights=[
                    0.92,
                    0.08,
                ],
            )[0]

            # -----------------------------------------------------
            # FRANCHISEE START DATE
            #
            # Generate historical operational start dates.
            # -----------------------------------------------------

            start_year = random.choice(
                [
                    2022,
                    2023,
                    2024,
                    2025,
                ]
            )

            start_month = random.randint(
                1,
                12,
            )

            start_day = random.randint(
                1,
                28,
            )

            start_date = date(
                start_year,
                start_month,
                start_day,
            )

            # -----------------------------------------------------
            # INACTIVE DATE
            #
            # Active franchisees:
            #
            #     inactive_date = None
            #
            # Inactive franchisees:
            #
            #     inactive_date is after start_date.
            # -----------------------------------------------------

            inactive_date = None

            if status == "INACTIVE":

                # Generate an inactive date between
                # 2025 and mid-2026.

                inactive_year = random.choice(
                    [
                        2025,
                        2026,
                    ]
                )

                inactive_month = random.randint(
                    1,
                    6,
                )

                inactive_day = random.randint(
                    1,
                    28,
                )

                candidate_inactive_date = date(
                    inactive_year,
                    inactive_month,
                    inactive_day,
                )

                # Ensure lifecycle chronology is valid.
                #
                # If the generated date is before the start date,
                # place the start date earlier.

                if candidate_inactive_date <= start_date:

                    start_date = date(
                        2022,
                        random.randint(
                            1,
                            6,
                        ),
                        random.randint(
                            1,
                            28,
                        ),
                    )

                inactive_date = candidate_inactive_date

            # -----------------------------------------------------
            # CREATE FRANCHISEE
            # -----------------------------------------------------

            franchisee = Franchisee(
                organisation_id=organisation.id,

                small_area_id=(
                    franchisee_small_area.id
                ),

                coach_id=coach.id,

                name=f"Franchisee {i:03d}",

                status=status,

                capacity=random.randint(
                    30,
                    80,
                ),

                start_date=start_date,

                inactive_date=inactive_date,
            )

            db.add(franchisee)
            franchisees.append(franchisee)

        db.flush()

        # ---------------------------------------------------------
        # CHILDREN
        #
        # These represent actual children enrolled in the
        # organisation.
        #
        # They are NOT derived from population statistics.
        #
        # Residential geography is independent from the
        # franchisee operating geography.
        # ---------------------------------------------------------

        children = []

        for franchisee in franchisees:

            # Only active franchisees enrol children.
            if franchisee.status != "ACTIVE":
                continue

            # -----------------------------------------------------
            # SYNTHETIC PERFORMANCE PATTERNS
            # -----------------------------------------------------

            if franchisee.id % 10 == 0:

                target_enrolment = int(
                    franchisee.capacity * 0.45
                )

            elif franchisee.id % 7 == 0:

                target_enrolment = int(
                    franchisee.capacity * 0.70
                )

            else:

                target_enrolment = int(
                    franchisee.capacity
                    * random.uniform(
                        0.65,
                        0.95,
                    )
                )

            # -----------------------------------------------------
            # CREATE CHILDREN
            # -----------------------------------------------------

            for _ in range(
                target_enrolment
            ):

                # -------------------------------------------------
                # RESIDENTIAL GEOGRAPHY
                #
                # A child does not necessarily live in the same
                # Small Area where their ECD programme operates.
                # -------------------------------------------------

                residential_small_area = random.choice(
                    small_areas
                )

                # -------------------------------------------------
                # DATE OF BIRTH
                # -------------------------------------------------

                birth_year = random.choice(
                    [
                        2020,
                        2021,
                        2022,
                        2023,
                        2024,
                    ]
                )

                birth_month = random.randint(
                    1,
                    12,
                )

                birth_day = random.randint(
                    1,
                    28,
                )

                birth_date = date(
                    birth_year,
                    birth_month,
                    birth_day,
                )

                # -------------------------------------------------
                # ENROLMENT DATE
                # -------------------------------------------------

                enrolment_date = date(
                    2025,
                    random.randint(
                        1,
                        6,
                    ),
                    random.randint(
                        1,
                        28,
                    ),
                )

                child = Child(
                    organisation_id=organisation.id,

                    franchisee_id=franchisee.id,

                    residential_small_area_id=(
                        residential_small_area.id
                    ),

                    date_of_birth=birth_date,

                    enrolment_date=enrolment_date,

                    status="ENROLLED",
                )

                db.add(child)
                children.append(child)

        db.flush()

        # ---------------------------------------------------------
        # ATTENDANCE
        # ---------------------------------------------------------

        for child in children:

            for month in range(
                1,
                7,
            ):

                attendance_probability = random.uniform(
                    0.70,
                    0.95,
                )

                for day in range(
                    1,
                    21,
                ):

                    attendance_date = date(
                        2026,
                        month,
                        day,
                    )

                    attended = (
                        1
                        if random.random()
                        < attendance_probability
                        else 0
                    )

                    db.add(
                        Attendance(
                            child_id=child.id,

                            attendance_date=(
                                attendance_date
                            ),

                            attended=attended,
                        )
                    )

        # ---------------------------------------------------------
        # MONTHLY METRICS
        # ---------------------------------------------------------

        for franchisee in franchisees:

            if franchisee.status != "ACTIVE":
                continue

            franchisee_children = [
                child
                for child in children
                if child.franchisee_id
                == franchisee.id
            ]

            enrolled = len(
                franchisee_children
            )

            for month in range(
                1,
                7,
            ):

                attendance_rate = random.uniform(
                    0.72,
                    0.96,
                )

                capacity_utilisation = (
                    enrolled
                    / franchisee.capacity
                )

                new_enrolments = random.randint(
                    0,
                    8,
                )

                exits = random.randint(
                    0,
                    4,
                )

                db.add(
                    MonthlyMetric(
                        franchisee_id=franchisee.id,

                        month=date(
                            2026,
                            month,
                            1,
                        ),

                        enrolled_children=enrolled,

                        attendance_rate=round(
                            attendance_rate,
                            3,
                        ),

                        capacity_utilisation=round(
                            capacity_utilisation,
                            3,
                        ),

                        new_enrolments=(
                            new_enrolments
                        ),

                        exits=exits,
                    )
                )

        # ---------------------------------------------------------
        # POPULATION SNAPSHOTS
        #
        # These represent demographic population.
        #
        # They do NOT represent ECD enrolment.
        #
        # children_5_9 does NOT mean ECD enrolment.
        #
        # Children aged 5-9 may already be attending primary
        # school.
        # ---------------------------------------------------------

        for small_area in small_areas:

            population_total = random.randint(
                800,
                12000,
            )

            children_0_4 = int(
                population_total
                * random.uniform(
                    0.07,
                    0.14,
                )
            )

            children_5_9 = int(
                population_total
                * random.uniform(
                    0.07,
                    0.14,
                )
            )

            households = int(
                population_total
                / random.uniform(
                    2.8,
                    4.5,
                )
            )

            db.add(
                PopulationSnapshot(
                    small_area_id=small_area.id,

                    census_year=2022,

                    population_total=(
                        population_total
                    ),

                    children_0_4=(
                        children_0_4
                    ),

                    children_5_9=(
                        children_5_9
                    ),

                    households=(
                        households
                    ),
                )
            )

        # ---------------------------------------------------------
        # COMMIT
        # ---------------------------------------------------------

        db.commit()

        # ---------------------------------------------------------
        # SUMMARY
        # ---------------------------------------------------------

        active_franchisees = sum(
            1
            for franchisee in franchisees
            if franchisee.status == "ACTIVE"
        )

        inactive_franchisees = sum(
            1
            for franchisee in franchisees
            if franchisee.status == "INACTIVE"
        )

        print(
            "Successfully seeded the synthetic "
            "ECD intelligence dataset."
        )

        print(
            f"Small areas: {len(small_areas)}"
        )

        print(
            f"Franchisees: {len(franchisees)}"
        )

        print(
            f"Active franchisees: "
            f"{active_franchisees}"
        )

        print(
            f"Inactive franchisees: "
            f"{inactive_franchisees}"
        )

        print(
            f"Children: {len(children)}"
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# -------------------------------------------------------------
# ENTRY POINT
# -------------------------------------------------------------

if __name__ == "__main__":

    create_tables()

    seed_database()