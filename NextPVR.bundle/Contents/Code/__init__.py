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
####################################################################################################
VIDEO_PREFIX = "/video/nextpvr"

NAME = "NextPVR"
ART  = 'item-default.png'
PVR_URL = 'http://%s:%s/' % (Prefs['server'],Prefs['port'])
####################################################################################################

def Start():
    
	ObjectContainer.title1 = NAME
	Log('%s Started' % NAME)
	#PVR_URL = 'http://%s:%s/' % (Prefs['server'],Prefs['port'])
	Log('URL set to %s' % PVR_URL)
	ValidatePrefs()

####################################################################################################
# This main function will setup the displayed items.
@handler('/video/nextpvr','NextPVR')
def MainMenu():
	
    dir=ObjectContainer()
    Log('MainMenu: Adding What\'s New Menu')
    dir.add(DirectoryObject(key=Callback(WhatsNewRecordingsMenu), title='What\'s New'))
    Log('MainMenu: Adding Live Menu')
    #dir.add(DirectoryObject(key=Callback(LiveMenu), title='Live'))
    dir.add(DirectoryObject(key=Callback(RecordingsMenu), title='Recordings'))

    #Log('MainMenu: Live Menu Added')
    dir.add(PrefsObject(title="Preferences", summary="Configure how to connect to NextPVR", thumb=R("icon-prefs.png")))
    Log('MainMenu: URL set to %s' % PVR_URL)
    return dir

####################################################################################################	
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

####################################################################################################
@route('/video/nextpvr/whatsnewrecordings')
def WhatsNewRecordingsMenu():
	Log('WhatsNewRecordingsMenu: Generating WhatsNewRecordingsMenu Screen')
	oc = ObjectContainer(title2='What\'s New')
	Log('WhatsNewRecordingsMenu: Calling Recording List')
	url = PVR_URL + 'services?method=recording.list&filter=Ready&sid=plex'
	Log('Loading URL %s' % url)
	request = urllib2.Request(url, headers={"Accept" : "application/xml"})
	Log('WhatsNewRecordingsMenu: Request: %s' % request)
	u = urllib2.urlopen(request)
	Log('WhatsNewRecordingsMenu: Result = %s code= %s' % ( u.code,u.msg))
	tree = ET.parse(u)
	#tree = ET.parse('g:\\recordings\\services.xml')
	root = tree.getroot()
	
	# calculating the start date - to be in <start_time>20/01/2012 10:30:00 a.m.</start_time> format
	whatsnewdays = int(Prefs['whatsnewdays'])
	
	newdate = datetime.datetime.now() - datetime.timedelta(days=whatsnewdays)
	newticks = (newdate - datetime.datetime(1970, 1, 1)).total_seconds()
	Log('WhatsNewRecordingsMenu: Calculated start date "%d" days ago as "%s" ticks = %d' % (whatsnewdays,newdate.isoformat(),newticks))

	# Nodes with start_time > stime which is x number of days ago
	recordings = root.findall('recordings/recording')
	for recording in recordings:
		Log('WhatsNewRecordingsMenu: Recording id %s' % recording.find('id').text)
		startticks = int(recording.find('start_time_ticks').text)
		if startticks > newticks:
			oc.add(ConvertRecordingToEpisode(recording,dateasname=False))
			Log('WhatsNewRecordingsMenu: Status %s' % recording.find('status').text.encode('utf-8'))
		
	
	oc.objects.sort(key=lambda obj: obj.rating_key,reverse=True)
	Log('WhatsNewRecordingsMenu: Completed WhatsNewRecording Menu')
	#oc.objects.sort(key=lambda obj: obj.url,reverse=True)
	return oc

####################################################################################################
@route('/video/nextpvr/recordings')
def RecordingsMenu():
	Log('RecordingsMenu: Generating Recordings Screen')
	oc = ObjectContainer(title2='Recordings')
	Log('RecordingsMenu: Calling Recording List')
	url = PVR_URL + 'services?method=recording.list&filter=Ready&sid=plex'
	Log('RecordingsMenu: Loading URL %s' % url)
	request = urllib2.Request(url, headers={"Accept" : "application/xml"})
	Log('RecordingsMenu: Request: %s' % request)
	u = urllib2.urlopen(request)
	Log('RecordingsMenu: Result = %s code= %s' % ( u.code,u.msg))
	tree = ET.parse(u)
	#tree = ET.parse('g:\\recordings\\services.xml')
	root = tree.getroot()
	
	# Nodes with start_time > stime which is x number of days ago
	recordings = root.findall('recordings/recording')
	shows = []
	for recording in recordings:
		Log('RecordingsMenu: **********************************************************************************************************')
		showname = recording.find('name').text
		Log('RecordingsMenu: Recording id %s name is \'%s\'' % (recording.find('id').text,showname))
		if showname not in shows:
			Log('RecordingsMenu: Adding %s to showset and Directory' % showname)
			shows.append(showname)
			oc.add(DirectoryObject(key=Callback(AddEpisodeObject, show_title=showname), title=showname))
		
	
	oc.objects.sort(key=lambda obj: obj.title)
	Log('RecordingsMenu: Finished adding Episodes')		
	return oc

