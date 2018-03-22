#!/usr/bin/python
#This script will run a number of jobs, limited to TLIM threads and ~MLIM memory. As threads finish, it will run new jobs.
#Can take integers as arguments as limits to the number of threads and the memory limit, respectively.
#Change the GENERATE FILELIST HERE and GENERATE CMD HERE sections
import sys
import os
import threading
import resource
from threading import BoundedSemaphore, Lock
#import psutil

#runs the bash command
def run_job(cmd, sem, lock):
  try:
    os.system(cmd)
  finally:
    #release the lock, then the semaphore
    try:
      lock.release()
    finally:
      sem.release()

def main(sysargv=[]):
  TLIM = 50 #the maximum number of concurrent threads
  MLIM = 20.0 #the memory limit (in GB)
  if len(sysargv) > 0:
    TLIM = int(sysargv[0])
  if len(sysargv) > 1:
    MLIM = float(sysargv[1])
  
  #imprecise safety precautions
  TLIM = TLIM - 1
  MLIM = int(MLIM * (2**20) * float(TLIM)/(TLIM+1)) #in kB
  
  t_arr = [] #array of threads
  sem = BoundedSemaphore(value=TLIM) #semaphore to control the number of threads
  lock = Lock()
  
  #################################################
  ##GENERATE FILELIST HERE
  filelist = []
  #################################################
  
  #run the job for each file
  for i,f in enumerate(filelist): #i is the counter, f is the filename
    
    #################################################
    ##GENERATE CMD HERE
    cmd = "echo \"stuff\""
    #################################################
    
    t_arr.append(threading.Thread(target=run_job, args=(cmd,sem,lock,)))
    t_arr[i].daemon = True
    
    #wait until enough threads have finished to start another
    sem.acquire()
    
    #wait until there's enough memory
    #process = psutil.Process(os.getpid())
    #memuse = (process.memory_info()).rss
    memdata = resource.getrusage(resource.RUSAGE_BOTH)
    memuse = memdata.ru_ixrss + memdata.ru_idrss
    if memuse >= MLIM:
      lock.acquire(blocking=True)

    t_arr[i].start()
    
  #wait until the last thread is finished to exit
  t_arr[-1].join()


if __name__ == "__main__":
  t_main = threading.Thread(target=main, args=(sys.argv[1:],))
  t_main.daemon = True
  t_main.start()