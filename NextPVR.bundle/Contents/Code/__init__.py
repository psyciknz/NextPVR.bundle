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
import websocket
import ast
import json
####################################################################################################
VIDEO_PREFIX = "/video/nextpvr"

ver = "0.5"
NAME = "NextPVR"
ART  = 'item-default.png'
ICON     = 'icon-default.png'
PVR_URL = 'http://%s:%s/' % (Prefs['server'],Prefs['port'])
PMS_URL = 'http://localhost:32400%s'

clientident = 'xxxxxxx'
####################################################################################################

def Start():
    
	ObjectContainer.title1 = "{0}: {1}".format(NAME ,ver)
	Log('%s Started' % NAME)
	#PVR_URL = 'http://%s:%s/' % (Prefs['server'],Prefs['port'])
	Log('URL set to %s' % PVR_URL)
    
	Plugin.AddViewGroup("Details", viewMode="InfoList", mediaType="items")
	Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
	
	try:
		# Get curret server version and save it to dict.
		server_version = XML.ElementFromURL(PMS_URL % '', errors='ignore').attrib['version']
		Log('Server Version is %s' % server_version)
		Dict['server_version'] = server_version

		#if not 'nowPlaying' in Dict:
		#	Dict['nowPlaying'] = dict()
	except: pass
		
	Log('No socket listen')
	#Thread.Create(SocketListen)
	ValidatePrefs()

####################################################################################################
# This main function will setup the displayed items.
@handler('/video/nextpvr','NextPVR')
def MainMenu():
	
	Log('Client %s' % Request.Headers)
	clientident = ''
	try:
		clientident = Request.Headers['X-Plex-Client-Identifier']
	except:
		Log('Could not get client details')
	
	mainmenuformat = "All"
	try:
		mainmenuformat = Prefs["mainmenu"]
	except:
		Log('Could not get menui format preferences')
		pass
		
	Log('Client Details: ident:%s' %  clientident)
	
	if mainmenuformat == "Live":
		dir=ObjectContainer()
		dir=LiveMenu()
	elif mainmenuformat == "Channel Group (set below)":
		dir=ObjectContainer()
		dir=ChannelListMenu()
	elif mainmenuformat == "Channel Group List":
		dir=ObjectContainer()
		dir=ChannelGroupMenu()
	else:
		dir=ObjectContainer()
		Log('MainMenu: Adding Live Menu')
		dir.add(DirectoryObject(key=Callback(LiveMenu), title='Live',thumb=R('live.jpg')))
		#Log('MainMenu: Adding Channel Menu')
		#dir.add(DirectoryObject(key=Callback(ChannelMenu), title='Channel',thumb=R('live.jpg')))
		Log('MainMenu: Adding Channel List Menu')
		dir.add(DirectoryObject(key=Callback(ChannelListMenu), title='Channel List',thumb=R('live.jpg')))
		dir.add(DirectoryObject(key=Callback(ChannelGroupMenu), title='Channel Group List',thumb=R('live.jpg')))
		Log('MainMenu: Adding What\'s New Menu')
		dir.add(DirectoryObject(key=Callback(WhatsNewRecordingsMenu), title='What\'s New',thumb=R('new.jpg')))


		#http://192.168.1.100:8866/streamer/vlc/stream.aspx?url=/live?channel=3
		#dir.add(
		#	CreateVideoClipObject(
		#		url = PVR_URL + 'services/service?method=channel.transcode.initiate&channel_id=7224&profile=720p-1024kbps',
		#		title = 'TestLive3',
		#		summary='summary',
		#		rating_key=float(3),
		#		channel=3
		#		)
		#	)
		dir.add(PrefsObject(title="Preferences", summary="Configure how to connect to NextPVR", thumb=R("icon-prefs.png")))
		Log('MainMenu: Live Menu Added')
		
	
	Log('MainMenu: URL set to %s' % PVR_URL)
	return dir

