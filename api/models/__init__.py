# Import all models here for metadata creation
from .job import Job
from .asset import Asset
from .transcript import Transcript
from .segment import Segment
from .speaker import Speaker
from .embedding import Embedding
from .tag import Tag
from .setting import Setting

__all__ = [
    "Job",
    "Asset", 
    "Transcript",
    "Segment",
    "Speaker",
    "Embedding",
    "Tag",
    "Setting"
] 