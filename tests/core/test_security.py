from datetime import timedelta
import time
from fastapi import HTTPException
import jwt
from app.core.security import OAuth2PasswordException, authenticate_user, create_access_token, decode_access_token, get_current_enabled_user, get_current_user, get_hashed_password, get_token_from_cookie_or_header, verify_password
import pytest
from unittest.mock import Mock, patch
from app.models import User
from tests.conftest import TEST_EMAIL, TEST_PASSWORD

def make_session_mock(user):
    session_mock = Mock()
    result_mock = Mock()

    result_mock.first.return_value = user 
    session_mock.exec.return_value = result_mock

    return session_mock

def test_verify_password():
    test_hashed_password = get_hashed_password(TEST_PASSWORD)

    assert verify_password(TEST_PASSWORD, test_hashed_password)

def test_verify_password_incorrect():
    test_hashed_password = get_hashed_password(TEST_PASSWORD + "123")

    assert verify_password(TEST_PASSWORD, test_hashed_password) == False

def test_get_hashed_password():
    hashed_password = get_hashed_password(TEST_PASSWORD)
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
    test_user = User(email=TEST_EMAIL, password_hash=get_hashed_password(TEST_PASSWORD))
    session_mock = make_session_mock(test_user)

    result = authenticate_user(session_mock, TEST_EMAIL, TEST_PASSWORD)
    assert result == test_user


def test_authenticate_user_disabled():
    test_user = User(email=TEST_EMAIL,
                     password_hash=get_hashed_password(TEST_PASSWORD),
                     disabled=True)
    session_mock = make_session_mock(test_user)

    result = authenticate_user(session_mock, TEST_EMAIL, TEST_PASSWORD)
    assert result is None

def test_authenticate_user_incorrect_password():
    test_user = User(email=TEST_EMAIL, password_hash=get_hashed_password(TEST_PASSWORD))
    session_mock = make_session_mock(test_user)

    result = authenticate_user(session_mock, TEST_EMAIL, TEST_PASSWORD + "123")
    assert result is None

def test_get_token_from_cookie_or_header():
    assert get_token_from_cookie_or_header("header_token", None) == "header_token"
    assert get_token_from_cookie_or_header(None, "cookie_token") == "cookie_token"

def test_get_token_from_cookie_or_header_none():
    with pytest.raises(HTTPException) as exc_info:
        get_token_from_cookie_or_header(None, None)

    assert exc_info.value.status_code == 401
    assert exc_info.value.headers["WWW-Authenticate"] == "Bearer"

def test_get_current_user():
    test_user = User(email=TEST_EMAIL, password_hash=TEST_PASSWORD, disabled=True)
    session_mock = make_session_mock(test_user)

    with patch("app.core.security.decode_access_token") as mock_decode:
        mock_decode.return_value = {"sub": "123"}

        user = get_current_user(session_mock, "token")
        assert user == test_user
 
def test_get_current_user_invalid_token():
    session = Mock()

    with patch("app.core.security.decode_access_token", side_effect=jwt.InvalidTokenError):
        with pytest.raises(OAuth2PasswordException, check=lambda e: e.error == "invalid_token"):
            _ = get_current_user(session, "bad_token")

def test_get_current_user_invalid_sub():
    session_mock = Mock()

    with patch("app.core.security.decode_access_token") as mock_decode:
        mock_decode.return_value = {"sub": 123}

        with pytest.raises(OAuth2PasswordException, check=lambda e: e.error == "invalid_token"):
            _ = get_current_user(session_mock, "token")

def test_get_current_user_not_found():
    session_mock = make_session_mock(None)

    with patch("app.core.security.decode_access_token") as mock_decode:
        mock_decode.return_value = {"sub": "123"}

        with pytest.raises(OAuth2PasswordException, check=lambda e: e.error == "invalid_token"):
            _ = get_current_user(session_mock, "token")

def test_get_current_enabled_user():
     test_user = User(email=TEST_EMAIL, password_hash=TEST_PASSWORD + "a1bs")

     user = get_current_enabled_user(test_user)
     assert user == test_user

def test_get_current_enabled_user_disabled():
     user = User(email=TEST_EMAIL, password_hash=TEST_PASSWORD + "a1bs", disabled=True)

     with pytest.raises(OAuth2PasswordException, check=lambda e: e.error == "invalid_token"):
         _ = get_current_enabled_user(user)
