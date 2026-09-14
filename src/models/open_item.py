from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

OpenItemType = Literal["decision_needed", "owner_missing", "conflict", "data_issue"]
OpenItemStatus = Literal["open", "assigned", "closed"]


class OpenItem(BaseModel):
    # TODO(mvp): spec section 4 doesn't list an id for OpenItem, but the session needs
    # to reference and close a specific item, so one is added here.
    id: str
    text: str
    type: OpenItemType
    raised_at: datetime
    proposed_owner: str | None = None
    status: OpenItemStatus = "open"
