#!/usr/bin/python

import sys

filename = sys.argv[1]

f = open(filename, "r")

a = 0

for line in f:
  if (line.strip() == ""):
    break
  elif line.startswith("eip:"):
    print line
    continue
  i1, i2, i3 = (int(x) for x in line.split(" "))
  parsed = "{3:05}    {0:06} {1:06} {2:06}      ".format(i1, i2, i3, a)
  if (i1 < 0):
    parsed += "REA"
  elif (i2 < 0):
    parsed += "WRT("
    parsed += str(i1 % 256)
    parsed += ")"
  else:
    parsed += "JMP"
  print parsed
  a += 3
