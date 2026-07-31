from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):

    id: int
    owner_id: int
    file_name: str
    file_path: str
    file_size: int
    content_type: str
    storage_node: str
    created_at: datetime

    class Config:
        from_attributes = True