####################################################################################################	
@route('/video/nextpvr/live')
def LiveMenu():
	oc = ObjectContainer(title2='Live', view_group='Details')

	clientident = 'temp'
	try:
		clientident = Request.Headers['X-Plex-Client-Identifier']
	except:
		Log('Could not get client details')

	url = PVR_URL + 'services?method=channel.listings.current&sid=plex&client=%s' % clientident
	Log('LiveMenu: Loading URL %s' % url)
	request = urllib2.Request(url, headers={"Accept" : "application/xml"})
	Log('LiveMenu: Request: %s' % request)
	u = urllib2.urlopen(request)
	Log('LiveMenu: Result = %s code= %s' % ( u.code,u.msg))
	tree = ET.parse(u)
	#Log('LiveMenu: Loading listings from xml file')
	#tree = ET.parse('g:\\plex\\listing.xml')
	root = tree.getroot()
	
	# Nodes with start_time > stime which is x number of days ago
	channels = root.findall('listings/channel')
	Log('LiveMenu: Number of channel entries found: %d' % len(channels))
	shows = []
	for channel in channels:
		Log('LiveMenu: **********************************************************************************************************')
		channelname = channel.attrib['name']
		channelnumber = float(channel.attrib['number'])
		channelid = channel.attrib['id']
		
		Log('LiveMenu: Channel number \'%.2f\' name is \'%s\'' % (channelnumber, channelname))
		
		Log('LiveMenu: Getting first programme for %s' % channelname)
		programme = channel.find('l')
		summary = channelname
		if programme is None:
			title = channelname
		else:
			Log('LiveMenu: Looking for programme name for channel %s' % channelname)
			titleformat = Prefs["titleformat"]
			Log('LiveMenu: Looking for title format')
			if titleformat == "Programme Name":
				title = programme.find('name').text
			elif titleformat == "Channel + Programme Name":
				title = channelname + ' : ' + programme.find('name').text
			elif titleformat == "Channel + Channel Callsign + Programme Name":
				title = channelname + ' (' + str(channelnumber) + ') : ' + programme.find('name').text
			elif titleformat == "Call Sign + Programme Name":
				title = str(channelnumber) + ' : ' + programme.find('name').text
			else: 
				title = channelname + ' : ' + programme.find('name').text
			
			Log('LiveMenu: Looking for programme name for channel %s' % title)
			summarytext = programme.find('description').text
			Log('LiveMenu: Looking for summary name for channel %s' % summarytext)

		Log('LiveMenu: Channel name %s, Summary %s' % (title,summarytext))
		originally_available_at_date = datetime.datetime.today()
		Log('LiveMenu: Date:{0}'.format(originally_available_at_date.strftime("%B %d, %Y")))
		
		testURL = PVR_URL + 'live?channel=%s&sid=plex&client=%s' % (channelnumber,clientident)
		Log('LiveMenu: URL set to %s' % testURL)
		oc.add(
		CreateVideoClipObject(
			url = testURL,
			title = title,
			summary=summarytext,
			call_sign = channelname,
			rating_key=float(channelnumber),
			originally_available_at=originally_available_at_date,
			channel=channelid
			)
		)
	return oc

####################################################################################################	
@route('/video/nextpvr/channel')
def ChannelMenu():
    oc = ObjectContainer(title2='Channel')

    clientident = ''
    try:
      clientident = Request.Headers['X-Plex-Client-Identifier']
    except:
      Log('Could not get client details')

    url = PVR_URL + 'public/GuideService/Listing'
    Log('LiveMenu: Loading URL %s' % url)
    parsed_json = json.load(urllib2.urlopen(url))

    # Nodes with start_time > stime which is x number of days ago
    listings = parsed_json['Guide']['Listings']
    shows = []
    for listing in listings:
      Log('ChannelMenu: **********************************************************************************************************')
      channelname = listing['Channel']['channelName']
      channelnumbermajor = listing['Channel']['channelNumber']
      channelnumberminor = listing['Channel']['channelMinor']
      channelid = listing['Channel']['channelOID']
      
      Log('ChannelMenu: Channel number \'%s\'.\'%s\' name is \'%s\'' % (channelnumbermajor, channelnumberminor, channelname))
      
      summary = listing['EPGEvents'][0]['epgEventJSONObject']['epgEvent']['Desc']
      programmname = listing['EPGEvents'][0]['epgEventJSONObject']['epgEvent']['Title']
      formattedChannel = listing['EPGEvents'][0]['epgEventJSONObject']['epgEvent']['FormattedChannelNumber']

      Log('ChannelMenu: Channel name %s, Summary %s' % (programmname,summary))
      
      playbackUrl = PVR_URL + 'live?channel=%s.%s&sid=plex&client=%s' % (channelnumbermajor,channelnumberminor,clientident) 
      Log('ChannelMenu: URL set to %s' % playbackUrl)

      oc.add(
      CreateVideoClipObject(
        url = playbackUrl,
        title = channelname + ' (' + formattedChannel + ')  ' + programmname,
        summary=summary,
        rating_key=int(channelid),
        call_sign = channelname,
        channel=channelid,
        originally_available_at=datetime.datetime.now()
        )
      )
    return oc

