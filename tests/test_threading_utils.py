import unittest

from backend.bilinovel.threading_utils import shutdown_executor


class OldExecutor:
    def __init__(self):
        self.calls = []

    def shutdown(self, wait=True, **kwargs):
        self.calls.append((wait, kwargs))
        if 'cancel_futures' in kwargs:
            raise TypeError(
                "shutdown() got an unexpected keyword argument "
                "'cancel_futures'"
            )


class NewExecutor:
    def __init__(self):
        self.calls = []

    def shutdown(self, wait=True, cancel_futures=False):
        self.calls.append((wait, cancel_futures))


class ShutdownExecutorTest(unittest.TestCase):
    def test_uses_cancel_futures_when_supported(self):
        executor = NewExecutor()

        shutdown_executor(executor)

        self.assertEqual(executor.calls, [(False, True)])

    def test_falls_back_for_older_python(self):
        executor = OldExecutor()

        shutdown_executor(executor)

        self.assertEqual(
            executor.calls,
            [
                (False, {'cancel_futures': True}),
                (False, {}),
            ],
        )


if __name__ == '__main__':
    unittest.main()
