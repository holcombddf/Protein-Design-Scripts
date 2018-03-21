 #!/usr/bin/python
#This script will run a number of jobs, limited to LIM threads. As threads finish, it will run new jobs.
#Can take an integer as a limit to the number of threads
#Change the GENERATE FILELIST HERE and GENERATE CMD HERE sections
import sys
import os
import threading
from threading import BoundedSemaphore

#runs the bash command
def run_job(cmd, sem):
  try:
    os.system(cmd)
  finally:
    sem.release()

def main(sysargv=[]):
  #the maximum number of concurrent threads
  LIM = 50
  if len(sysargv) > 0:
    LIM = int(sysargv[0])
  
  t_arr = [] #array of threads
  sem = BoundedSemaphore(value=LIM) #semaphore to control the number of threads
  
  ##GENERATE FILELIST HERE
  filelist = []
  
  #run the job for each file
  for i,f in enumerate(filelist): #i is the counter, f is the filename
    
    ##GENERATE CMD HERE
    cmd = "echo \"stuff\""
    
    t_arr.append(threading.Thread(target=run_job, args=(cmd,sem,)))
    t_arr[i].daemon = True
    
    #wait until enough threads have finished to start another
    sem.acquire()
    t_arr[i].start()
    
  #wait until the last thread is finished to exit
  t_arr[-1].join()


if __name__ == "__main__":
  t_main = threading.Thread(target=main, args=(sys.argv[1:],))
  t_main.daemon = True
  t_main.start()