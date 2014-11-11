'''Pipes-related utilities'''

import fcntl

F_SETPIPE_SZ = 1031 # From `bits/fcntl-linux.h`
F_GETPIPE_SZ = 1032 # From `bits/fcntl-linux.h`

PIPE_MAX_SIZE_PATH = '/proc/sys/fs/pipe-max-size'

def read_pipe_max_size(path=PIPE_MAX_SIZE_PATH):
    '''Retrieve the system-wide maximum pipe size (for unprivileged users)'''

    with open(path, 'r') as fd: #pylint: disable=C0103
        data = fd.read()
        return int(data.strip())

def get_pipe_size(fd): #pylint: disable=C0103
    '''Retrieve the capacity of the pipe referred to by `fd`

    See the section on `F_GETPIPE_SZ` in `man 2 fcntl` for more information.
    '''

    return fcntl.fcntl(fd, F_GETPIPE_SZ)

def set_pipe_size(fd, size): #pylint: disable=C0103
    '''Set the capacity of the pipe referred to by `fd`

    This returns the size chosen by the kernel (e.g. a multiple of the page
    size).

    Raises an `IOError` with the appropriate `errno` (`EPERM`) if the given
    value is larger than the maximum permitted value (see
    `read_pipe_max_size`).

    See the section on `F_SETPIPE_SZ` in `man 2 fcntl` for more information.
    '''

    return fcntl.fcntl(fd, F_SETPIPE_SZ, size)
