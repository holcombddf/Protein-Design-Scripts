#!/usr/bin/python
#This script will run a number of jobs, limited to TLIM threads and MLIM memory. As threads finish, it will run new jobs.
#Can take integers as arguments as limits to the number of threads and the memory limit, respectively.
#Change the GENERATE FILELIST HERE and GENERATE CMD HERE sections
import sys
import os
import threading
import resource
from threading import Lock
from Queue import Queue
#import psutil

#grabs a command from the queue, and runs it
def worker(q,lock):
  while not q.empty():
    #wait until there's enough memory
    #process = psutil.Process(os.getpid())
    #memuse = (process.memory_info()).rss
    memdata = resource.getrusage(resource.RUSAGE_BOTH)
    memuse = memdata.ru_ixrss + memdata.ru_idrss
    if memuse >= MLIM:
      lock.acquire(blocking=True)
    
    #get a command and run it
    cmd = q.get()
    try:
      os.system(cmd)
    #free up the queue and (try to) release the lock
    finally:
      q.task_done()
      try:
	lock.release()
      except Exception as e:
	pass

def main(sysargv=[]):
  TLIM = 50 #the maximum number of concurrent threads
  MLIM = 20000 #the memory limit
  if len(sysargv) > 0:
    TLIM = int(sysargv[0])
  if len(sysargv) > 1:
    MLIM = int(sysargv[1])
    
  #imprecise safety precautions
  TLIM = TLIM - 1
  MLIM = MLIM * TLIM/(TLIM+1)
  
  t_arr = [] #array of threads
  q = Queue() #queue of commands
  lock = Lock()
  
  ##GENERATE FILELIST HERE
  filelist = []
  
  #put each command on the queue
  for i,f in enumerate(filelist): #i is the counter, f is the filename
    
    ##GENERATE CMD HERE
    cmd = "echo \"stuff\""

    q.put(cmd)
  
  #create TLIM workers to process the queue
  for i in range(TLIM):
    t_arr.append(threading.Thread(target=worker, args=(q,lock,)))
    t_arr[i].daemon = True
    t_arr[i].start()
    
  q.join()

if __name__ == "__main__":
  t_main = threading.Thread(target=main, args=(sys.argv[1:],))
  t_main.daemon = True
  t_main.start()