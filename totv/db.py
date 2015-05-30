# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals, absolute_import
from contextlib import contextmanager
import logging
from os import getenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError, DBAPIError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

Base = declarative_base()
Base.__repr__ = lambda self: "<{}({})>".format(
    self.__class__.__name__,
    ', '.join(["{}={}".format(k, repr(self.__dict__[k])) for k in self.__dict__ if k[0] != '_'])
)

Session = sessionmaker()


class ToTVException(Exception):
    pass


class InternalError(ToTVException):
    pass


class DuplicateError(ToTVException):
    pass


def make_engine(url: str="", echo=True, init=True) -> Engine:
    if not url:
        url = getenv("SQLALCHEMY_URI")
        if not url:
            raise AssertionError("No url provided, and not found in env")
    engine = create_engine(url, echo=echo)
    if init:
        init_db(engine)
    Session.configure(bind=engine)
    return engine


def init_db(engine: Engine):
    Base.metadata.create_all(engine)


@contextmanager
def ctx(ses):
    """Provide a transactional scope around a series of operations."""
    try:
        yield ses
        ses.commit()
    except IntegrityError as e:
        ses.rollback()
        logger.exception("Tried to create duplicate record")
        raise DuplicateError(e)
    except DBAPIError as e:
        ses.rollback()
        logger.exception("Error committing transaction.")
        raise InternalError(e)


