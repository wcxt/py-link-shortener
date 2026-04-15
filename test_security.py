from datetime import timedelta
import time
import jwt
from database import User
from security import OAuth2PasswordException, authenticate_user, create_access_token, decode_access_token, get_current_enabled_user, get_current_user, get_hashed_password, verify_password
import pytest
from unittest.mock import Mock, patch

def test_verify_password():
    test_plain_password = "password"
    test_hashed_password = get_hashed_password(test_plain_password)

    assert verify_password(test_plain_password, test_hashed_password)

def test_verify_password_incorrect():
    test_plain_password = "password"
    test_hashed_password = get_hashed_password("password1")

    assert verify_password(test_plain_password, test_hashed_password) == False

def test_get_hashed_password_different():
    test_plain_password = "password"

    hashed_password = get_hashed_password(test_plain_password)
    hashed_password2 = get_hashed_password(test_plain_password)

    assert hashed_password != hashed_password2

def test_get_hashed_password():
    test_plain_password = "password"

    hashed_password = get_hashed_password(test_plain_password)
    assert hashed_password is not None
    assert isinstance(hashed_password, str)
    assert len(hashed_password) > 0

def test_create_and_decode_access_token():
    test_data = {"sub": "123"}
    encoded = create_access_token(test_data)
    
    assert encoded is not None
    assert isinstance(encoded, str)
    assert len(encoded) > 0

    decoded = decode_access_token(encoded)

    assert isinstance(decoded["exp"], int)
    assert decoded["exp"] > time.time()
    assert decoded["sub"] == test_data["sub"]

def test_decode_access_token_incorrect():
    with pytest.raises(jwt.InvalidTokenError):
        _ = decode_access_token("")

def test_create_and_decode_access_token_with_custom_expires():
    test_data = {"sub": "123"}
    before = time.time()
    encoded = create_access_token(test_data, expires_delta=timedelta(minutes=10))
    
    decoded = decode_access_token(encoded)

    assert decoded["sub"] == test_data["sub"]
    assert isinstance(decoded["exp"], int)

    after = time.time()

    assert decoded["exp"] > before
    assert decoded["exp"] < after + 10 * 60 

def test_authenticate_user():
    test_email = "user@example.com"
    test_password = "password"
    test_user = User(email=test_email, password_hash=get_hashed_password(test_password))

    session_mock = Mock()
    result_mock = Mock()

    result_mock.first.return_value = test_user
    session_mock.exec.return_value = result_mock

    result = authenticate_user(session_mock, test_email, test_password)
    assert result == test_user


def test_authenticate_user_disabled():
    test_email = "user@example.com"
    test_password = "password"

    session_mock = Mock()
    result_mock = Mock()

    result_mock.first.return_value = User(email=test_email,
                                          password_hash=get_hashed_password(test_password),
                                          disabled=True)
    session_mock.exec.return_value = result_mock

    result = authenticate_user(session_mock, test_email, test_password)
    assert result is None

def test_authenticate_user_incorrect_password():
    test_email = "user@example.com"
    test_password = "password"

    session_mock = Mock()
    result_mock = Mock()

    result_mock.first.return_value = User(email=test_email,
                                          password_hash=get_hashed_password(test_password))
    session_mock.exec.return_value = result_mock

    result = authenticate_user(session_mock, test_email, "password1")
    assert result is None

def test_get_current_user():
    test_user = User(email="user@example.com", password_hash="password", disabled=True)

    session_mock = Mock()

    result_mock = Mock()
    result_mock.first.return_value = test_user
    session_mock.exec.return_value = result_mock

    with patch("security.decode_access_token") as mock_decode:
        mock_decode.return_value = {"sub": "123"}

        user = get_current_user(session_mock, "token")
        assert user == test_user
 
def test_get_current_user_invalid_token():
    session = Mock()

    with patch("security.decode_access_token", side_effect=jwt.InvalidTokenError):
        with pytest.raises(OAuth2PasswordException, check=lambda e: e.error == "invalid_token"):
            _ = get_current_user(session, "bad_token")

def test_get_current_user_invalid_sub():
    session = Mock()

    with patch("security.decode_access_token") as mock_decode:
        mock_decode.return_value = {"sub": 123}

        with pytest.raises(OAuth2PasswordException, check=lambda e: e.error == "invalid_token"):
            _ = get_current_user(session, "token")

def test_get_current_user_not_found():
    session_mock = Mock()

    result_mock = Mock()
    result_mock.first.return_value = None
    session_mock.exec.return_value = result_mock

    with patch("security.decode_access_token") as mock_decode:
        mock_decode.return_value = {"sub": "123"}

        with pytest.raises(OAuth2PasswordException, check=lambda e: e.error == "invalid_token"):
            _ = get_current_user(session_mock, "token")

def test_get_current_enabled_user():
     test_user = User(email="user@example.com", password_hash="1a2b3c4d")

     user = get_current_enabled_user(test_user)
     assert user == test_user

def test_get_current_enabled_user_disabled():
     user = User(email="user@example.com", password_hash="1a2b3c4d", disabled=True)

     with pytest.raises(OAuth2PasswordException, check=lambda e: e.error == "invalid_token"):
         _ = get_current_enabled_user(user)