####################################################################################################	
@route('/video/nextpvr/channellist')
def ChannelListMenu(group=None):

	clientident = 'temp'
	oc = ObjectContainer()
	try:
		clientident = Request.Headers['X-Plex-Client-Identifier']
	except:
		Log('Could not get client details')
	
	Log('ChannelListMenu: ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++: ')
	
	if not group is None:
		Log('ChannelListMenu: Getting channel list for passed in group: ' + group)
		chngroup = '&group_id=' + urllib2.quote(group)
		oc = ObjectContainer(title2=group)
	else:
		Log('ChannelListMenu: Getting channel list from name in preferences')
		channelgroup = Prefs['channelgroup']
		if (not channelgroup is None):
			chngroup = '&group_id=' + urllib2.quote(Prefs['channelgroup'])
		else:
			chngroup = ''
		group = 'Empty'
		oc = ObjectContainer(title2='Channel List')
	
	url = PVR_URL + 'services?method=channel.list%s&sid=plex&client=%s' % (chngroup,clientident)
	
	Log('ChannelListMenu: Loading URL %s' % url)
	request = urllib2.Request(url, headers={"Accept" : "application/xml"})
	Log('ChannelListMenu: Request: %s' % request)
	u = urllib2.urlopen(request)
	Log('ChannelListMenu: Result = %s code= %s' % ( u.code,u.msg))
	tree = ET.parse(u)
	#Log('ChannelListMenu: Loading listings from xml file')
	#tree = ET.parse('g:\\plex\\listing.xml')
	root = tree.getroot()
	
	# Nodes with start_time > stime which is x number of days ago
	channels = root.findall('channels/channel')
	Log('ChannelListMenu: Number of channel entries found: %d' % len(channels))
	if (len(channels) > 0):
		for channel in channels:
			Log('ChannelListMenu: **********************************************************************************************************')
			channelname = channel.find('name').text
			channelnumber = float(channel.find('formatted-number').text)
			channelid = channel.find('id').text
			
			Log('ChannelListMenu: Channel number \'%.2f\' name is \'%s\'' % (channelnumber, channelname))
			
			Log('ChannelListMenu: Getting first programme for %s' % channelname)
			summary = channelname
			programmname = channelname
			
			Log('ChannelListMenu: Channel name %s, Summary %s' % (programmname,summary))
			
			testURL = PVR_URL + 'live?channel=%s&sid=plex&client=%s' % (channelnumber,clientident)
			Log('ChannelListMenu: URL set to %s' % testURL)
			oc.add(
			CreateVideoClipObject(
				url = testURL,
				title = programmname,
				summary=summary,
				call_sign = channelname,
				rating_key=float(channelnumber),
				channel=channelid,
				originally_available_at=datetime.datetime.today()
				)
			)
	
	Log('ChannelListMenu: Completed listing for ' + group)
	return oc

