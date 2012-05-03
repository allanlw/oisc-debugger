#/bin/sh

# This takes our binary file, and outputs the thingies so that they thingy.


hexdump -v -s 0x03ac -e '"%i %i %i\n"' $1