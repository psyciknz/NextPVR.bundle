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

NAME = "NextPVR"
ART  = 'item-default.png'
ICON     = 'icon-default.png'
PVR_URL = 'http://%s:%s/' % (Prefs['server'],Prefs['port'])
PMS_URL = 'http://localhost:32400%s'

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
 
    Log('Client Details: ident:%s' %  clientident)
    dir=ObjectContainer()
    Log('MainMenu: Adding Live Menu')
    dir.add(DirectoryObject(key=Callback(LiveMenu), title='Live',thumb=R('live.jpg')))
    Log('MainMenu: Adding Channel Menu')
    dir.add(DirectoryObject(key=Callback(ChannelMenu), title='Channel',thumb=R('live.jpg')))

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
    Log('MainMenu: Live Menu Added')
    dir.add(PrefsObject(title="Preferences", summary="Configure how to connect to NextPVR", thumb=R("icon-prefs.png")))
    Log('MainMenu: URL set to %s' % PVR_URL)
    return dir

####################################################################################################	
@route('/video/nextpvr/live')
def LiveMenu():
	oc = ObjectContainer(title2='Live')

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
			call_sign = channelname,
			rating_key=float(channelnumber),
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
        
        )
      )
    return oc

####################################################################################################
@route('/video/nextpvr/videoclipobject')
#def CreateVideoClipObject(url, title, summary, rating_key, channel=None, container='mp2ts', include_container=False, includeRelated=False,**kwargs):
def CreateVideoClipObject(url, title, summary, rating_key,call_sign='',  channel=None, container='mp2ts', include_container=False, includeRelated=False,includeRelatedCount=False,includeBandwidths=True):
	
	showthumb = PVR_URL + 'service?method=recording.artwork&recording_id=%s&sid=plex' % str(rating_key)
	Log('CreateVideoClipObject Getting artwork url "%s"' % showthumb)
	if not channel is None:
		Log('Getting logo the old way')
		thumb = PVR_URL + 'services?method=channel.icon&channel_id=%s' % channel
		Log('Getting logo the old way: ' + PVR_URL + 'services?method=channel.icon&channel_id=%s' % channel)
		
		if thumb is None:
			thumb = R(call_sign + '.jpg')
			Log('Logo: ' + call_sign + '.png')
			if thumb is None:
				Log('Getting the default logo the new way')
				thumb = R(ICON)
	else:
		thumb = R(ART)

	Log('CreateVideoClipObject: Playvideo: %s' % url)
	track_object = EpisodeObject(
		key = Callback(CreateVideoClipObject, url=url, title=title, summary=summary, rating_key=rating_key,call_sign=call_sign,channel=channel,container=container,include_container=True, includeRelated=False,includeRelatedCount=False,includeBandwidths=True),
		title = title ,
		summary = summary,
		originally_available_at = datetime.datetime.now(),
		duration = int(3600),
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