####################################################################################################	
@route('/video/nextpvr/channelgroups')
def ChannelGroupMenu():
	oc = ObjectContainer()

	clientident = ''
	try:
	  clientident = Request.Headers['X-Plex-Client-Identifier']
	except:
	  Log('Could not get client details')

	url = PVR_URL + 'public/GuideService/ChannelGroups'
	Log('LiveMenu: Loading URL %s' % url)
	parsed_json = json.load(urllib2.urlopen(url))

	# Nodes with start_time > stime which is x number of days ago
	listings = parsed_json['channelGroupJSONObject']['ChannelGroups']
	for listing in listings:
		Log('ChannelMenu: **********************************************************************************************************')
		if not listing is None:
			Log('ChannelGroupMenu: ' + listing)
		
			oc.add(
			DirectoryObject(
				key=Callback(ChannelListMenu,group=listing), 
				title=listing,
				thumb=R('live.jpg')
				)
			)
			Log('ChannelGroupMenu: Completed ' + listing)
		else:
			Log('ChannelGroupMenu: Skipping entry')
	
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
		
	
	#oc.objects.sort(key=lambda obj: obj.rating_key,reverse=True)
	oc.objects.sort(key=lambda obj: obj.originally_available_at,reverse=True)
	Log('WhatsNewRecordingsMenu: Completed WhatsNewRecording Menu')
	#oc.objects.sort(key=lambda obj: obj.url,reverse=True)
	return oc


####################################################################################################
@route('/video/nextpvr/videoclipobject')
#def CreateVideoClipObject(url, title, summary, rating_key,call_sign='',  channel=None, container='mp2ts', include_container=False, includeRelated=False,includeRelatedCount=False,includeBandwidths=True):
def CreateVideoClipObject(url, title, summary, rating_key, originally_available_at,  call_sign='',channel=None, container='mp2ts', include_container=False, includeRelated=False,includeRelatedCount=False,includeBandwidths=True, duration=3600):
	
	showthumb = PVR_URL + 'service?method=recording.artwork&recording_id=%s&sid=plex' % str(rating_key)
	Log('CreateVideoClipObject Getting artwork url "%s"' % showthumb)
	if not channel is None:
		thumb = PVR_URL + 'services?method=channel.icon&channel_id=%s' % channel
		Log('Getting logo : ' + PVR_URL + 'services?method=channel.icon&channel_id=%s' % channel)
		
		if thumb is None:
			thumb = R(call_sign + '.jpg')
			Log('Logo: ' + call_sign + '.png')
			if thumb is None:
				Log('Getting the default logo the new way')
				thumb = R(ICON)
	else:
		thumb = R(ART)

	Log('CreateVideoClipObject: Playvideo: {0} date: {1}, duration:{2}'.format(url,originally_available_at,duration))
	Log('CreateVideoClipObject: Playvideo: {0}:{1}'.format(title,summary))
	if type(originally_available_at) is not datetime.date:
		Log('CreateVideoClipObject - not a date')
		originally_available_at_date=datetime.datetime.now()
	else:
		Log('CreateVideoClipObject - a date')
		originally_available_at_date=originally_available_at
		
	track_object = EpisodeObject(
		key = Callback(CreateVideoClipObject, url=url, title=title, summary=summary, rating_key=rating_key,originally_available_at=originally_available_at,call_sign=call_sign,channel=channel,container=container,include_container=True, includeRelated=False,includeRelatedCount=False,includeBandwidths=True,duration=duration),
		title = title ,
		summary = summary,
		originally_available_at = datetime.datetime.now(),
		duration = int(duration),
		rating_key=float(rating_key),
		thumb = Resource.ContentsOfURLWithFallback(url=thumb, fallback='icon-default.png'),
		items = [
			MediaObject(
				parts = [
					PartObject(key=Callback(PlayVideo, url=url))
				],
				container = container,
				#video_resolution = 128,
				#video_codec = VideoCodec.H264,
				#video_codec = 'h264',
				#audio_codec = 'aac_latm',
				#audio_channels=2,
				#bitrate = 13000,
				#video_resolution=480,
				optimized_for_streaming = True
			)
			#,
			# MediaObject(
                    # parts = [PartObject(key=Callback(PlayVideo, url=url))],
					# container = container,
                    # video_resolution = 1080,
                    # bitrate = 8000, #8000 #12000
                    # video_codec = VideoCodec.H264,
                    # audio_codec = "aac_latm",
                    # audio_channels = 2,
                    # optimized_for_streaming = True
                # ),
                # MediaObject(
                    # parts = [PartObject(key=Callback(PlayVideo, url=url))],
					# container = container,
                    # video_resolution = 720,
                    # bitrate = 2000, #2000 #8000
                    # video_codec = VideoCodec.H264,
                    # audio_codec = "aac_latm",
                    # audio_channels = 2,
                    # optimized_for_streaming = True
                # ),
                # MediaObject(
                    # parts = [PartObject(key=Callback(PlayVideo, url=url))],
                    # container = container,
                    # video_resolution = 480,
                    # bitrate = 1500, #1500 #2000
                    # video_codec = VideoCodec.H264,
                    # audio_codec = "aac_latm",
                    # audio_channels = 2,
                    # optimized_for_streaming = True
                # ),
                # MediaObject(
                    # parts = [PartObject(key=Callback(PlayVideo, url=url))],
                    # container = container,
                    # video_resolution = 240,
                    # bitrate = 720, # 720 #1500
                    # video_codec = VideoCodec.H264,
                    # audio_codec = "aac_latm",
                    # audio_channels = 2,
                    # optimized_for_streaming = True
                # )
		]
	)
	#track_object = VideoClipObject(
	#	key = Callback(CreateVideoClipObject, url=url, title=title, rating_key=rating_key,channel=channel,container=container,include_container=True),
	#	title = title ,
	#	rating_key=int(rating_key),
	#	thumb = thumb,
	#	items = [
	#		MediaObject(
	#			parts = [
	#				PartObject(
	#					key=Callback(PlayVideo, channel='3',url = url),
	#					duration = 3600
	#				)
	#			],
	#			container =  container,
	#			duration = 3600,
	#			audio_channels = 2,
	#			#audio_codec = AudioCodec.AAC,
	#			#video_codec = VideoCodec.H264,
	#			optimized_for_streaming = True
	#		)
	#	]
	#)

	if include_container:
		return ObjectContainer(objects=[track_object])
	else:
		return track_object
		
