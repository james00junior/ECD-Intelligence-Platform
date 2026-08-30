from datetime import date

from sqlalchemy import Date
from sqlalchemy import Float
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.database.database import Base


class SurveyResponse(Base):
    __tablename__ = "survey_responses"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    country: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
    )

    age_group: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    customer_segment: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
    )

    satisfaction_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    nps_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    response_date: Mapped[date] = mapped_column(
        Date,
        index=True,
        nullable=False,
    )
