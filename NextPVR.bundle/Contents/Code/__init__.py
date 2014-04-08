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
import socket
####################################################################################################
VIDEO_PREFIX = "/video/nextpvr"

NAME = "NextPVR"
ART  = 'item-default.png'
PVR_URL = 'http://%s:%s/' % (Prefs['server'],Prefs['port'])
PMS_URL = 'http://localhost:32400%s'
OPCODE_DATA = (websocket.ABNF.OPCODE_TEXT, websocket.ABNF.OPCODE_BINARY)

clientident = 'xxxxxxx'
####################################################################################################

def Start():
    
    ObjectContainer.title1 = NAME
    Log('%s Started' % NAME)
    #PVR_URL = 'http://%s:%s/' % (Prefs['server'],Prefs['port'])
    Log('URL set to %s' % PVR_URL)
    
    try:
        # Get curret server version and save it to dict.
        server_version = XML.ElementFromURL(PMS_URL % '', errors='ignore').attrib['version']
        Log('Server Version is %s' % server_version)
        Dict['server_version'] = server_version

        if not 'nowPlaying' in Dict:
            Dict['nowPlaying'] = dict()
    except: pass

    Thread.Create(SocketListen)
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
 
    Log('Client Details: ident:%s' %  clientident)
    dir=ObjectContainer()
    Log('MainMenu: Adding What\'s New Menu')
    dir.add(DirectoryObject(key=Callback(WhatsNewRecordingsMenu), title='What\'s New'))
    Log('MainMenu: Adding Live Menu')
    dir.add(DirectoryObject(key=Callback(LiveMenu), title='Live'))
    Log('MainMenu: Adding Recordings Menu')
    dir.add(DirectoryObject(key=Callback(RecordingsMenu), title='Recordings'))
    
    #http://192.168.1.100:8866/streamer/vlc/stream.aspx?url=/live?channel=3
    #dir.add(
	#	CreateVideoClipObject(
	#		url = PVR_URL + 'live?channel=3',
	#		title = 'TestLive3',
	#		rating_key=1,
	#		channel=3
	#		)
	#	)
    #Log('MainMenu: Live Menu Added')
    dir.add(PrefsObject(title="Preferences", summary="Configure how to connect to NextPVR", thumb=R("icon-prefs.png")))
    Log('MainMenu: URL set to %s' % PVR_URL)
    return dir

