"""Result and Option types for error handling"""
from typing import Generic, TypeVar, Callable, Union


T = TypeVar('T')
E = TypeVar('E')


class Result(Generic[T, E]):
    """Result type for operations that can succeed or fail"""
    
    def __init__(self, value: Union[T, E], is_ok: bool):
        self._value = value
        self._is_ok = is_ok
    
    @staticmethod
    def ok(value: T) -> 'Result[T, E]':
        """Create a successful result"""
        return Result(value, True)
    
    @staticmethod
    def err(error: E) -> 'Result[T, E]':
        """Create an error result"""
        return Result(error, False)
    
    def is_ok(self) -> bool:
        """Check if result is successful"""
        return self._is_ok
    
    def is_err(self) -> bool:
        """Check if result is an error"""
        return not self._is_ok
    
    def unwrap(self) -> T:
        """Get the value, raising exception if error"""
        if not self._is_ok:
            raise ValueError(f"Called unwrap on error: {self._value}")
        return self._value
    
    def unwrap_err(self) -> E:
        """Get the error, raising exception if ok"""
        if self._is_ok:
            raise ValueError(f"Called unwrap_err on ok: {self._value}")
        return self._value
    
    def unwrap_or(self, default: T) -> T:
        """Get the value or return default if error"""
        return self._value if self._is_ok else default

    def map(self, func: Callable[[T], 'U']) -> 'Result[U, E]':
        """Map the value if ok"""
        if self._is_ok:
            return Result.ok(func(self._value))
        return Result.err(self._value)
    
    def map_err(self, func: Callable[[E], 'F']) -> 'Result[T, F]':
        """Map the error if err"""
        if not self._is_ok:
            return Result.err(func(self._value))
        return Result.ok(self._value)


class Option(Generic[T]):
    """Option type for values that may or may not exist"""
    
    def __init__(self, value: T = None, has_value: bool = False):
        self._value = value
        self._has_value = has_value
    
    @staticmethod
    def some(value: T) -> 'Option[T]':
        """Create an option with a value"""
        return Option(value, True)
    
    @staticmethod
    def none() -> 'Option[T]':
        """Create an empty option"""
        return Option(None, False)
    
    def is_some(self) -> bool:
        """Check if option has a value"""
        return self._has_value
    
    def is_none(self) -> bool:
        """Check if option is empty"""
        return not self._has_value
    
    def unwrap(self) -> T:
        """Get the value, raising exception if none"""
        if not self._has_value:
            raise ValueError("Called unwrap on None")
        return self._value
    
    def unwrap_or(self, default: T) -> T:
        """Get the value or return default if none"""
        return self._value if self._has_value else default
    
    def map(self, func: Callable[[T], 'U']) -> 'Option[U]':
        """Map the value if some"""
        if self._has_value:
            return Option.some(func(self._value))
        return Option.none()
