"""Csw SQLALchemy base classes.

The following is a draft of a potential interactive session with the code,
serving more as a reminder for this intial dev stage than as any guidance for
a future API:

>>> from uuid import uuid1
>>> from sqlalchemy import create_engine
>>> from sqlalchemy.orm import sessionmaker
>>> from pycsw.repositories.sla.models import Record
>>> engine = create_engine("sqlite:///:memory:", echo=True)
>>> Session = sessionmaker()
>>> Session.configure(bind=engine)
>>> this_session = Session()
>>> sla_repo = CswSlaRepository(engine, this_session)
>>> sla_repo.create_db()
>>> record1 = Record(identifier=str(uuid1(), title="My phony csw record")
>>> record2 = Record(identifier=str(uuid1(), title="Another phony csw record")
>>> record3 = Record(identifier=str(uuid1(), title="One more phony csw record")
>>> sla_repo.session.add(record1)
>>> sla_repo.session.add(record2)
>>> sla_repo.session.add(record3)
>>> sla_repo.session.commit()

The CSW repository is associated with the CSW service (not the server).

"""


import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ... import exceptions
from ..repositorybase import CswRepository
from .models import Base
from .models import Record
from . import querytranslators


logger = logging.getLogger(__name__)


class CswSlaRepository(CswRepository):
    """SQLAlchemy base repository class."""

    _query_translators = {
        "csw:Record": querytranslators.translate_csw_record,
        "gmd:MD_Metadata": querytranslators.translate_gmd_md_record,
        "rim:SomeType,rim:AnotherType":
            querytranslators.translate_ebrim_record,
    }
    engine = None
    session = None

    def __init__(self, engine_url=None, echo=False,
                 query_translator_modules=None):
        super().__init__(
            extra_query_translator_modules=query_translator_modules)
        engine_url = (engine_url if engine_url is not None
                      else "sqlite:///:memory:")
        self.engine = create_engine(engine_url, echo=echo)
        self.session_factory = sessionmaker(bind=self.engine)

    def create_db(self):
        path = self.engine.url.database
        if self.engine.url.database != ":memory:":
            raise exceptions.PycswError("Non memory based databases are not "
                                        "supported yet")
        Base.metadata.create_all(self.engine)

    def get_record_by_id(self, id):
        session = self.session_factory()
        return session.query(Record).first()


