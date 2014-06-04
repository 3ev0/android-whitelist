__author__ = 'ivo'

import logging
import os
import os.path

import sqlalchemy as sqla
from sqlalchemy.ext import declarative
from sqlalchemy import Date, Column,Integer, String, create_engine, Boolean, ForeignKey
from sqlalchemy.orm import sessionmaker, scoped_session, relationship

_log = logging.getLogger(__name__)
_Base = declarative.declarative_base()

class DbIf():
    def __init__(self, connstr):
        self.connstr = connstr
        self._engine = create_engine(self.connstr)
        self.Session = scoped_session(sessionmaker(bind=self._engine))
        _log.debug("DB Interface connection configured: %s", repr(self._engine))

    def init_db(self, dbinfos):
        _Base.metadata.create_all(self._engine, checkfirst=False)
        for k in dbinfos:
            self.Session.add(DbInfo(key=k, value=dbinfos[k]))
        self.Session.commit()
        _log.debug("Database (re)created at %s", self._engine)
        return True

    def get_db_info(self):
        return {ci.key:ci.val for ci in self.Session.query(DbInfo)}

    def add_db_info(self, key, value, replace=False):
        dbinfos = self.Session.query(DbInfo).filter(DbInfo.key==key).all()
        if len(dbinfos) > 0 and replace:
            for dbi in dbinfos:
                dbi.key = key
                dbi.value = value
        else:
            self.Session.add(DbInfo(key=key, value=value))
        self.Session.commit()
        return True

class DbInfo(_Base):
    __tablename__= "DbInfo"

    id = Column(Integer, primary_key=True)
    key = Column(String(4096), nullable=False)
    value = Column(String(4096))

    def __repr__(self):
        return "<DbInfo(id={:d}, key={}, value={})>".format(self.id, self.key, self.value)

class Indicator(_Base):
    __tablename__ = "Indicators"

    SCORE_HIGH = 50
    SCORE_MED = 10
    SCORE_LOW = 5
    SCORE_NEG_HIGH = -50

    id = Column(Integer, primary_key=True)
    score = Column(Integer)
    description = Column(String(4096))
    metafile_id = Column(Integer, ForeignKey("MetaFiles.id"))
    modulerun_id = Column(Integer, ForeignKey("ModuleRuns.id"))

    modulerun = relationship("ModuleRun")
    metafile = relationship("MetaFile")

    def __repr__(self):
        return "<Indicator(id={:d}, score={:d}, description={})>".format(self.id, self.score, self.description)


class ModuleRun(_Base):
    __tablename__ = "ModuleRuns"

    id = Column(Integer, primary_key=True)
    name = Column(String(4096), nullable=False, unique=True)
    config = Column(String(4096), nullable=False)

    def __repr__(self):
        return "<ModuleRun(id={:d}, fingerprint={})>".format(self.id, self.fingerprint)

class MetaFile(_Base):
    __tablename__ = "MetaFiles"

    id = Column(Integer, primary_key=True)
    path = Column(String(1024), index=True)
    extension = Column(String(256), index=True)
    uid = Column(sqla.Integer)
    gid = Column(sqla.Integer)
    stmode_type = Column(sqla.String(512))
    permissions = Column(Integer)
    lastaccess = Column(sqla.DateTime)
    lastmodified = Column(sqla.DateTime)
    created = Column(sqla.DateTime)
    size = Column(Integer)
    mimetype = Column(String(1024), index=True)
    magic = Column(String(4096))
    md5 = Column(String(256), nullable=False, index=True)
    sha1 = Column(String(256), nullable=False, index=True)
    sha256 = Column(String(256), nullable=False, index=True)
    ssdeep = Column(String(256))
    excluded = Column(Boolean, default=False)

    def __repr__(self):
        return "<MetaFile(id={:d}, path={}, md5={})>".format(self.id, self.path, self.md5)
