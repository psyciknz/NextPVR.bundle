#
# Copyright (c) 2010 Plex Development Team. All rights reserved.
# Modified by Guillaume Boudreau to ignore folders containing .plexignore marker files
# Modified by David Cole to allow import of NextPVR based recordings drive:\Folder\<showname>\<showname>_yyyymmdd_hhmmhhmm.ts
#
import sys
#sys.path.append("G:\Plex/Plex Media Server/Scanners/Series")
#sys.path.append("G:\Plex Media Server\Plug-ins\Scanners.bundle\Contents\Resources\Common\")
import re, os, os.path
import Media, VideoFiles, Stack, Utils
from mp4file import mp4file, atomsearch

#Filthy Rich_20160215_21302230.ts

episode_regexps = [
    '(?P<show>.*?)[-_](?P<year>[0-9]{4})(?P<month>[0-9]{2})(?P<day>[0-9]{2})[-_](?P<stime>[0-9]{4})(?P<etime>[0-9]{4})[-_.]ts',
	'(?P<show>.*?)*.ts'
  ]

def Ignore(subdirs):
	#print "Checking for Ignores in the following subdirs:" + pprint.pformat(subdirs)
	subdirs_to_whack = []
	for subdir in subdirs:
		if os.path.exists(subdir + '/.plexignore'):
			print "Found .plexignore file in " + subdir + ". Ignoring."
			subdirs_to_whack.append(subdir)

	# Whack subdirs.
	subdirs_to_whack = list(set(subdirs_to_whack))
	for subdir in subdirs_to_whack:
		subdirs.remove(subdir)


# Look for episodes.
def Scan(path, files, mediaList, subdirs):
	print "********************************************"
	print "Starting scan of "+ path
	
	# Scan for video files.
	VideoFiles.Scan(path, files, mediaList, subdirs)
	print "After videofiles scan " + path
	# Run the select regexps we allow at the top level.
	for i in files:
		file = os.path.basename(i)
		print "File found: " + file
		for rx in episode_regexps[0:1]:
			match = re.search(rx, file, re.IGNORECASE)
			if match:

				# Extract data.
				print "Match found on file: " + file
				show = match.group('show')
				year = int(match.group('year'))
				month = int(match.group('month'))
				day = int(match.group('day'))
				ep = '%0*d' % (2,month)+'%0*d' % (2,day)
				title = '%0*d' % (4,year) + "-" + ep
				print "Extracted Details:"
				print "Show: " + show
				print "Year: " + '%0*d' % (4,year)
				print "Month: " + '%0*d' % (2,month)
				print "Day:" + '%0*d' % (2,day)
				print "ep: " + ep
				print "Title: " + title
				if len(show) > 0:
					tv_show = Media.Episode(show, year, ep, ep, None)
					tv_show.released_at = '%d-%02d-%02d' % (year, month, day)
					tv_show.parts.append(i)
					mediaList.append(tv_show)
			else:
				print 'No match found on %s' % file

	# Stack the results.
	Stack.Scan(path, files, mediaList, subdirs)
  
def find_data(atom, name):
  child = atomsearch.find_path(atom, name)
  data_atom = child.find('data')
  if data_atom and 'data' in data_atom.attrs:
    return data_atom.attrs['data']

import sys
    
if __name__ == '__main__':
  print "Hello, world!"
  path = sys.argv[1]
  files = [os.path.join(path, file) for file in os.listdir(path)]
  media = []
  Scan(path[1:], files, media, [])
  print "Media:", media