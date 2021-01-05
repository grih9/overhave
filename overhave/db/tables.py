# pylint: disable=C0121
from __future__ import annotations

from typing import Optional, cast

import sqlalchemy as sa
import sqlalchemy_utils as su
from flask import url_for
from sqlalchemy import orm as so

from overhave.db.base import Base, PrimaryKeyMixin, PrimaryKeyWithoutDateMixin
from overhave.db.statuses import EmulationStatus, TestRunStatus
from overhave.db.types import ARRAY_TYPE, DATETIME_TYPE, INT_TYPE, LONG_STR_TYPE, SHORT_STR_TYPE, TEXT_TYPE
from overhave.db.users import UserRole


class FeatureType(Base, PrimaryKeyWithoutDateMixin):
    name = sa.Column(sa.Text, unique=True, nullable=False, doc='Feature types choice')

    def __repr__(self) -> str:
        return cast(str, self.name.upper())


@su.generic_repr('name', 'last_edited_by')
class Feature(Base, PrimaryKeyMixin):
    name = sa.Column(LONG_STR_TYPE, doc="Feature name", nullable=False, unique=True)
    author = sa.Column(
        SHORT_STR_TYPE, sa.ForeignKey(UserRole.login), doc="Feature author login", nullable=False, index=True
    )
    type_id = sa.Column(INT_TYPE, sa.ForeignKey(FeatureType.id), nullable=False, doc='Feature types choice')
    task = sa.Column(ARRAY_TYPE, doc="Feature tasks list", nullable=False)
    last_edited_by = sa.Column(SHORT_STR_TYPE, doc="Last feature editor login", nullable=False)
    released = sa.Column(sa.Boolean, doc="Feature release state boolean", nullable=False, default=False)

    feature_type = so.relationship(FeatureType)
    user = so.relationship(UserRole)


@su.generic_repr('feature_id')
class Scenario(Base, PrimaryKeyMixin):
    feature_id = sa.Column(INT_TYPE, sa.ForeignKey(Feature.id), nullable=False, unique=True)
    text = sa.Column(TEXT_TYPE, doc="Text storage for scenarios in feature")

    feature = so.relationship(Feature, backref=so.backref("scenario", cascade="all, delete-orphan"))


class TestRun(Base, PrimaryKeyMixin):
    scenario_id = sa.Column(INT_TYPE, sa.ForeignKey(Scenario.id), nullable=False, index=True)
    name = sa.Column(LONG_STR_TYPE, nullable=False)
    start = sa.Column(DATETIME_TYPE, doc="Test start time", nullable=False)
    end = sa.Column(DATETIME_TYPE, doc="Test finish time")
    executed_by = sa.Column(SHORT_STR_TYPE, doc="Test executor login", nullable=False)

    status = sa.Column(sa.Enum(TestRunStatus), doc="Current test status")
    report = sa.Column(TEXT_TYPE, doc="Relative report URL")
    traceback = sa.Column(TEXT_TYPE, doc="Text storage for error traceback")

    scenario = so.relationship(Scenario, backref=so.backref("test_runs", cascade="all, delete-orphan"))


class DraftQuery(so.Query):
    def as_unique(self, test_run_id: int) -> Draft:
        with self.session.no_autoflush:
            run = self.session.query(TestRun).get(test_run_id)
            draft: Optional[Draft] = self.session.query(Draft).filter(
                Draft.test_run_id == run.id, Draft.text == run.scenario.text
            ).one_or_none()

        if draft:
            return draft

        return Draft(  # type: ignore
            test_run_id=test_run_id, feature_id=run.scenario.feature_id, text=run.scenario.text
        )


class Draft(Base, PrimaryKeyMixin):

    __query_cls__ = DraftQuery

    feature_id = sa.Column(INT_TYPE, sa.ForeignKey(Feature.id), nullable=False, index=True)
    test_run_id = sa.Column(INT_TYPE, sa.ForeignKey(TestRun.id), nullable=False)
    text = sa.Column(TEXT_TYPE, doc="Released scenario text")
    pr_url = sa.Column(sa.Text, doc="Absolute pull-request URL", nullable=True)

    feature = so.relationship(Feature, backref=so.backref("versions", cascade="all, delete-orphan"))

    __table_args__ = (sa.UniqueConstraint(test_run_id),)

    def __html__(self) -> str:
        return f'<a href="{url_for("draft.details_view", id=self.id)}">Draft: {self.id}</a>'


@su.generic_repr('id', 'name', 'created_by')
class TestUser(Base, PrimaryKeyMixin):
    name = sa.Column(LONG_STR_TYPE, nullable=False, unique=True)
    feature_type_id = sa.Column(INT_TYPE, sa.ForeignKey(FeatureType.id), nullable=False, doc='Feature types choice')
    specification = sa.Column(sa.JSON(none_as_null=True))
    created_by = sa.Column(SHORT_STR_TYPE, sa.ForeignKey(UserRole.login), doc="Author login", nullable=False)

    feature_type = so.relationship(FeatureType)
    creator = so.relationship(UserRole)


class Emulation(Base, PrimaryKeyMixin):
    name = sa.Column(LONG_STR_TYPE, nullable=False, unique=True)
    test_user_id = sa.Column(INT_TYPE, sa.ForeignKey(TestUser.id), nullable=False, doc='Test user ID')
    command = sa.Column(TEXT_TYPE, nullable=False, doc="Command for emulator's execution")
    created_by = sa.Column(SHORT_STR_TYPE, sa.ForeignKey(UserRole.login), doc="Author login", nullable=False)

    test_user = so.relationship(TestUser)
    creator = so.relationship(UserRole)


class EmulationRun(Base, PrimaryKeyMixin):
    __tablename__ = 'emulation_run'  # type: ignore
    emulation_id = sa.Column(INT_TYPE, sa.ForeignKey(Emulation.id), nullable=False, index=True)
    status = sa.Column(sa.Enum(EmulationStatus), doc="Current emulation status", nullable=False)
    changed_at = sa.Column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    port = sa.Column(INT_TYPE, doc="Port for emulation")
    traceback = sa.Column(TEXT_TYPE, doc="Text storage for error traceback")

    emulation = so.relationship(Emulation, backref=so.backref("emulation_runs", cascade="all, delete-orphan"))

    def __init__(self, emulation_id: int):
        self.emulation_id = emulation_id
        self.status = EmulationStatus.CREATED