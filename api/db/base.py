from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData

# Create declarative base
Base = declarative_base()

# Import all models here for metadata creation
from .models.job import Job
from .models.asset import Asset
from .models.transcript import Transcript
from .models.segment import Segment
from .models.speaker import Speaker
from .models.embedding import Embedding
from .models.tag import Tag
from .models.setting import Setting 