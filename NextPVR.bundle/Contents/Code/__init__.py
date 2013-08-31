# NextPVR
# Copyright (C) 2011-2012 Rene Koecher <shirk@bitspin.org>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

#=============================================================================
VIDEO_PREFIX = "/video/nextpvr"

NAME = "NextPVR"
ART  = 'item-default.png'

#=============================================================================

def Start():
    
	ObjectContainer.title1 = NAME
	Log('Started')

# This main function will setup the displayed items.
@handler('/video/nextpvr','NextPVR')
def MainMenu():
	
    dir=ObjectContainer()
    Log('Adding Recordings Menu')
    dir.add(DirectoryObject(key=Callback(RecordingsMenu), title='Recordings'))
    Log('Recordings Menu Added')
    dir.add(DirectoryObject(key=Callback(LiveMenu), title='Live'))
    Log('Live Menu Added')

    return dir
	
@route('/video/nextpvr/live')
def LiveMenu():
	oc = ObjectContainer(title2='Live')
	
	testURL = 'http://pvr.lan:8866/live?channel=2'
	oc.add(
		VideoClipObject(
			url = testURL,
			title = 'Test 1-Live',
			summary = testURL
		)
	)
	testURL = 'http://pvr.lan:8866/live?recording=18121'
	oc.add(
		VideoClipObject(
			url = testURL,
			title = 'Test 2-Recorded',
			summary = testURL
		)
	)
	testURL = 'http://pvr.lan:8866/live?recording=18234'
	oc.add(
		VideoClipObject(
			url = testURL,
			title = 'Test 3-In progress',
			summary = testURL
		)
	)
	return oc

@route('/video/nextpvr/recordings')
def RecordingsMenu():
	Log('Generating Recordings Screen')
	oc = ObjectContainer(title2='Recordings')
	Log('Calling Recording List')
	import xml.etree.ElementTree as ET
	import datetime
	url = "http://pvr.lan:8866/services?method=recording.list&filter=Ready&sid=plex"
	Log('Loading URL %s' % url)
	import urllib2
	request = urllib2.Request(url, headers={"Accept" : "application/xml"})
	Log('Request: %s' % request)
	u = urllib2.urlopen(request)
	Log('Result = %s code= %s' % ( u.code,u.msg))
	tree = ET.parse(u)
	root = tree.getroot()
	Log('Root = %s'  %  root)
	recordings = root.findall('recordings/recording')
	for recording in recordings:
		Log('Recording id %s' % recording.find('id').text)
		testURL = 'http://pvr.lan:8866/live?recording=%s' % recording.find('id').text
		Log('Url %s' % testURL)
		'''
		oc.add(
			VideoClipObject(
				url = testURL,
				title = recording.find('name').text.encode('utf-8'),
				summary = recording.find('desc').text.encode('utf-8')
			)
		)
		'''
		t = datetime.datetime.strptime(recording.find('duration').text,"%H:%M")
		delta = datetime.timedelta(hours=t.hour, minutes=t.minute, seconds=0)
		Log('Name  %s' % recording.find('name').text.encode('utf-8'))
		descr = recording.find('desc').text.encode('utf-8')
		Log('Desc %s' % descr)
		oc.add(
			EpisodeObject(
				url=testURL, 
				title=recording.find('name').text.encode('utf-8'),
				originally_available_at=datetime.datetime.fromtimestamp(float(recording.find('start_time_ticks').text)),
				duration=int(delta.total_seconds()) * 1000,
				summary=descr,
				thumb=R(ART)
			)
		)
		
		Log('Status %s' % recording.find('status').text.encode('utf-8'))
		Log('Start Time %s' % datetime.datetime.fromtimestamp(float(recording.find('start_time_ticks').text)))
		
		'''
		title = recording.find('name').text.encode('utf-8')
		thumb = R(ART)

		oc.add(DirectoryObject(
			key = Callback(Show, show=title, thumb=thumb,root),
			title = title,
			thumb = R(ART)
		))
		'''

	return oc

def PlayVideo(url):
	Log('*************************************************************** Video URL --- ' + url)
	return Redirect(url)