import functools
from queue import Queue
from typing import Union, Callable
from threading import Thread


class AsyncUpdate:
    def __init__(self, message: str, progress: int = 1, progress_max: int = 1, minor: bool = False):
        self.progress = progress
        self.progress_max = progress_max
        self.message = message.rstrip("\n")
        self.minor = minor

    def get_completion(self) -> float:
        return round(float(self.progress / self.progress_max) * 100, 2)

    def is_minor(self):
        return self.minor


class ThrowingThread(Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, *, daemon=None):
        super().__init__(group=group, target=target, name=name,
                         args=args, kwargs=kwargs, daemon=daemon)
        self.exception = None

    def run(self):
        self.exception = None
        try:
            super().run()
        except BaseException as e:
            self.exception = e

    def join(self, timeout=None) -> BaseException:
        super().join(timeout)
        return self.exception


def threaded_func():
    def outer_wrapper(f):
        @functools.wraps(f)
        def wrapper(self: Threadable, *args, **kwargs):
            data_queue = Queue()

            def _thread_exec():
                try:
                    res = f(self, data_queue, *args, *kwargs)
                except BaseException as e:
                    raise e
                return res
            self.thread = ThrowingThread(target=_thread_exec)
            self.thread.start()
            return data_queue
        return wrapper
    return outer_wrapper


class Threadable:

    def __init__(self):
        self.thread: Union[ThrowingThread, None] = None
        super().__init__()

    def is_running(self):
        return self.thread is not None and self.thread.is_alive()

    def wait_for_completion(self):
        if self.thread is not None and self.thread.is_alive():
            e = self.thread.join()
            if e is not None:
                raise e

    def get_error(self) -> str:
        if self.thread is not None and self.thread.exception is not None:
            return str(self.thread.exception)
        else:
            return ""
