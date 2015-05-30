# coding=utf-8
import functools
import time


class RateLimit(object):
    """ Rate limit decorator used to restrict functions from being executed
    based on numbers of requests allowed within a defined window.

    >>> @RateLimit
    >>> def test():
    >>>     print("Called")
    >>> test()
    Called
    >>> test()
    Called
    >>> test()
    >>>

    """

    def __init__(self, wrapped, rate=2, window=120):
        """
        :param wrapped: function to rate limit
        :type wrapped: callable
        :param rate:
        :type rate: int
        :param window: Time in seconds to use as rate limit window
        :type window: int
        """
        self.wrapped = wrapped
        self.rate = rate
        self.window = window
        self.allowance = rate
        self.last_check = time.time()
        functools.update_wrapper(self, wrapped)

    def is_allowed(self):
        """ Determine if the requested action should be allowed to proceed.

        :return: Allow or reject a call
        :rtype: bool
        """
        current = time.time()
        time_passed = current - self.last_check
        self.last_check = current
        self.allowance += time_passed * (self.rate / self.window)
        if self.allowance > self.rate:
            self.allowance = self.rate
        if self.allowance < 1.0:
            return False
        else:
            self.allowance -= 1
            return True

    def __call__(self, *args, **kwargs):
        if self.is_allowed():
            return self.wrapped(*args, **kwargs)
        else:
            args[0].say("Rate limit hit, +1 autisms")

