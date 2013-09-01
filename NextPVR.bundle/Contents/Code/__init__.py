# NextPVR
# Copyright (C) 2013 David Cole github@andc.co.nz
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
import xml.etree.ElementTree as ET
import datetime
import urllib2
#=============================================================================
VIDEO_PREFIX = "/video/nextpvr"

NAME = "NextPVR"
ART  = 'item-default.png'
PVR_URL = 'http://%s:%s/' % (Prefs['server'],Prefs['port'])
#=============================================================================

def Start():
    
	ObjectContainer.title1 = NAME
	Log('%s Started' % NAME)
	#PVR_URL = 'http://%s:%s/' % (Prefs['server'],Prefs['port'])
	Log('URL set to %s' % PVR_URL)
	ValidatePrefs()

# This main function will setup the displayed items.
@handler('/video/nextpvr','NextPVR')
def MainMenu():
	
    dir=ObjectContainer()
    Log('MainMenu: Adding What\'s New Menu')
    dir.add(DirectoryObject(key=Callback(WhatsNewRecordingsMenu), title='What\'s New'))
    Log('MainMenu: Adding Live Menu')
    dir.add(DirectoryObject(key=Callback(LiveMenu), title='Live'))
    Log('MainMenu: Live Menu Added')
    dir.add(PrefsObject(title="Preferences", summary="Configure how to connect to NextPVR", thumb=R("icon-prefs.png")))
    Log('MainMenu: URL set to %s' % PVR_URL)
    return dir
	
@route('/video/nextpvr/live')
def LiveMenu():
	oc = ObjectContainer(title2='Live')
	
	testURL = PVR_URL + 'live?channel=2'
	Log('LiveMenu: URL set to %s' % testURL)
	oc.add(
		CreateVideoObject(
			url = testURL,
			title = 'Test 1-Live',
			summary = testURL
		)
	)
	testURL = PVR_URL + 'live?recording=18121' 
	oc.add(
		CreateVideoObject(
			url = testURL,
			title = 'Test 2-Recorded',
			summary = testURL
		)
	)
	testURL = PVR_URL + 'live?recording=18234'
	oc.add(
		CreateVideoObject(
			url = testURL,
			title = 'Test 3-In progress',
			summary = testURL
		)
	)
	return oc

@route('/video/nextpvr/whatsnewrecordings')
def WhatsNewRecordingsMenu():
	Log('Generating Recordings Screen')
	oc = ObjectContainer(title2='What\'s New')
	Log('Calling Recording List')
	url = PVR_URL + 'services?method=recording.list&filter=Ready&sid=plex'
	Log('Loading URL %s' % url)
	request = urllib2.Request(url, headers={"Accept" : "application/xml"})
	Log('Request: %s' % request)
	u = urllib2.urlopen(request)
	Log('Result = %s code= %s' % ( u.code,u.msg))
	tree = ET.parse(u)
	root = tree.getroot()
	Log('Root = %s'  %  root)
	# calculating the start date - to be in <start_time>20/01/2012 10:30:00 a.m.</start_time> format
	newdate = datetime.datetime.now() - datetime.timedelta(days=10)
	newticks = (newdate - datetime.datetime(1970, 1, 1)).total_seconds()
	
	Log('Calculated start date as %s ticks = %d' % (newdate.isoformat(),newticks))
	# Nodes with start_time > stime which is x number of days ago
	recordings = root.findall('recordings/recording')
	for recording in recordings:
		Log('Recording id %s' % recording.find('id').text)
		startticks = int(recording.find('start_time_ticks').text)
		if startticks > newticks:
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
			descr = recording.find('desc').text.strip()
			Log('Desc %s' % descr)
			airdate = datetime.datetime.fromtimestamp(float(recording.find('start_time_ticks').text))
			Log('Air date %s' % airdate.strftime('%c'))
			oc.add(
				CreateVideoObject(
					url=testURL, 
					title='%s - %s' % (recording.find('name').text.encode('utf-8'),airdate.strftime('%Y-%m-%d')),
					originally_available_at=airdate,
					duration=int(delta.total_seconds()) * 1000,
					summary=descr
				)
			)
			
			Log('Status %s' % recording.find('status').text.encode('utf-8'))
			Log('Start Time %s' % datetime.datetime.fromtimestamp(float(recording.find('start_time_ticks').text)))
		
	
	oc.objects.sort(key=lambda obj: obj.originally_available_at.isoformat(),reverse=True)
	return oc

####################################################################################################
def CreateVideoObject(url, title, summary, originally_available_at=None, duration=None, include_container=False):
	track_object = EpisodeObject(
		key = Callback(CreateVideoObject, url=url, title=title, summary=summary, originally_available_at=originally_available_at, duration=duration, include_container=True),
		rating_key = url,
		title = title,
		summary = summary,
		originally_available_at = originally_available_at,
		duration = duration,
		thumb = R(ART),
		items = [
			MediaObject(
				parts = [
					PartObject(key=url)
				],
				container = 'mp2ts',
				video_codec = VideoCodec.H264,
				audio_channels = 2,
				optimized_for_streaming = True,
			)
		]
	)

	if include_container:
		return ObjectContainer(objects=[track_object])
	else:
		return track_object

####################################################################################################
def ValidatePrefs():
    
	if Prefs['server'] is None:
		return MessageContainer("Error", "No server information entered.")
	elif Prefs['port'] is None:
		return MessageContainer("Error", "Server port is not defined")
	elif not Prefs['port'].isdigit():
		return MessageContainer("Error", "Server port is not numeric")
	else:
		port = Prefs['port']
		PVR_URL = 'http://%s:%s/' % (Prefs['server'],port)
		Log('PVR URL = %s' % PVR_URL)
		#return MessageContainer("Success","Success")

####################################################################################################
