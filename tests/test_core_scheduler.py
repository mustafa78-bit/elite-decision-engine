import time
from core.scheduler import Scheduler, GracefulShutdown


class TestScheduler:

    def test_start_stop(self):
        scheduler = Scheduler(interval=0.05)
        assert scheduler.is_running is False
        scheduler.start()
        assert scheduler.is_running is True
        scheduler.stop()
        assert scheduler.is_running is False

    def test_add_task(self):
        scheduler = Scheduler(interval=0.05)
        results = []

        def task():
            results.append(1)

        scheduler.add_task(task)
        scheduler.start()
        time.sleep(0.12)
        scheduler.stop()
        assert len(results) >= 1

    def test_double_start(self):
        scheduler = Scheduler(interval=0.1)
        scheduler.start()
        scheduler.start()
        assert scheduler.is_running is True
        scheduler.stop()


class TestGracefulShutdown:

    def test_add_and_run_handlers(self):
        gs = GracefulShutdown()
        results = []

        def handler1():
            results.append(1)

        def handler2():
            results.append(2)

        gs.add_handler(handler1)
        gs.add_handler(handler2)
        gs.shutdown()
        assert results == [1, 2]

    def test_no_double_shutdown(self):
        gs = GracefulShutdown()
        results = []

        def handler():
            results.append(1)

        gs.add_handler(handler)
        gs.shutdown()
        gs.shutdown()
        assert len(results) == 1
