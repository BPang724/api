import re
from urllib.parse import parse_qs, urlsplit

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.db import get_db
from core.security import get_experiment_member
from models.dataset import Dataset, Video
from repositories import datasets as dataset_repository
from schemas.datasets import (
    DatasetCreate,
    DatasetDetail,
    DatasetSummary,
    DatasetUpdate,
    DatasetVideoResponse,
    GroundTruthResponse,
    GroundTruthUpdate,
    VideoCreate,
)

router = APIRouter(
    prefix="/datasets",
    tags=["datasets"],
    dependencies=[Depends(get_experiment_member)],
)
videos_router = APIRouter(
    prefix="/videos",
    tags=["videos"],
    dependencies=[Depends(get_experiment_member)],
)

YOUTUBE_VIDEO_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")
YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "youtu.be",
    "www.youtu.be",
}


def _youtube_video_id(value: str) -> str:
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Enter a valid YouTube video URL.",
        ) from None

    if (
        parsed.scheme not in {"http", "https"}
        or hostname not in YOUTUBE_HOSTS
        or port not in {None, 80, 443}
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Enter a valid YouTube video URL.",
        )

    path_parts = [part for part in parsed.path.split("/") if part]
    if hostname.endswith("youtu.be"):
        video_id = path_parts[0] if len(path_parts) == 1 else None
    elif parsed.path == "/watch":
        video_ids = parse_qs(parsed.query).get("v", [])
        video_id = video_ids[0] if len(video_ids) == 1 else None
    elif len(path_parts) == 2 and path_parts[0] in {"embed", "shorts", "live"}:
        video_id = path_parts[1]
    else:
        video_id = None

    if not video_id or not YOUTUBE_VIDEO_ID_PATTERN.fullmatch(video_id):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Enter a valid YouTube video URL.",
        )
    return video_id


def _dataset_summary(dataset: Dataset, video_count: int = 0) -> DatasetSummary:
    return DatasetSummary(
        id=dataset.id,
        name=dataset.name,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
        video_count=video_count,
    )


def _dataset_video_response(video: Video) -> DatasetVideoResponse:
    return DatasetVideoResponse(
        id=video.id,
        youtube_id=video.youtube_id,
        url=video.url,
        title=video.title,
        duration_seconds=video.duration_seconds,
        ground_truth_timestamps=[
            timestamp.timestamp_seconds
            for timestamp in video.ground_truth_timestamps
        ],
    )


def _raise_dataset_name_conflict(error: IntegrityError) -> None:
    diagnostic = getattr(error.orig, "diag", None)
    if getattr(diagnostic, "constraint_name", None) == "uq_datasets_name_lower":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A Dataset with this name already exists.",
        ) from error
    raise error


@router.get("", response_model=list[DatasetSummary])
def list_datasets(
    response: Response,
    db: Session = Depends(get_db),
) -> list[DatasetSummary]:
    response.headers["Cache-Control"] = "no-store"
    return [
        _dataset_summary(dataset, video_count)
        for dataset, video_count in dataset_repository.list_datasets(db)
    ]


@router.get("/{dataset_id}", response_model=DatasetDetail)
def get_dataset(
    response: Response,
    dataset_id: int = Path(gt=0),
    db: Session = Depends(get_db),
) -> DatasetDetail:
    response.headers["Cache-Control"] = "no-store"
    dataset = dataset_repository.get_dataset(db, dataset_id)
    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )

    return DatasetDetail(
        id=dataset.id,
        name=dataset.name,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
        videos=[
            _dataset_video_response(link.video)
            for link in dataset.video_links
        ],
    )


@router.post(
    "",
    response_model=DatasetSummary,
    status_code=status.HTTP_201_CREATED,
)
def create_dataset(
    dataset_data: DatasetCreate,
    response: Response,
    db: Session = Depends(get_db),
) -> DatasetSummary:
    response.headers["Cache-Control"] = "no-store"
    try:
        dataset = dataset_repository.create_dataset(db, dataset_data.name)
    except IntegrityError as error:
        db.rollback()
        _raise_dataset_name_conflict(error)
    return _dataset_summary(dataset)


@router.patch("/{dataset_id}", response_model=DatasetSummary)
def update_dataset(
    dataset_data: DatasetUpdate,
    response: Response,
    dataset_id: int = Path(gt=0),
    db: Session = Depends(get_db),
) -> DatasetSummary:
    response.headers["Cache-Control"] = "no-store"
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )
    try:
        dataset = dataset_repository.update_dataset(
            db, dataset, dataset_data.name
        )
    except IntegrityError as error:
        db.rollback()
        _raise_dataset_name_conflict(error)
    return _dataset_summary(dataset)


@router.delete(
    "/{dataset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_dataset(
    dataset_id: int = Path(gt=0),
    db: Session = Depends(get_db),
) -> Response:
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )
    dataset_repository.delete_dataset(db, dataset)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{dataset_id}/videos",
    response_model=DatasetVideoResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_video_to_dataset(
    video_data: VideoCreate,
    response: Response,
    dataset_id: int = Path(gt=0),
    db: Session = Depends(get_db),
) -> DatasetVideoResponse:
    response.headers["Cache-Control"] = "no-store"
    if db.get(Dataset, dataset_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )

    youtube_id = _youtube_video_id(video_data.url)
    video = dataset_repository.add_video_to_dataset(
        db,
        dataset_id,
        youtube_id,
        f"https://www.youtube.com/watch?v={youtube_id}",
    )
    if video is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This video is already in the Dataset.",
        )

    video = dataset_repository.get_video(db, video.id)
    if video is None:
        raise RuntimeError("Video disappeared after being added to Dataset.")
    return _dataset_video_response(video)


@router.delete(
    "/{dataset_id}/videos/{video_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_video_from_dataset(
    dataset_id: int = Path(gt=0),
    video_id: int = Path(gt=0),
    db: Session = Depends(get_db),
) -> Response:
    if db.get(Dataset, dataset_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )
    if not dataset_repository.remove_video_from_dataset(
        db, dataset_id, video_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video is not in this Dataset.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@videos_router.get("/{video_id}/timestamps", response_model=GroundTruthResponse)
def get_video_timestamps(
    response: Response,
    video_id: int = Path(gt=0),
    db: Session = Depends(get_db),
) -> GroundTruthResponse:
    response.headers["Cache-Control"] = "no-store"
    if dataset_repository.get_video(db, video_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found.",
        )
    return GroundTruthResponse(
        video_id=video_id,
        timestamps=dataset_repository.get_video_timestamps(db, video_id),
    )


@videos_router.put("/{video_id}/timestamps", response_model=GroundTruthResponse)
def replace_video_timestamps(
    timestamp_data: GroundTruthUpdate,
    response: Response,
    video_id: int = Path(gt=0),
    db: Session = Depends(get_db),
) -> GroundTruthResponse:
    response.headers["Cache-Control"] = "no-store"
    video = dataset_repository.get_video(db, video_id)
    if video is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found.",
        )
    if (
        video.duration_seconds is not None
        and any(value > video.duration_seconds for value in timestamp_data.timestamps)
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="A timestamp cannot exceed the video duration.",
        )
    try:
        timestamps = dataset_repository.replace_video_timestamps(
            db, video_id, timestamp_data.timestamps
        )
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ground Truth changed concurrently. Reload and try again.",
        ) from error
    return GroundTruthResponse(video_id=video_id, timestamps=timestamps)
