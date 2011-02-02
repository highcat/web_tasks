
import fcntl
import time
import os

if __name__=='__main__':
    filename = 'myfile.pid'
    try:
        fd=os.open(filename, os.O_CREAT|os.O_RDWR)
        fcntl.flock(fd, fcntl.LOCK_SH|fcntl.LOCK_NB)
        print "sh success"
        time.sleep(20000)
    except IOError:
        print "sh error"
    
