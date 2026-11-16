from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator


class DatasetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=60)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Dataset name cannot be blank.")
        return value


class DatasetUpdate(DatasetCreate):
    pass


class VideoCreate(BaseModel):
    url: str = Field(min_length=1, max_length=2048)


class GroundTruthUpdate(BaseModel):
    timestamps: list[StrictInt] = Field(max_length=5000)

    @field_validator("timestamps")
    @classmethod
    def validate_timestamps(cls, values: list[int]) -> list[int]:
        if any(value < 0 or value > 2_147_483_647 for value in values):
            raise ValueError("Timestamps must be between 0 and 2147483647 seconds.")
        if len(set(values)) != len(values):
            raise ValueError("Timestamps must not contain duplicates.")
        return sorted(values)


class DatasetSummary(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime
    video_count: int


class DatasetVideoResponse(BaseModel):
    id: int
    youtube_id: str
    url: str
    title: str | None
    duration_seconds: int | None
    ground_truth_timestamps: list[int]

    model_config = ConfigDict(from_attributes=True)


class DatasetDetail(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime
    videos: list[DatasetVideoResponse]

    model_config = ConfigDict(from_attributes=True)


class GroundTruthResponse(BaseModel):
    video_id: int
    timestamps: list[int]
