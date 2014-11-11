'''
Bindings to the `tee` and `splice` system calls
'''

import os
import ctypes
import ctypes.util

#pylint: disable=C0103,R0903,R0913

__all__ = ['tee', 'splice']

_c_loff_t = ctypes.c_uint64

_libc = ctypes.CDLL(ctypes.util.find_library('c'), use_errno=True)

class Tee(object):
    '''Binding to `tee`'''

    __slots__ = '_c_tee',

    def __init__(self):
        c_tee = _libc.tee

        c_tee.argtypes = [
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_size_t,
            ctypes.c_uint
        ]

        c_tee.restype = ctypes.c_ssize_t

        def errcheck(result, func, arguments): #pylint: disable=W0613,C0111
            if result == -1:
                errno_ = ctypes.get_errno()

                raise OSError(errno_, os.strerror(errno_))
            else:
                return result

        c_tee.errcheck = errcheck

        self._c_tee = c_tee

    def __call__(self, fd_in, fd_out, len_, flags):
        '''See `man 2 tee`

        File-descriptors can be file-like objects with a `fileno` method, or
        integers.

        Flags can be an integer value, or a list of flags (exposed on
        `splice`).
        '''

        if not isinstance(flags, (int, long)):
            c_flags = ctypes.c_uint(reduce(lambda a, b: a | b, flags, 0))
        else:
            c_flags = ctypes.c_uint(flags)

        c_fd_in = ctypes.c_int(getattr(fd_in, 'fileno', lambda: fd_in)())
        c_fd_out = ctypes.c_int(getattr(fd_out, 'fileno', lambda: fd_out)())

        return self._c_tee(c_fd_in, c_fd_out, ctypes.c_size_t(len_), c_flags)

tee = Tee()
del Tee


class Splice(object):
    '''Binding to `splice`'''

    # From `bits/fcntl-linux.h`
    SPLICE_F_MOVE = 1
    SPLICE_F_NONBLOCK = 2
    SPLICE_F_MORE = 4
    SPLICE_F_GIFT = 8

    __slots__ = '_c_splice',

    def __init__(self):
        c_splice = _libc.splice

        c_loff_t_p = ctypes.POINTER(_c_loff_t)

        c_splice.argtypes = [
            ctypes.c_int, c_loff_t_p,
            ctypes.c_int, c_loff_t_p,
            ctypes.c_size_t,
            ctypes.c_uint
        ]

        c_splice.restype = ctypes.c_ssize_t

        def errcheck(result, func, arguments): #pylint: disable=W0613,C0111
            if result == -1:
                errno_ = ctypes.get_errno()

                raise OSError(errno_, os.strerror(errno_))
            else:
                off_in = arguments[1]
                off_out = arguments[3]

                return (
                    result,
                    off_in.contents if off_in is not None else None,
                    off_out.contents if off_out is not None else None)

        c_splice.errcheck = errcheck

        self._c_splice = c_splice

    def __call__(self, fd_in, off_in, fd_out, off_out, len_, flags):
        '''See `man 2 splice`

        File-descriptors can be file-like objects with a `fileno` method, or
        integers.

        Flags can be an integer value, or a list of flags (exposed on this
        object).

        Returns a tuple of the result of the `splice` call, the output value of
        `off_in` and the output value of `off_out` (or `None`, if applicable).
        '''

        # TODO: Passing non-`None` values for the offsets (and the corresponding
        #       effect on the result of this function call) is untested.

        if not isinstance(flags, (int, long)):
            c_flags = ctypes.c_uint(reduce(lambda a, b: a | b, flags, 0))
        else:
            c_flags = ctypes.c_uint(flags)

        c_fd_in = ctypes.c_int(getattr(fd_in, 'fileno', lambda: fd_in)())
        c_fd_out = ctypes.c_int(getattr(fd_out, 'fileno', lambda: fd_out)())

        c_off_in = \
            ctypes.byref(_c_loff_t(off_in)) if off_in is not None else None
        c_off_out = \
            ctypes.byref(_c_loff_t(off_out)) if off_out is not None else None

        return self._c_splice(
            c_fd_in, c_off_in, c_fd_out, c_off_out, ctypes.c_size_t(len_),
            c_flags)

splice = Splice()
del Splice
