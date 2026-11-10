from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from models.member import Member


def upsert_google_member(
    db: Session,
    *,
    google_sub: str,
    email: str,
    name: str | None,
    picture: str | None,
) -> Member:
    statement = insert(Member).values(
        google_sub=google_sub,
        email=email,
        email_verified=True,
        name=name,
        picture=picture,
    )
    statement = statement.on_conflict_do_update(
        index_elements=[Member.google_sub],
        set_={
            "email": statement.excluded.email,
            "email_verified": statement.excluded.email_verified,
            "name": statement.excluded.name,
            "picture": statement.excluded.picture,
            "updated_at": func.now(),
        },
    ).returning(Member)

    member = db.scalars(statement).one()
    db.commit()
    return member
