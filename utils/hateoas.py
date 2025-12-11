from fastapi import Request
from typing import List
from models.hateoas import HATEOASLink

from models.user import User, UserRead

# -----------------------------------------------------------------------------
# User HATEOAS
# -----------------------------------------------------------------------------
def build_user_links(request: Request, user: User) -> List[HATEOASLink]:
    return [
        HATEOASLink(
            rel="self",
            href=str(request.url_for("get_user", user_id=user.id)),
            method="GET",
        ),
        HATEOASLink(
            rel="update",
            href=str(request.url_for("update_user", user_id=user.id)),
            method="PATCH",
        ),
        HATEOASLink(
            rel="delete",
            href=str(request.url_for("delete_user", user_id=user.id)),
            method="DELETE",
        ),
        HATEOASLink(
            rel="collection",
            href=str(request.url_for("list_users")),
            method="GET",
        ),
    ]

def hateoas_user(request: Request, user: User):
    links: List[HATEOASLink] = build_user_links(request, user)

    user_read = UserRead.model_validate(user)
    if links:
        user_read = user_read.model_copy(update={"links": links})

    return user_read