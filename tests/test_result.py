"""Tests for Result and Option types"""
from src.result import Result, Option


def test_result_ok():
    """Test Result.ok creation and methods"""
    result = Result.ok(42)
    assert result.is_ok()
    assert not result.is_err()
    assert result.unwrap() == 42


def test_result_err():
    """Test Result.err creation and methods"""
    result = Result.err("error message")
    assert result.is_err()
    assert not result.is_ok()
    assert result.unwrap_err() == "error message"


def test_result_unwrap_or():
    """Test Result.unwrap_or with ok and err"""
    ok_result = Result.ok(42)
    err_result = Result.err("error")
    
    assert ok_result.unwrap_or(0) == 42
    assert err_result.unwrap_or(0) == 0


def test_result_map():
    """Test Result.map transformation"""
    result = Result.ok(5)
    mapped = result.map(lambda x: x * 2)
    assert mapped.is_ok()
    assert mapped.unwrap() == 10


def test_option_some():
    """Test Option.some creation and methods"""
    option = Option.some(42)
    assert option.is_some()
    assert not option.is_none()
    assert option.unwrap() == 42


def test_option_none():
    """Test Option.none creation and methods"""
    option = Option.none()
    assert option.is_none()
    assert not option.is_some()


def test_option_unwrap_or():
    """Test Option.unwrap_or with some and none"""
    some_option = Option.some(42)
    none_option = Option.none()
    
    assert some_option.unwrap_or(0) == 42
    assert none_option.unwrap_or(0) == 0


def test_option_map():
    """Test Option.map transformation"""
    option = Option.some(5)
    mapped = option.map(lambda x: x * 2)
    assert mapped.is_some()
    assert mapped.unwrap() == 10
