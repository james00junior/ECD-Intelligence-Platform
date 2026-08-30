from datetime import date
import random

from app.database.database import Base
from app.database.database import SessionLocal
from app.database.database import engine

from app.database.models import SurveyResponse


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


def seed_database() -> None:
    db = SessionLocal()

    existing_count = db.query(SurveyResponse).count()

    if existing_count > 0:
        print("Database already contains data.")
        db.close()
        return

    countries = [
        "South Africa",
        "United Kingdom",
        "Kenya",
    ]

    age_groups = [
        "18-24",
        "25-34",
        "35-44",
        "45-54",
        "55+",
    ]

    segments = [
        "Budget",
        "Standard",
        "Premium",
    ]

    responses = []

    for _ in range(1000):

        country = random.choice(countries)

        if country == "South Africa":

            satisfaction_score = round(
                random.normalvariate(6.8, 1.2),
                1,
            )

            nps_score = int(
                random.normalvariate(15, 25)
            )

        elif country == "United Kingdom":

            satisfaction_score = round(
                random.normalvariate(7.5, 1.0),
                1,
            )

            nps_score = int(
                random.normalvariate(30, 20)
            )

        else:

            satisfaction_score = round(
                random.normalvariate(7.1, 1.1),
                1,
            )

            nps_score = int(
                random.normalvariate(20, 22)
            )

        satisfaction_score = max(
            1.0,
            min(10.0, satisfaction_score),
        )

        nps_score = max(
            -100,
            min(100, nps_score),
        )

        responses.append(
            SurveyResponse(
                country=country,
                age_group=random.choice(age_groups),
                customer_segment=random.choice(segments),
                satisfaction_score=satisfaction_score,
                nps_score=nps_score,
                response_date=date(
                    2026,
                    random.randint(1, 6),
                    random.randint(1, 28),
                ),
            )
        )

    db.add_all(responses)

    db.commit()

    db.close()

    print("Successfully seeded 1,000 survey responses.")


if __name__ == "__main__":

    create_tables()

    seed_database()
