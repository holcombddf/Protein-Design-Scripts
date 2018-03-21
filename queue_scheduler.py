 #!/usr/bin/python
#This script will run a number of jobs, limited to LIM threads. As threads finish, it will run new jobs.
#Can take an integer as a limit to the number of threads
#Change the GENERATE FILELIST HERE and GENERATE CMD HERE sections
import sys
import os
import threading
from Queue import Queue

#grabs a command from the queue, and runs it
def worker(q):
  while not q.empty():
    cmd = q.get()
    try:
      os.system(cmd)
    finally:
      q.task_done()

def main(sysargv=[]):
  #the maximum number of concurrent threads
  LIM = 50
  if len(sysargv) > 0:
    LIM = int(sysargv[0])
  
  t_arr = [] #array of threads
  q = Queue() #queue of commands
  
  ##GENERATE FILELIST HERE
  filelist = []
  
  #put each command on the queue
  for i,f in enumerate(filelist): #i is the counter, f is the filename
    
    ##GENERATE CMD HERE
    cmd = "echo \"stuff\""

    q.put(cmd)
  
  #create LIM workers to process the queue
  for i in range(LIM):
    t_arr.append(threading.Thread(target=worker, args=(q,)))
    t_arr[i].daemon = True
    t_arr[i].start()
    
  q.join()

if __name__ == "__main__":
  t_main = threading.Thread(target=main, args=(sys.argv[1:],))
  t_main.daemon = True
  t_main.start()