"""
graceful_exit.py
20260804

Provide a graceful exit mechanism for all download scripts:
    - the first Ctrl+C stops starting new downloads, and waits for the
      in-flight downloads to finish, printing how many downloads are still
      running every few seconds;
    - the second Ctrl+C exits immediately.

The SIGINT handler is installed automatically when this module is imported,
and the in-flight downloads are joined automatically at exit (via atexit),
so every script that imports lib.downloader or lib.my_request supports this
mechanism without any further changes.
"""

import os
import time
import signal
import threading
import atexit

_stop_requested = False
_lock = threading.Lock()
_inflight_threads = []
_status_print_interval_in_seconds = 10


def is_stop_requested():
    """whether the first Ctrl+C has been pressed"""
    with _lock:
        return _stop_requested


def register_thread(thread):
    """register a download thread as in-flight, so that it will be waited
    for at exit"""
    _inflight_threads.append(thread)


def has_inflight_downloads():
    """whether there is any in-flight download thread"""
    return any(t.is_alive() for t in _inflight_threads)


def _start_status_printer():
    """print how many downloads are still running every
    _status_print_interval_in_seconds seconds until all of them finish"""
    def _print_status():
        while has_inflight_downloads():
            time.sleep(_status_print_interval_in_seconds)
            alive = [t for t in _inflight_threads if t.is_alive()]
            if alive:
                print(f'\nwaiting for the remaining {len(alive)} paper(s) '
                      f'to finish downloading...', flush=True)
    threading.Thread(target=_print_status, daemon=True).start()


def wait_for_inflight_downloads():
    """wait until all in-flight download threads have finished"""
    alive = [t for t in _inflight_threads if t.is_alive()]
    if not alive:
        return
    print(f'\nwaiting for {len(alive)} in-flight download(s) to finish...',
          flush=True)
    for t in alive:
        t.join()
    print('all in-flight downloads finished.', flush=True)


def _print_prompt(message):
    """print a message wrapped by a prominent separator, so that it is
    easily noticed in the middle of progress bars"""
    print('\n' + '=' * 60, flush=True)
    print(message, flush=True)
    print('=' * 60, flush=True)


def _sigint_handler(signum, frame):
    global _stop_requested
    with _lock:
        if _stop_requested:
            # the second Ctrl+C: force exit immediately
            _print_prompt('force exit!')
            os._exit(1)
        if not has_inflight_downloads():
            # no download is running, just stop the whole script
            _print_prompt('Ctrl+C pressed, no in-flight download, exiting...')
            raise SystemExit(0)
        _stop_requested = True
    _print_prompt(
        'Ctrl+C pressed: stop starting new downloads and wait for\n'
        'in-flight downloads to finish.\n'
        'Press Ctrl+C again to force exit immediately.')
    _start_status_printer()


def _install():
    try:
        signal.signal(signal.SIGINT, _sigint_handler)
    except ValueError:
        # not in the main thread, skip installing
        pass


_install()
atexit.register(wait_for_inflight_downloads)
