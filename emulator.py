#!/usr/bin/python

import sys
import time

## FORMAT FOR CHANGE:
### old eip, changed memloc [or None], old value [or None], new value [or None], new eip


filename = sys.argv[1]

mem = []

changes = []

future_changes = []

save_points = [0]
save_points_future = []
eip = -1

break_on_write = True
break_on_read = True
break_after_instructions = 1

broken = False

verbose = True

def initialize():
  global filename, mem, eip
  f = open(filename, "r")
  l = f.readline()
  if l.startswith("eip:"):
    eip = int(l[len("eip:"):])
  else:
    eip = 0
    mem.extend([int(x) for x in l.split(" ")])

  for line in f:
    ie = [int(x) for x in line.split(" ")]
    mem.extend(ie)
  f.close()

def dump():
  global eip, mem
  fn = sys.argv[1] + "-" + str(int(time.time())) + ".dump"
  f2 = open(fn, "w")
  print "Dumping to " + fn
  f2.write("eip:" + str(eip) + "\n")
  for b in range(0, len(mem), 3):
    f2.write("{0} {1} {2}\n".format(mem[b], mem[b+1], mem[b+2]))
  f2.close()

def dochange():
  global eip, mem
  change = future_changes.pop()
  _oldeip, loc, _oldval, newval, neweip = change
  eip = neweip
  if loc is not None:
    mem[loc] = newval
  changes.append(change)

def undochange():
  global eip, mem
  change = changes.pop()
  oldeip, loc, oldval, _newval, _neweip = change
  eip = oldeip
  if loc is not None:
    mem[loc] = oldval
  future_changes.append(change)

def do_read():
  global break_on_read, broken
  if break_on_read:
    broken = True
  sys.stdout.write("READ: ")
  t = sys.stdin.readline()
  return t[0]

def do_write(c):
  global break_on_write, broken
  if break_on_write:
    broken = True
  print "WRITE - " + chr(c) + "  (" + str(c) + ")"

def step():
  global eip, mem
  a, b, c = mem[eip:eip+3]
  change = [eip]
  if (a < 0):
    t = do_read()
    change.extend([b, mem[b], mem[b] + ord(t), eip + 3])
  elif (b < 0):
    do_write(mem[a] % 256)
    change.extend([None, None, None, eip+3])
  else:
    new = mem[b] - mem[a]
    if (new <= 0):
      neweip = c
    else:
      neweip = eip + 3
    change.extend([b, mem[b], mem[b] - mem[a], neweip])
  return change

def main():
  global break_on_read, break_on_write, break_after_instructions, future_changes, eip, broken, verbose
  initialize()

  while eip >= 0:
    if verbose:
      print "Executing instruction at " + str(eip)
    change = step()
    if verbose and change[1] is not None:
      print "Changed value at " + str(change[1]) + " from " + str(change[2]) + " to " + str(change[3])
    if break_after_instructions != None:
      break_after_instructions = break_after_instructions - 1
      if break_after_instructions == 0:
        break_after_instructions = None
        broken = True
    if not broken:
      future_changes = [change]
      future_save_points = []
      dochange()
    else:
      while 1:
        sys.stdout.write(">>> ")
        cmd = sys.stdin.readline()
        if len(cmd) == 0:
          cmd = "e"
        else:
          cmd = cmd.strip()
        if cmd.startswith("h"):
          print "h:           help"
          print "c:           continue"
          print "d:           take a dump"
          print "e:           exit"
          print "i:           print values of all registers.  All two of them.  Hehe."
          print "n[$]:        proceed for $ steps, or until other break"
          print "r[$]:        redo $ steps, unconditionally"
          print "u[$]:        undo $ steps"
          print "b[r/w][t/f]: enable/disable breaking on reads/writes"
          print "s/l:         setjmp/longjmp (create savepoint, restore to last savepoint)"  
          print "v[t/f]       set/disable verbose"
        elif cmd.startswith("d"):
          dump()
        elif cmd.startswith("e"):
          sys.exit()
        elif cmd.startswith("c"):
          broken = False
          future_changes = [change]
          future_save_points = []
          dochange()
          print "Continuing..."
          break
        elif cmd.startswith("u"):
          try:
            n = int(cmd[len("u"):])
          except:
            n = 1
          for i in range(n):
            undochange()
            while len(save_points) > 0 and save_points[-1] > len(changes):
              future_save_points.append(save_points.pop())
          print "Undid " + str(n) + " instructions."
        elif cmd.startswith("r"):
          try:
            n = int(cmd[len("r"):])
          except:
            n = 1
          for i in range(n):
            dochange()
            while len(future_save_points) > 0 and future_save_points[-1] < len(changes):
              save_points.append(future_save_points.pop())
          print "Redid " + str(n) + " instructions."
        elif cmd.startswith("n"):
          try:
            n = int(cmd[len("n"):])
          except:
            n = 1
          break_after_instructions = n
          broken = False
          future_changes = [change]
          future_save_points = []
          dochange()
          print "Executing " + str(n) + " instructions..."
          break
        elif cmd.startswith("i"):
          print "eip: " + str(eip)
          print "eiz: 0     (as always)"
        elif cmd.startswith("b"):
          if (cmd[2] == "t"):
            flagg = True
          else:
            flagg = False
          if (cmd[1] == "r"):
            break_on_read = flagg
            print "Break on read set to " + str(flagg)
          else:
            break_on_write = flagg
            print "Break on write set to " + str(flagg)
        elif cmd.startswith("v"):
          verbose = (cmd[1] == "t")
          print "Verbose set to " + str(verbose)
        elif cmd.startswith("s"):
          index = len(changes)
          print "Savepoint added at change " + str(index) + "."
          save_points.append(index)
        elif cmd.startswith("l"):
          try:
            index = save_points.pop()
            print "Restoring to most recent savepoint, at " + str(index) + "."
            while (len(changes) > index):
              undochange()
          except:
            print "No savepoint to restore."
        elif cmd.startswith("L"):
          try:
            index = save_points_future.pop()
            print "Restoring to most recent future savepoint, at " + str(index) + "."
            while (len(changes) < index):
              dochange()
          except:
            print "No future savepoint to restore."

if __name__ == "__main__":
  main()
