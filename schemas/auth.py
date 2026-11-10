from pydantic import BaseModel, ConfigDict


class MemberProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str | None
    email: str
    picture: str | None
