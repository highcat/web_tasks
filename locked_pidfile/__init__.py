#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import fcntl
import time

# Запуск демона с pid-файлом на основе блокировки pid-файла.
# + таймаут на исполнение процесса
# заявлена 100% гарантия что демон не запустится дважды, и что левый процесс не убъётся.

# TODO: заменить printf логгингом



def __lock_pidfile(filename):
    fd=os.open(filename, os.O_CREAT|os.O_RDWR)

    try: 
        # Lock for read, to read PID
        pid = 0        
        fcntl.flock(fd, fcntl.LOCK_SH)
        try:
            pid = int(os.read(fd, 100))
        except ValueError:
            os.ftruncate(fd, 0)
        
        # Lock for write or exit
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

    

def lock_pidfile(filename, time_limit=None):
    ok, pid = __lock_pidfile(filename)
    if not ok:
        print "can't acquire lock - task is already running, or no access to pidfile (pid='%d')"%pid
        if not time_limit:
            return False
        else:
            time_file=os.path.getmtime(filename)
            # kill process if lived too long
            try:
                os.kill(pid, 0)
                print "running %f seconds"%(time.time()-time_file)
                if (time.time()-time_file) <= time_limit * 60:
                    return False
                else:
                    print "time limit exceeded!"
                    try:
                        print "killing with SIGTERM..."
                        os.kill(pid, 15)
                        print "waiting for process to handle SIGTERM"
                        for i in range(10):
                            os.kill(pid, 0)                            
                            time.sleep(1)
                        print "killing with SIGKILL..."
                        os.kill(pid, 9)
                        for i in range(10):
                            os.kill(pid, 0)                            
                            time.sleep(1)
                        # NOTE - не 100% гарантия, что запустится после kill
                    except OSError: # can't find PID - so it's killed
                        pass
                    print "process has been killed, starting new process"
                    ok, pid = __lock_pidfile(filename)
                    if not ok:
                        return False
            except OSError: # can't find PID - so it does not exist
                pass
    return True



if __name__=='__main__':
    if lock_pidfile('myfile.pid', 10):
        print "acquired"
        time.sleep(20)
        print "done"

