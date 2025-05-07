"""
Copyright <2023> <Andreas Niskanen, University of Helsinki>

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be included in all copies
or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT
OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
"""

import sys
import itertools

file = sys.argv[1]
assert(file.endswith(".tgf"))

lines = [line.strip() for line in open(file).read().split("\n")]
lines = [line for line in lines if len(line) > 0]

sep = lines.index("#")

args = lines[:sep]
atts = [line.split() for line in lines[sep+1:]]

arg_counter = itertools.count(1)
arg_to_int = { arg : next(arg_counter) for arg in args }

output = open(file.replace(".tgf", ".af"), "w")
output.write("p af " + str(len(args)) + "\n")
for arg in args:
	output.write("# " + arg + "\n")
for att in atts:
	output.write(str(arg_to_int[att[0]]) + " " + str(arg_to_int[att[1]]) + "\n")
output.close()