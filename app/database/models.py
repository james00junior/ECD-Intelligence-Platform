from datetime import date
from pgvector.sqlalchemy import Vector
from sqlalchemy import Date
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import (
    JSON,
    ForeignKey,
    Integer,
    String,
    Text,
)
from app.database.database import Base


class Organisation(Base):
    __tablename__ = "organisations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        unique=True,
        index=True,
    )

    country: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )


class KnowledgeSource(Base):
    __tablename__ = "knowledge_sources"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    organisation_id: Mapped[int] = mapped_column(
        ForeignKey("organisations.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    base_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    organisation_id: Mapped[int] = mapped_column(
        ForeignKey("organisations.id"),
        nullable=False,
        index=True,
    )

    knowledge_source_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_sources.id"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    document_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    source_uri: Mapped[str] = mapped_column(
        String(2000),
        nullable=False,
    )

    content_hash: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="active",
        index=True,
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    organisation_id: Mapped[int] = mapped_column(
        ForeignKey("organisations.id"),
        nullable=False,
        index=True,
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id"),
        nullable=False,
        index=True,
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    content_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(),
        nullable=True,
    )

    chunk_metadata: Mapped[dict | None] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
    )

class Province(Base):
    __tablename__ = "provinces"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )


class Municipality(Base):
    __tablename__ = "municipalities"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    province_id: Mapped[int] = mapped_column(
        ForeignKey("provinces.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )

    municipality_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )


class LocalMunicipality(Base):
    __tablename__ = "local_municipalities"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    municipality_id: Mapped[int] = mapped_column(
        ForeignKey("municipalities.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )


class MainPlace(Base):
    __tablename__ = "main_places"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    local_municipality_id: Mapped[int] = mapped_column(
        ForeignKey("local_municipalities.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )


class SubPlace(Base):
    __tablename__ = "sub_places"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    main_place_id: Mapped[int] = mapped_column(
        ForeignKey("main_places.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )


class SmallArea(Base):
    __tablename__ = "small_areas"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    sub_place_id: Mapped[int] = mapped_column(
        ForeignKey("sub_places.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )

    census_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
    )

    area_km2: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )


class Coach(Base):
    __tablename__ = "coaches"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    organisation_id: Mapped[int] = mapped_column(
        ForeignKey("organisations.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )


class Franchisee(Base):
    __tablename__ = "franchisees"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    organisation_id: Mapped[int] = mapped_column(
        ForeignKey("organisations.id"),
        nullable=False,
        index=True,
    )

    small_area_id: Mapped[int] = mapped_column(
        ForeignKey("small_areas.id"),
        nullable=False,
        index=True,
    )

    coach_id: Mapped[int] = mapped_column(
        ForeignKey("coaches.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    inactive_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        index=True,
    )

    capacity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )


class Child(Base):
    __tablename__ = "children"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    organisation_id: Mapped[int] = mapped_column(
        ForeignKey("organisations.id"),
        nullable=False,
        index=True,
    )

    franchisee_id: Mapped[int] = mapped_column(
        ForeignKey("franchisees.id"),
        nullable=False,
        index=True,
    )

    residential_small_area_id: Mapped[int] = mapped_column(
        ForeignKey("small_areas.id"),
        nullable=False,
        index=True,
    )

    date_of_birth: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    enrolment_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )


class Attendance(Base):
    __tablename__ = "attendance"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    child_id: Mapped[int] = mapped_column(
        ForeignKey("children.id"),
        nullable=False,
        index=True,
    )

    attendance_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    attended: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )


class MonthlyMetric(Base):
    __tablename__ = "monthly_metrics"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    franchisee_id: Mapped[int] = mapped_column(
        ForeignKey("franchisees.id"),
        nullable=False,
        index=True,
    )

    month: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    enrolled_children: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    attendance_rate: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    capacity_utilisation: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    new_enrolments: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    exits: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )


class PopulationSnapshot(Base):
    __tablename__ = "population_snapshots"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    small_area_id: Mapped[int] = mapped_column(
        ForeignKey("small_areas.id"),
        nullable=False,
        index=True,
    )

    census_year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    population_total: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    children_0_4: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    children_5_9: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    households: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )