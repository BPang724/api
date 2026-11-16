from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base


class Dataset(Base):
    __tablename__ = "datasets"
    __table_args__ = (
        CheckConstraint("length(btrim(name)) > 0", name="ck_datasets_name_not_blank"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger, Identity(), primary_key=True
    )
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    video_links: Mapped[list["DatasetVideo"]] = relationship(
        back_populates="dataset",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="DatasetVideo.video_id",
    )


class Video(Base):
    __tablename__ = "videos"
    __table_args__ = (
        CheckConstraint(
            "youtube_id ~ '^[A-Za-z0-9_-]{11}$'",
            name="ck_videos_youtube_id_format",
        ),
        CheckConstraint(
            "duration_seconds IS NULL OR duration_seconds >= 0",
            name="ck_videos_duration_nonnegative",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger, Identity(), primary_key=True
    )
    youtube_id: Mapped[str] = mapped_column(String(11), unique=True, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    dataset_links: Mapped[list["DatasetVideo"]] = relationship(
        back_populates="video",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    ground_truth_timestamps: Mapped[list["GroundTruthTimestamp"]] = relationship(
        back_populates="video",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="GroundTruthTimestamp.timestamp_seconds",
    )


class DatasetVideo(Base):
    __tablename__ = "dataset_videos"

    dataset_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("datasets.id", ondelete="CASCADE"),
        primary_key=True,
    )
    video_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("videos.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    dataset: Mapped[Dataset] = relationship(back_populates="video_links")
    video: Mapped[Video] = relationship(back_populates="dataset_links")


class GroundTruthTimestamp(Base):
    __tablename__ = "ground_truth_timestamps"
    __table_args__ = (
        CheckConstraint(
            "timestamp_seconds >= 0",
            name="ck_ground_truth_timestamps_nonnegative",
        ),
        UniqueConstraint(
            "video_id",
            "timestamp_seconds",
            name="uq_ground_truth_timestamps_video_time",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger, Identity(), primary_key=True
    )
    video_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("videos.id", ondelete="CASCADE"),
        nullable=False,
    )
    timestamp_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    video: Mapped[Video] = relationship(back_populates="ground_truth_timestamps")
