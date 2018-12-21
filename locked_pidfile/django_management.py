# -*- coding: utf-8 -*-
import os
import re
import sys
from functools import wraps
from django.conf import settings
from locked_pidfile import lock_pidfile

import logging
script_log = logging.getLogger('management_script')


def single(script_name):
    """
    A decorator for `handle()` and `handle_noargs()` methods in scripts.
    Usage:

        @script.single(__name__)
        def handle_noargs(self, **options):
            ...

    1. Ensure only 1 instance of the script is running.
    2. Log errors.
    """
    def wrapper(fn):
        @wraps(fn)
        def do(*args, **kwargs):
            s_name = re.match('^.*\.([^.]+)$', script_name).group(1)
            if hasattr(settings, 'DJANGO_ROOT'):
                path = os.path.join(settings.DJANGO_ROOT, '../var/run/{}.lock'.format(s_name))
            else:
                path = os.path.join(settings.BASE_DIR, 'var/run/{}.lock'.format(s_name))
            
            if lock_pidfile(path, time_limit=10):
                try:
                    fn(*args, **kwargs)
                except Exception:
                    script_log.exception('%s failed' % script_name)
                    if sys.stdout.isatty():
                        raise
            else:
                print("%s is already running" % script_name)
        return do
    return wrapper
