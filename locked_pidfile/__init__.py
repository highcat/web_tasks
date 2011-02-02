#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import fcntl
import time

# Запуск демона с pid-файлом на основе блокировки pid-файла.
# + таймаут на исполнение процесса
# заявлена 100% гарантия что демон не запустится дважды, и что левый процесс не убъётся.
# 
# 
# Принцип работы lock_pidfile:
# 1. Блокируем на чтение, чтобы сразу прочитать PID.
# 2. Блокируем на запись, пишем PID. Гарантирует что другие процессы не держат блокировку.
# 3. Блокируем на чтение, чтобы другие могли прочитать PID.
# Файловый дескриптор держит блокировку до окончания процесса.
# 


def __lock_pidfile(filename):
    fd=os.open(filename, os.O_CREAT|os.O_RDWR)

    try:
        pid = 0
        # Lock for read, to read PID
        fcntl.flock(fd, fcntl.LOCK_SH)

        pid = 0
        str_pid = os.read(fd, 100)
        try:
            pid = int(str_pid)
        except ValueError:
            # XXX bad pidfile - clean trash
            os.ftruncate(fd, 0)
            sys.stderr.write("Bad Pidfile!\nPidfile contains trash: \"%s\"\nPidfile nas been cleaned!\n" % str_pid)
        
        # reLock for write or exit
        fcntl.flock(fd, fcntl.LOCK_EX|fcntl.LOCK_NB)
        # save PID
        process_id = str(os.getpid())
        os.ftruncate(fd, 0)
        os.lseek(fd, 0, os.SEEK_SET)        
        os.write(fd, process_id)
        os.fsync(fd)
        
        # Re-lock for read to make the PID accessible
        fcntl.flock(fd, fcntl.LOCK_SH)
        return fd, pid
    except IOError:
        os.close(fd)        
        return None, pid


class PidLink(object):
    def __init__(self):
        self.pid = None

def lock_pidfile(filename, time_limit=None, pid_output=PidLink()):
    """
    Lock pidfile for write, if able.

    Returns:
        True on success,
        and setspid into PidLink object, if specified
    """
    ok, pid = __lock_pidfile(filename)

    if ok:
        pid_output.pid = pid
        return True
    if not ok:
        if not time_limit:
            sys.stderr.write("can't acquire lock - task is already running, or no access to pidfile (pid='%d')\n" % pid)
            return False
        else:
            sys.stderr.write("can't acquire lock - task is running on pid (pid='%d'), checking time limit..\n" % pid)
            time_file=os.path.getmtime(filename)
            # kill process if lived too long
            try:
                if pid==0:
                    sys.stderr.write("read lock set on  \n" % pid)
                os.kill(pid, 0)
            except OSError: # can't find PID - so it does not exist
                ok, pid_2nd = __lock_pidfile(filename)
                if ok:
                    pid_output.pid = pid_2nd
                    return True
            else:
                sys.stderr.write("has been running %f seconds\n" % (time.time()-time_file))
                if not (time.time()-time_file) <= time_limit * 60:
                    sys.stderr.write("time limit exceeded!\n")
                    try:
                        sys.stderr.write("killing with SIGTERM...\n")
                        os.kill(pid, 15)
                        sys.stderr.write("waiting for process to handle SIGTERM\n")
                        for i in range(10):
                            os.kill(pid, 0)                            
                            time.sleep(1)
                        sys.stderr.write("killing with SIGKILL...\n")
                        os.kill(pid, 9)
                        for i in range(10):
                            os.kill(pid, 0)
                            time.sleep(1)
                        # NOTE - не 100% гарантия, что запустится после kill (может быть зомби?)
                    except OSError:
                        pass # can't find PID - so it's killed
                    sys.stderr.write("process has been killed, starting new process\n")
                    ok, pid_2nd = __lock_pidfile(filename)
                    if ok:
                        pid_output.pid = pid_2nd
                        return True
                else:
                    sys.stderr.write("time limit is not exceeded pid=%d, stop\n" % pid)
    return False



# FIXME: autotests needed
if __name__=='__main__':
    filename = 'myfile.pid'

    pl = PidLink()
    if lock_pidfile(filename, time_limit=10, pid_output=pl):
        print "acquired", pl.pid
        time.sleep(2000)
        print "done"
    print pl.pid
