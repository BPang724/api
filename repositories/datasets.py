from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, selectinload

from models.dataset import (
    Dataset,
    DatasetVideo,
    GroundTruthTimestamp,
    Video,
)


def list_datasets(db: Session) -> list[tuple[Dataset, int]]:
    statement = (
        select(Dataset, func.count(DatasetVideo.video_id).label("video_count"))
        .outerjoin(Dataset.video_links)
        .group_by(Dataset.id)
        .order_by(Dataset.id)
    )
    return [
        (dataset, video_count)
        for dataset, video_count in db.execute(statement)
    ]


def get_dataset(db: Session, dataset_id: int) -> Dataset | None:
    statement = (
        select(Dataset)
        .where(Dataset.id == dataset_id)
        .options(
            selectinload(Dataset.video_links)
            .selectinload(DatasetVideo.video)
            .selectinload(Video.ground_truth_timestamps)
        )
    )
    return db.scalar(statement)


def create_dataset(db: Session, name: str) -> Dataset:
    dataset = Dataset(name=name)
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


def update_dataset(db: Session, dataset: Dataset, name: str) -> Dataset:
    dataset.name = name
    db.flush()
    db.execute(
        update(Dataset)
        .where(Dataset.id == dataset.id)
        .values(updated_at=func.now())
    )
    db.commit()
    db.refresh(dataset)
    return dataset


def delete_dataset(db: Session, dataset: Dataset) -> None:
    db.delete(dataset)
    db.commit()


def add_video_to_dataset(
    db: Session,
    dataset_id: int,
    youtube_id: str,
    url: str,
    title: str,
    duration_seconds: int | None,
) -> Video | None:
    db.execute(
        insert(Video)
        .values(
            youtube_id=youtube_id,
            url=url,
            title=title,
            duration_seconds=duration_seconds,
        )
        .on_conflict_do_update(
            index_elements=[Video.youtube_id],
            set_={
                "url": url,
                "title": title,
                "duration_seconds": duration_seconds,
                "updated_at": func.now(),
            },
        )
    )
    video = db.scalar(select(Video).where(Video.youtube_id == youtube_id))
    if video is None:
        raise RuntimeError("Video was not available after insert.")

    association = db.scalar(
        insert(DatasetVideo)
        .values(dataset_id=dataset_id, video_id=video.id)
        .on_conflict_do_nothing(
            index_elements=[DatasetVideo.dataset_id, DatasetVideo.video_id]
        )
        .returning(DatasetVideo.video_id)
    )
    if association is None:
        db.rollback()
        return None

    db.commit()
    return video


def remove_video_from_dataset(
    db: Session,
    dataset_id: int,
    video_id: int,
) -> bool:
    result = db.execute(
        delete(DatasetVideo).where(
            DatasetVideo.dataset_id == dataset_id,
            DatasetVideo.video_id == video_id,
        )
    )
    db.commit()
    return result.rowcount > 0


def get_video(db: Session, video_id: int) -> Video | None:
    return db.get(Video, video_id)


def get_dataset_video(
    db: Session,
    dataset_id: int,
    youtube_id: str,
) -> Video | None:
    statement = (
        select(Video)
        .join(Video.dataset_links)
        .where(
            DatasetVideo.dataset_id == dataset_id,
            Video.youtube_id == youtube_id,
        )
    )
    return db.scalar(statement)


def get_video_timestamps(db: Session, video_id: int) -> list[int]:
    statement = (
        select(GroundTruthTimestamp.timestamp_seconds)
        .where(GroundTruthTimestamp.video_id == video_id)
        .order_by(GroundTruthTimestamp.timestamp_seconds)
    )
    return list(db.scalars(statement))


def replace_video_timestamps(
    db: Session,
    video_id: int,
    timestamps: list[int],
) -> list[int]:
    db.execute(
        delete(GroundTruthTimestamp).where(
            GroundTruthTimestamp.video_id == video_id
        )
    )
    db.add_all(
        GroundTruthTimestamp(video_id=video_id, timestamp_seconds=value)
        for value in timestamps
    )
    db.commit()
    return timestamps
