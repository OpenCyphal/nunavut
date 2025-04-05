/// @file
/// Unit tests for cetl::pmr::O1heapResource
///
/// @copyright
/// Copyright (C) OpenCyphal Development Team  <opencyphal.org>
/// Copyright Amazon.com Inc. or its affiliates.
/// SPDX-License-Identifier: MIT
///
/// Dummy system dependencies to allow cross-compiling for bare-metal.
///

#include <stdio.h>
#include <stdint.h>
#include <errno.h>

void _exit(int);
void _exit(int a)
{
    (void) a;
    __asm("BKPT #0");
    while (1)
    {
    }
}

int32_t _getpid(void);
int32_t _getpid(void)
{
    return 0;
}

int _kill(int, int);
int _kill(int a, int b)
{
    (void) a;
    (void) b;
    return -1;
}

size_t _write(const void*, size_t, size_t, FILE*);
size_t _write(const void* a, size_t b, size_t c, FILE* d)
{
    (void) a;
    (void) b;
    (void) c;
    (void) d;
    return 0;
}

int _close(FILE*);
int _close(FILE* a)
{
    (void) a;
    return -1;
}

int _read(int, char*, int);
int _read(int a, char* b, int c)
{
    (void) a;
    (void) b;
    (void) c;
    return -1;
}

off_t _lseek(int, off_t, int);
off_t _lseek(int a, off_t b, int c)
{
    (void) a;
    (void) b;
    (void) c;
    return -1;
}

void* _sbrk(ptrdiff_t);
void* _sbrk(ptrdiff_t a)
{
    (void) a;
    __asm("BKPT #0");
    errno = ENOMEM;
    return (void*) -1;
}

struct stat
{
    int x;
};
int _fstat(int, struct stat* b);
int _fstat(int a, struct stat* b)
{
    (void) a;
    (void) b;
    return -1;
}

int _isatty(int);
int _isatty(int a)
{
    (void) a;
    return -1;
}