@route('/video/nextpvr/playvideo')
def PlayVideo(url):
	# Tune in to the stream
	Log('Playvideo method redirecting to : ' + url)
	return Redirect(url)
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

	epid = recording.find('id').text
	position = 0

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
	duration = int(delta.total_seconds() * 1000)

	# Added test for empty description
	try:
		descr = recording.find('desc').text.strip()
	except:
		Warning('ConvertRecordingToEpisode: Recording: "%s", Descr error, Unexpected error' % showname)
		descr = showname
	Log('ConvertRecordingToEpisode: Desc Set to "%s"' % descr)

	# Added test for empty description
	try:
		status = recording.find('status').text.strip()
	except:
		Warning('ConvertRecordingToEpisode: Recording: "%s", Status error, Unexpected error' % showname)
		status = 'Reading'

	if status == 'Recording':
		duration = '3600'
	Log('ConvertRecordingToEpisode: Duration  Set to "%s"' % duration)

	#Added try/Catch for dates
	try:
		airdate = datetime.datetime.fromtimestamp(float(recording.find('start_time_ticks').text))
	except:
		Warning('ConvertRecordingToEpisode: Recording: "%s", AirTime error, Unexpected error' % showname)
		airdate = datetime.datetime.now()

	try:
		positiontext = recording.find('playback_position').text
		position = int(positiontext)
	except:
		Warning('ConvertRecordingToEpisode: Recording: "%s", Position error, Unexpected error' % showname)

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
	Log('Returning Video Object')
	return CreateVideoClipObject(
		url=testURL,
		title=epname,
		summary=descr,
		#rating_key=str(int(airdate.strftime('%Y%m%d%H%M'))),
		rating_key=str(epid),
		originally_available_at=airdate,
		duration=duration,
		channel=channel
	)
	
