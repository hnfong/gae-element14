#!/usr/bin/python
"""
Usage: qwe [-] [title]

Post notes to notes.py

If title is omitted, or '-' is passed as first argument, then read stdin for content.
"""

import urllib
import sys

title = 'from qwe'
content = ''
if len(sys.argv) == 1 or sys.argv[1] == '-':
	content = sys.stdin.read(1024*1024)
	if len(content) > 900*1024:
		sys.stderr.write("Warning: contents might be too large\n")

try:
	if sys.argv[1] == '-': sys.argv.pop(0)
except IndexError:
	pass
sys.argv.pop(0)

if len(sys.argv) > 0: title = " ".join(sys.argv)

sys.stderr.write("* Sending data ...")
urllib.urlopen("http://app.element14.org/note/", urllib.urlencode( { 'title': title, 'content' : content } ))
sys.stderr.write(" done.\n")
