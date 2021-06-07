"""
This type stub file was generated by pyright.
"""

import asyncio
import asyncio.tasks
import functools
import multiprocessing
import os
import warnings
from asyncio import coroutine
from concurrent.futures import ThreadPoolExecutor

"""asyncio compatibility layer for Motor, an asynchronous MongoDB driver.

See "Frameworks" in the Developer Guide.
"""
CLASS_PREFIX = ...
def get_event_loop(): # -> AbstractEventLoop:
    ...

def is_event_loop(loop): # -> bool:
    ...

def check_event_loop(loop): # -> None:
    ...

def get_future(loop):
    ...

if 'MOTOR_MAX_WORKERS' in os.environ:
    max_workers = ...
else:
    max_workers = ...
_EXECUTOR = ...
def run_on_executor(loop, fn, *args, **kwargs):
    ...

def chain_future(a, b): # -> None:
    ...

def chain_return_value(future, loop, return_value):
    """Compatible way to return a value in all Pythons.

    PEP 479, raise StopIteration(value) from a coroutine won't work forever,
    but "return value" doesn't work in Python 2. Instead, Motor methods that
    return values resolve a Future with it, and are implemented with callbacks
    rather than a coroutine internally.
    """
    ...

def is_future(f): # -> bool:
    ...

def call_soon(loop, callback, *args, **kwargs): # -> None:
    ...

def add_future(loop, future, callback, *args): # -> None:
    ...

def pymongo_class_wrapper(f, pymongo_class): # -> (self: Unknown, *args: Unknown, **kwargs: Unknown) -> Coroutine[Any, Any, Unknown]:
    """Executes the coroutine f and wraps its result in a Motor class.

    See WrapAsync.
    """
    ...

def yieldable(future):
    ...

def platform_info(): # -> Literal['asyncio']:
    ...

