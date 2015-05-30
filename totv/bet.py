# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals, absolute_import
from datetime import datetime
import logging
from enum import IntEnum
from sqlalchemy import Column, Integer, DateTime
from totv import db
from totv.db import Base, Session

MIN_BET = 10
MAX_BET = 1000000


class BetState(IntEnum):
    # Bet has been opened successfully
    opened = 1

    # Awaiting responses from both parties to confirm result
    waiting = 2

    # Bet is closed, rewards have been distributed.
    closed = 3


class Bet(Base):
    __tablename__ = "bet"

    bet_id = Column(Integer, primary_key=True)
    person_a = Column(Integer, nullable=False)
    person_b = Column(Integer, nullable=False)
    state = Column(Integer, nullable=False, default=BetState.opened)
    created_on = Column(DateTime, default=datetime.now(), nullable=False)
    closed_on = Column(DateTime)

    def __init__(self, person_a: str, person_b: str, amount: int):
        amount = int(amount)
        self.person_a = person_a
        self.person_b = person_b
        if amount < MIN_BET or amount > MAX_BET:
            raise ValueError("Amount must be between {} and {}".format(MIN_BET, MAX_BET))
        self.amount = amount


def active_user_bets(session: Session, user_id: int) -> list:
    open_bets = session.query(Bet).\
        filter(Bet.person_a == user_id).\
        filter(Bet.state < BetState.closed).\
        all()
    return open_bets


def place(session: Session, bet: Bet) -> bool:
    try:
        with db.ctx(session):
            session.add(bet)
    except db.ToTVException:
        logging.exception("Failed to place bet")
        return False
    else:
        return True


