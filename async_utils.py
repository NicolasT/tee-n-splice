'''
Utilities to use `bindings.tee` and `bindings.splice` in an `eventlet` setting
'''

import os
import errno
import fcntl

import eventlet.hubs

import bindings

def retry_while_errno(action, errnos):
    '''Run a given action and retry if applicable

    This function will run the given function `action` (without any arguments),
    and catch any `OSError`s. If the `errno` provided with the exception is
    part of the given `errnos` collection, the call will be retried, and so on.

    The result of the successful call to `action` is returned. Any exceptions
    which don't match the given `errnos` are propagated.

    This is useful to handle `errno.EINTR`.
    '''

    while True:
        try:
            return action()
        except OSError as exc:
            if exc.errno in errnos:
                continue
            else:
                raise

def run_and_retry_while_ewouldblock(wait, action):
    '''
    Run a given action, and retry after calling `wait` upon `errno.EWOULDBLOCK`

    This function will call the given action `action` (without any arguments)
    and return its result.

    If execution of `action` raises an `OSError` with `errno` set to
    `errno.EWOULDBLOCK`, then `wait` will be called (without any arguments), and
    `action` will be retried, as long as necessary.

    Any other errors will be propagated.

    The function returns the result of a successful call to `action`.
    '''

    try:
        return action()
    except OSError as exc:
        if exc.errno != errno.EWOULDBLOCK:
            raise

    def wait_and_do(): #pylint: disable=C0111
        wait()
        return action()

    return retry_while_errno(wait_and_do, [errno.EWOULDBLOCK])

def tee(fd_in, fd_out, len_, flags):
    '''`eventlet`-enabled version of `bindings.tee`'''

    def action(): #pylint: disable=C0111
        return retry_while_errno(
            lambda: bindings.tee(fd_in, fd_out, len_, flags),
            [errno.EINTR])

    def wait(): #pylint: disable=C0111
        eventlet.hubs.trampoline(fd_in, read=True)
        eventlet.hubs.trampoline(fd_out, write=True)

    return run_and_retry_while_ewouldblock(wait, action)

#pylint: disable=R0913
def splice(fd_in, off_in, fd_out, off_out, len_, flags):
    '''`eventlet`-enabled version of `bindings.splice`'''

    def action(): #pylint: disable=C0111
        return retry_while_errno(
            lambda: bindings.splice(
                fd_in, off_in, fd_out, off_out, len_, flags),
            [errno.EINTR])

    def wait(): #pylint: disable=C0111
        eventlet.hubs.trampoline(fd_in, read=True)
        eventlet.hubs.trampoline(fd_out, write=True)

    return run_and_retry_while_ewouldblock(wait, action)

def make_non_blocking(fd): #pylint: disable=C0103
    '''Set the `os.O_NONBLOCK` flag on a file descriptor'''

    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
