import pytest
from faker import Faker
from pydantic import SecretStr

from overhave import db
from overhave.storage import SystemUserModel, SystemUserStorage
from tests.db_utils import count_queries


@pytest.mark.usefixtures("database")
@pytest.mark.parametrize("test_user_role", list(db.Role), indirect=True)
class TestSystemUserStorage:
    """Integration tests for :class:`TestSystemUserStorage`."""

    def test_get_existing_user(
        self, test_system_user_storage: SystemUserStorage, test_system_user: SystemUserModel
    ) -> None:
        with count_queries(1):
            user = test_system_user_storage.get_user(test_system_user.id)
        assert user is not None
        assert user == test_system_user

    def test_get_not_existing_user(
        self, test_system_user_storage: SystemUserStorage, test_system_user: SystemUserModel
    ) -> None:
        with count_queries(1):
            user = test_system_user_storage.get_user(test_system_user.id + 1)
        assert user is None

    @pytest.mark.parametrize("test_system_user_password", [None, SecretStr("secret password")])
    def test_get_existing_user_by_credits(
        self,
        test_system_user_storage: SystemUserStorage,
        test_system_user_password: SecretStr | None,
        test_user_role: db.Role,
        faker: Faker,
    ) -> None:
        with count_queries(1):
            created_user = test_system_user_storage.create_user(
                login=faker.word(), password=test_system_user_password, role=test_user_role
            )
        with count_queries(1):
            with db.create_session() as session:
                user = test_system_user_storage.get_user_by_credits(
                    session=session, login=created_user.login, password=created_user.password
                )
        assert user is not None
        assert user == created_user

    @pytest.mark.parametrize("test_system_user_password", [None, SecretStr("secret password")])
    def test_get_not_existing_user_by_credits(
        self,
        test_system_user_storage: SystemUserStorage,
        test_system_user_password: SecretStr | None,
        test_user_role: db.Role,
        faker: Faker,
    ) -> None:
        with count_queries(1):
            with db.create_session() as session:
                assert (
                    test_system_user_storage.get_user_by_credits(
                        session=session, login=faker.word(), password=test_system_user_password
                    )
                    is None
                )

    @pytest.mark.parametrize("test_new_user_role", list(db.Role))
    def test_update_user_role(
        self,
        test_system_user_storage: SystemUserStorage,
        test_system_user: SystemUserModel,
        test_new_user_role: db.Role,
    ) -> None:
        with count_queries(1):
            with db.create_session() as session:
                test_system_user_storage.update_user_role(
                    session=session, user_id=test_system_user.id, role=test_new_user_role
                )
        with count_queries(1):
            user = test_system_user_storage.get_user(test_system_user.id)
        assert user is not None
        assert user.role == test_new_user_role