####################################################################################################	
@route('/video/nextpvr/live')
def LiveMenu():
	oc = ObjectContainer(title2='Live')

	clientident = ''
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
	#tree = ET.parse('g:\\recordings\\live.xml')
	root = tree.getroot()
	
	# Nodes with start_time > stime which is x number of days ago
	channels = root.findall('listings/channel')
	shows = []
	for channel in channels:
		Log('LiveMenu: **********************************************************************************************************')
		channelname = channel.attrib['name']
		channelnumber = channel.attrib['number']
		channelid = channel.attrib['id']
		
		Log('LiveMenu: Channel number \'%s\' name is \'%s\'' % (channelnumber, channelname))
		
		Log('LiveMenu: Getting first programme for %s' % channelname)
		programme = channel.find('l')
		summary = channelname
		if programme is None:
			programmname = channelname
		else:
			Log('LiveMenu: Looking for programme name for channel %s' % channelname)
			programmname = channelname + ' : ' + programme.find('name').text
			summary = programme.find('description').text

		Log('LiveMenu: Channel name %s, Summary %s' % (programmname,summary))
		
		testURL = PVR_URL + 'live?channel=%s&sid=plex&client=%s' % (channelnumber,clientident)
		Log('LiveMenu: URL set to %s' % testURL)
		oc.add(
		CreateVideoClipObject(
			url = testURL,
			title = programmname,
			summary=summary,
			rating_key=int(channelnumber),
			channel=channelid
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
		
	
	#oc.objects.sort(key=lambda obj: obj.rating_key,reverse=True)
	oc.objects.sort(key=lambda obj: obj.originally_available_at,reverse=True)
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

	#oc.objects.sort(key=lambda obj: obj.rating_key,reverse=False)
	oc.objects.sort(key=lambda obj: obj.originally_available_at,reverse=False)
	return oc

####################################################################################################
#@route('/video/nextpvr/videoobject')
def CreateVideoObject(url, title, summary, rating_key, playback_position, originally_available_at=None, duration=0, channel=None, container='mp2ts', include_container=False):
	Log('Date %s ' % originally_available_at)

	if int(duration) <1:
		duration = '3600000'

	playbackstring = ''
	unwatchedstring = ''
	try:
		Log('Playback position %d' % playback_position)
		if int(playback_position) > 0:
			playbackstring = str(datetime.timedelta(seconds=playback_position))
			playbackstring = 'Last Playback position: ' + playbackstring + '            '
			unwatchedstring = '*'
	except:
		playbackstring = ''

	if not channel is None:
		thumb = PVR_URL + 'services?method=channel.icon&channel_id=%s&sid=plex' % channel
	else:
		thumb = R(ART)

	track_object = EpisodeObject(
		key = Callback(CreateVideoObject, url=url, title=unwatchedstring + title, summary=playbackstring + ' ' + summary, rating_key=rating_key,playback_position=playback_position,originally_available_at=originally_available_at, duration=duration, channel=channel,container=container,include_container=True),
		title = unwatchedstring + title ,
		summary = playbackstring + ' ' + summary,
		originally_available_at = Datetime.ParseDate(originally_available_at),
		duration = int(duration),
		rating_key=int(rating_key),
		thumb = thumb,
		items = [
			MediaObject(
				parts = [
					PartObject(key=url)
				],
				container = container,
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
@route('/video/nextpvr/videoclipobject')
def CreateVideoClipObject(url, title, summary, rating_key, channel=None, container='mp2ts', include_container=False):
	
	if not channel is None:
		thumb = PVR_URL + 'services?method=channel.icon&channel_id=%s' % channel
	else:
		thumb = R(ART)

	Log('CreateVideoClipObject: Playvideo: ' + url)
	track_object = EpisodeObject(
		key = Callback(CreateVideoClipObject, url=url, title=title, summary=summary, rating_key=rating_key,channel=channel,container=container,include_container=True),
		title = title ,
		summary = summary,
		originally_available_at = datetime.datetime.now(),
		duration = int(3600000),
		rating_key=int(rating_key),
		thumb = thumb,
		items = [
			MediaObject(
				parts = [
					PartObject(key=url)
				],
				container = container,
				#video_codec = VideoCodec.H264,
				#audio_channels = 2,
				optimized_for_streaming = True
			)
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

def PlayVideo(channel,url):
	# Tune in to the stream
	Log('Playvideo: ' + url)
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
	duration = str(int(delta.total_seconds() * 1000))

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
	return CreateVideoObject(
		url=testURL,
		title=epname,
		summary=descr,
		#rating_key=str(int(airdate.strftime('%Y%m%d%H%M'))),
		rating_key=str(epid),
		playback_position=position,
		originally_available_at=airdate.strftime('%c'),
		duration=duration,
		channel=channel
	)

####################################################################################################
@route('/video/nextpvr/socketlisten')
def SocketListen():
    
    ws = websocket.create_connection('ws://localhost:32400/:/websockets/notifications')
    
    def SocketRecv():
        frame = ws.recv_frame()
        if not frame:
            raise websocket.WebSocketException("Not a valid frame %s" % frame)
        elif frame.opcode in OPCODE_DATA:
            return (frame.opcode, frame.data)
        elif frame.opcode == websocket.ABNF.OPCODE_CLOSE:
            ws.send_close()
            return (frame.opcode, None)
        elif frame.opcode == websocket.ABNF.OPCODE_PING:
            ws.pong("Hi!")
    
        return None, None
    
    while True:
        opcode, data = SocketRecv()
        msg = None
        if opcode in OPCODE_DATA:
            info = JSON.ObjectFromString(data)
            Log.Debug("Data received: type = " + info['type'])
            
            #scrobble
            if info['type'] == "playing":
                sessionKey = str(info['_children'][0]['sessionKey'])
                state = str(info['_children'][0]['state'])
                viewOffset = str(info['_children'][0]['viewOffset'])
                Log.Debug(sessionKey + " - " + state + ' - ' + viewOffset)
                Scrobble(sessionKey,state,viewOffset)
            
            #adding to collection
            elif info['type'] == "timeline" and Dict['new_sync_collection']:
                if (info['_children'][0]['type'] == 1 or info['_children'][0]['type'] == 4) and info['_children'][0]['state'] == 0:
                    Log.Info("New File added to Libray: " + info['_children'][0]['title'] + ' - ' + str(info['_children'][0]['itemID']))
                    itemID = info['_children'][0]['itemID']
                    # delay sync to wait for metadata
                    #Thread.CreateTimer(120, CollectionSync,True,itemID,'add')
                    
                # #deleted file (doesn't work yet)
                elif (info['_children'][0]['type'] == 1 or info['_children'][0]['type'] == 4) and info['_children'][0]['state'] == 9:
                    Log.Info("File deleted from Libray: " + info['_children'][0]['title'] + ' - ' + str(info['_children'][0]['itemID']))
                #     itemID = info['_children'][0]['itemID']
                #     # delay sync to wait for metadata
                #     CollectionSync(itemID,'delete')
                
    return

####################################################################################################
@route('/video/nextpvr/scrobble')
def Scrobble(sessionKey,state,viewOffset):
    
    #fix for pht (not sending pause or stop when finished playing)
    #delete sessiondata if viewOffset is smaller than previous session viewOffset
    #we assume, that in this case it could be a new file.
    #if the user simply seeks backwards on the client, this is also triggered.
    action = 'nothing'
    if sessionKey in Dict['nowPlaying']:
        if 'prev_viewOffset' in Dict['nowPlaying'][sessionKey] and Dict['nowPlaying'][sessionKey]['prev_viewOffset'] > viewOffset:
            del Dict['nowPlaying'][sessionKey]
        else:
            Dict['nowPlaying'][sessionKey]['prev_viewOffset'] = viewOffset
    
    #skip over unkown items etc.        
    if sessionKey in Dict['nowPlaying'] and 'skip' in Dict['nowPlaying'][sessionKey]:
        return
    
    if not sessionKey in Dict['nowPlaying']:
        Log.Info('getting MetaData for current media')

        try:
            pms_url = PMS_URL % ('/status/sessions/')
            xml_content = XML.ElementFromURL(pms_url).xpath('//MediaContainer/Video')
            for section in xml_content:
                ratingKey = section.get('ratingKey')
                Log.Info('Rating Key: ' + ratingKey + '   SessionKey: ' + sessionKey)
                if section.get('sessionKey') == sessionKey and '/video/nextpvr/:/function/CreateVideoObject' in section.get('key'):
                    Log.Debug('Looking for Item metadata for ' + ratingKey + ' for session key: ' + sessionKey)
                    Dict['nowPlaying'][sessionKey] = get_metadata_from_pms(xml_content)
                    Log.Debug('Item metadata for ' + ratingKey + ' has been set to session key: ' + sessionKey)
                    
                    Dict['nowPlaying'][sessionKey]['UserName'] = ''
                    Dict['nowPlaying'][sessionKey]['UserID'] = ''
                    
                    for user in section.findall('User'):
                        Dict['nowPlaying'][sessionKey]['UserName'] = user.get('title')
                        Dict['nowPlaying'][sessionKey]['UserID'] = user.get('id')
                    
                    # setup some variables in Dict
                    Dict['nowPlaying'][sessionKey]['Last_updated'] = Datetime.FromTimestamp(0)
                    Dict['nowPlaying'][sessionKey]['scrobbled'] = False
                    Dict['nowPlaying'][sessionKey]['cur_state'] = state
                    Dict['nowPlaying'][sessionKey]['prev_viewOffset'] = 0
            
            # if session wasn't found, return False
            if not (sessionKey in Dict['nowPlaying']):
                Log.Info('Session data not found')
                return
                
        except Ex.HTTPError, e:
            Log.Error('Failed to connect to %s.' % pms_url)
            return
        except Ex.URLError, e:
            Log.Error('Failed to connect to %s.' % pms_url)
            return
    
    # calculate play progress
    Dict['nowPlaying'][sessionKey]['progress'] = int(round((float(viewOffset)/(Dict['nowPlaying'][sessionKey]['duration']*60*1000))*100, 0))
    Dict['nowPlaying'][sessionKey]['viewOffset'] = viewOffset
    
    if (state != Dict['nowPlaying'][sessionKey]['cur_state'] and state != 'buffering'):
        if (state == 'stopped') or (state == 'paused'):
            Log.Debug(Dict['nowPlaying'][sessionKey]['title']+' paused or stopped, cancel watching')
            action = 'cancelwatching'
        elif (state == 'playing'):
            Log.Debug('Updating watch status for '+Dict['nowPlaying'][sessionKey]['title'])
            action = 'watching'
    
    #scrobble item
    elif state == 'playing' and Dict['nowPlaying'][sessionKey]['scrobbled'] != True and Dict['nowPlaying'][sessionKey]['progress'] > 80:
        Log.Debug('Scrobbling '+Dict['nowPlaying'][sessionKey]['title'])
        action = 'scrobble'
        Dict['nowPlaying'][sessionKey]['scrobbled'] = True
    
    # update every 2 min
    elif state == 'playing' and ((Dict['nowPlaying'][sessionKey]['Last_updated'] + Datetime.Delta(seconds=30)) < Datetime.Now()):
        Log.Debug('Updating watch status for '+Dict['nowPlaying'][sessionKey]['title'])
        action = 'watching'
    
    else:
        # Already watching or already scrobbled
        Log.Debug('Nothing to do this time for '+Dict['nowPlaying'][sessionKey]['title'])
        return
    
    # Setup Data to send to Trakt
    values = dict()
    
    if Dict['nowPlaying'][sessionKey]['type'] == 'episode':
        values['ratingKey'] = Dict['nowPlaying'][sessionKey]['ratingKey']
    
    values['duration'] = Dict['nowPlaying'][sessionKey]['duration']
    values['progress'] = Dict['nowPlaying'][sessionKey]['progress']
    values['position'] = int(Dict['nowPlaying'][sessionKey]['viewOffset'])/1000
    
    values['title'] = Dict['nowPlaying'][sessionKey]['title']

    Log.Debug('This will be where we put the NextPVR URL with the rating key of ' + values['ratingKey'])
	#/service?method=recording.watched.set&recording_id=%s&position=%d" % (ratingKey, values['position'])
    url = PVR_URL + '/service?method=recording.watched.set&recording_id=%s&position=%d&sid=Plex' % (Dict['nowPlaying'][sessionKey]['ratingKey'], values['position'])
    Log('Scrobble: Loading URL %s' % url)
    request = urllib2.Request(url, headers={"Accept" : "application/xml"})
    Log('Request: %s' % request)
    u = urllib2.urlopen(request)

    #result = talk_to_trakt(action, values)
    
    Dict['nowPlaying'][sessionKey]['cur_state'] = state
    Dict['nowPlaying'][sessionKey]['Last_updated'] = Datetime.Now()
    
    #if just scrobbled, force update on next status update to set as watching again
    if action.find('scrobble') > 0:
        Dict['nowPlaying'][sessionKey]['Last_updated'] = Datetime.Now() - Datetime.Delta(minutes=20)
    
    # if stopped, remove data from Dict['nowPlaying']
    if (state == 'stopped' or state == 'paused'):
        del Dict['nowPlaying'][sessionKey] #delete session from Dict
    
    #make sure, that Dict is saved in case of plugin crash/restart
    Dict.Save()
    
    return 

####################################################################################################
@route('/video/nextpvr/get_metadata_from_pms')
def get_metadata_from_pms(xml_content):
    # Prepare a dict that contains all the metadata required for trakt.
    #Log.Debug('Getting Metadata from ' + xml_content)

    try:
        for section in xml_content:
            metadata = dict()

            metadata['ratingKey'] = section.get('ratingKey')
            
            try:
                metadata['duration'] = int(float(section.get('duration'))/60000)
            except: pass

            metadata['type'] = section.get('type')
            
            if metadata['type'] == 'movie':
                metadata['title'] = section.get('title')
            
            elif metadata['type'] == 'episode':
                metadata['title'] = section.get('title')
                metadata['episode_title'] = section.get('title')
                
            else:
                Log('The content type %s is not supported, the item %s will not be ignored.' % (section.get('type'), section.get('title')))

            return metadata
    except Ex.HTTPError, e:
        Log('Failed to connect to %s.' % pms_url)
        return {'status' : False, 'message' : responses[e.code][1]}
    except Ex.URLError, e:
        Log('Failed to connect to %s.' % pms_url)
        return {'status' : False, 'message' : e.reason[0]}

####################################################################################################