####################################################################################################
def AddEpisodeObject(show_title):
	oc = ObjectContainer(title2=show_title)
	url = PVR_URL + 'services?method=recording.list&filter=Ready&sid=plex'
	Log('AddEpisodeObject: Loading URL %s' % url)
	request = urllib2.Request(url, headers={"Accept" : "application/xml"})
	Log('Request: %s' % request)
	u = urllib2.urlopen(request)
	Log('AddEpisodeObject: Result = %s code= %s' % ( u.code,u.msg))
	tree = ET.parse(u)
	#tree = ET.parse('g:\\recordings\\services.xml')
	root = tree.getroot()
	Log('Root = %s'  %  root)
	
	# Nodes with start_time > stime which is x number of days ago
	recordings = root.findall('recordings/recording')
	for recording in recordings:
		showname = recording.find('name').text
		if showname == show_title:
			oc.add(ConvertRecordingToEpisode(recording,dateasname=True))

	oc.objects.sort(key=lambda obj: obj.rating_key,reverse=False)
	return oc

####################################################################################################
#@route('/video/nextpvr/videoobject')
def CreateVideoObject(url, title, summary, rating_key, originally_available_at=None, duration=None, channel=None,include_container=False):
	Log('Date %s ' % originally_available_at)

	if int(duration) <1:
		duration = '50'

	if not channel is None:
		thumb = PVR_URL + 'services?method=channel.icon&channel_id=%s' % channel
	else:
		thumb = R(ART)

	track_object = EpisodeObject(
		key = Callback(CreateVideoObject, url=url, title=title, summary=summary, rating_key=rating_key,originally_available_at=originally_available_at, duration=duration, channel=channel,include_container=True),
		title = title,
		summary = summary,
		originally_available_at = Datetime.ParseDate(originally_available_at),
		duration = int(duration),
		rating_key=int(rating_key),
		thumb = thumb,
		items = [
			MediaObject(
				parts = [
					PartObject(key=url)
				],
				container = 'mp2ts',
				#video_codec = VideoCodec.H264,
				#audio_channels = 2,
				optimized_for_streaming = True
			)
		]
	)

	if include_container:
		return ObjectContainer(objects=[track_object])
	else:
		return track_object

####################################################################################################
def ValidatePrefs():
	global PVR_URL
	if Prefs['server'] is None:
		return MessageContainer("Error", "No server information entered.")
	elif Prefs['port'] is None:
		return MessageContainer("Error", "Server port is not defined")
	elif not Prefs['port'].isdigit():
		return MessageContainer("Error", "Server port is not numeric")
	else:
		port = Prefs['port']
		PVR_URL = 'http://%s:%s/' % (Prefs['server'],port)
		Log('ValidatePrefs: PVR URL = %s' % PVR_URL)
		return MessageContainer("Success","Success")

####################################################################################################
def ConvertRecordingToEpisode(recording, dateasname):
	showname = recording.find('name').text
	Log('**********************************************************************************************************')

	#set the show name
	epname = showname

	testURL = PVR_URL + 'live?recording=%s' % recording.find('id').text
	Log('ConvertRecordingToEpisode: Name  "%s" URL="%s"' % (showname,testURL))
	#add duration of video
	try:
		durationtext = recording.find('duration').text
		t = datetime.datetime.strptime(durationtext,"%H:%M")
		delta = datetime.timedelta(hours=t.hour, minutes=t.minute, seconds=0)
	except:
		Warning('ConvertRecordingToEpisode: Recording: "%s", Duration error, Unexpected error' % showname)
		delta = datetime.timedelta(hours=1, minutes=0,seconds=0)
	if not delta is None:
		Log('ConvertRecordingToEpisode: Duration Set to "%d"' % delta.total_seconds())
	else:
		Log('ConvertRecordingToEpisode: Duration Set is empty')
	
	# Added test for empty description
	try:
		descr = recording.find('desc').text.strip()
	except:
		Warning('ConvertRecordingToEpisode: Recording: "%s", Descr error, Unexpected error' % showname)
		descr = showname
	Log('ConvertRecordingToEpisode: Desc Set to "%s"' % descr)

	#Added try/Catch for dates
	try:
		airdate = datetime.datetime.fromtimestamp(float(recording.find('start_time_ticks').text))
	except:
		Warning('ConvertRecordingToEpisode: Recording: "%s", AirTime error, Unexpected error' % showname)
		airdate = datetime.datetime.now()

	try:
		channel = recording.find('channel_id').text
		if channel == '0':
			channel = None
	except:
		Warning('ConvertRecordingToEpisode: Recording: "%s", Could not set channel ID' % showname)			
		channel = None
	if not channel is None:
		Log('ConvertRecordingToEpisode: Channel ID set to "%s"' % channel)
		
	#set episode name - if date as name bool set then use the the date, otherwide use teh showname and the date (whats new)
	if dateasname:
		epname = airdate.strftime('%Y-%m-%d')
	else:
		epname = showname + ' - ' + airdate.strftime('%Y-%m-%d')

	Log('ConvertRecordingToEpisode: Setting episode name to date "%s"' % epname)

	Log('ConvertRecordingToEpisode: Air date %s in iso format:%d' % (airdate.strftime('%c'),int(airdate.strftime('%Y%m%d%H%M'))))
	return CreateVideoObject(
		url=testURL,
		title=epname,
		summary=descr,
		rating_key=str(int(airdate.strftime('%Y%m%d%H%M'))),
		originally_available_at=airdate.strftime('%c'),
		duration=str(int(delta.total_seconds() * 1000)),
		channel=channel
	)
