# xbmc-nfo importer
# spec'd from: http://wiki.xbmc.org/index.php?title=Import_-_Export_Library#Video_nfo_Files
#
# Original code author: Harley Hooligan
# Modified by Guillaume Boudreau
#
import os, re, time, datetime

plextoken = ''
TVDB_SERIE_SEARCH            = 'http://thetvdb.com/api/GetSeries.php?seriesname={0}'                                                 #
TVDB_IMAGES_URL              = 'http://thetvdb.com/banners/'                                                                      # TVDB picture directory
        

class npvrxml(Agent.TV_Shows):
	name = 'NPVR TV .xml Importer'
	ver = '0.2'
	primary_provider = True
	languages = [Locale.Language.NoLanguage, Locale.Language.English, Locale.Language.Czech, Locale.Language.Danish, Locale.Language.German,
             Locale.Language.Greek, Locale.Language.Spanish, Locale.Language.Finnish, Locale.Language.French,
             Locale.Language.Hebrew, Locale.Language.Croatian, Locale.Language.Hungarian, Locale.Language.Italian,
             Locale.Language.Latvian, Locale.Language.Dutch, Locale.Language.Norwegian, Locale.Language.Polish,
             Locale.Language.Portuguese, Locale.Language.Russian, Locale.Language.Slovak, Locale.Language.Swedish,
             Locale.Language.Thai, Locale.Language.Turkish, Locale.Language.Vietnamese, Locale.Language.Chinese,
             Locale.Language.Korean]
	accepts_from = ['com.plexapp.agents.localmedia','com.plexapp.agents.thetvdb','com.plexapp.agents.opensubtitles','com.plexapp.agents.podnapisi','com.plexapp.agents.plexthememusic','com.plexapp.agents.subzero']
	contributes_to = ['com.plexapp.agents.thetvdb']
	fallback_agent = ['com.plexapp.agents.thetvdb']
	
	
		
	def Start():
		Log("Start")
		
		pass

	def search(self, results, media, lang):
		if Prefs['plextoken']:
			if not Prefs['plextoken'] == 'replace me':
				plextoken = "?X-Plex-Token={0}".format(Prefs['plextoken'])
				Log("Found plex token: " + plextoken)
			else:
				plextoken = ""
				Log("Default plex token found")
		else:
			Log("No plex token found")
			plextoken = ""
			
		
		Log("Searching: plex token: " + plextoken)
		pageUrl="http://localhost:32400/library/metadata/" + media.id + "/tree{0}".format(plextoken)
		#page=HTTP.Request(pageUrl)
		#Log(media.primary_metadata)
		if not media is None:
			Log("Search: Curent media name: " + media.name)
		else:
			Log("Search: Empty media found")
			
		Log(XML.ElementFromURL(pageUrl).xpath('//MediaContainer/MetadataItem/MetadataItem/MetadataItem/MetadataItem'))
		npvrXML = XML.ElementFromURL(pageUrl).xpath('//MediaContainer/MetadataItem/MetadataItem/MetadataItem/MediaItem/MediaPart')[0]
		path1 = String.Unquote(npvrXML.get('file'))
		Log("Search: Retrieved path from plex: " + path1)
		#path = os.path.dirname(path1)
		fileExtension = path1.split(".")[-1].lower()
		Log("Search: Retrieved ext from plex: " + fileExtension)
		xmlFile = path1.replace('.'+fileExtension, '.xml')
		
		Log("Search: Looking for XMLFile " + xmlFile)		
		if os.path.exists(xmlFile):
			Log("+++++++++++++++++++++ Opening XMLFile " + xmlFile)	
			nfoText = Core.storage.load(xmlFile)
			nfoTextLower = nfoText.lower()
			year = 0
			Log("Search: Media Name: %s id: %s" % (media.name,media.id))
			tvshowname = media.name
		
			Log("Search: Checking for <recording> tag")	
			if nfoTextLower.count('<recording') > 0 and nfoTextLower.count('</recording>') > 0:
				Log('Found the tag, likely an NPVR XML file')	
				#likely an xbmc nfo file
				try: npvrXML = XML.ElementFromString(nfoText).xpath('//recording')[0]
				except:
					Log('Search: ERROR: Cant parse XML in ' + xmlFile + '. Aborting!')
					return
				#tv show name
				Log('Search: Looking for TV Show Title')
				try: tvshowname=npvrXML.xpath("title")[0].text
				except:
					Log("Search: ERROR: No <title> tag in " + xmlFile + ". Aborting!")
					return
				Log('Search: Found tv show title: ' + tvshowname)
				#tv show name
				Log('Search: Looking for Year in <startTime> Tag')
				try: year=npvrXML.xpath("startTime")[0].text
				except:
					Log("Search: Error grabbing year from <startTime>")
				Log('Search: Show name: ' + tvshowname)
				Log('Search: Year: ' + str(year[:4]))
			if tvshowname:
				Log('Search: We have a show name updating results: ' + tvshowname)
				name = tvshowname
				results.Append(MetadataSearchResult(id=media.id, name=name, year=year[:4], lang=lang, score=100))
				for result in results:
					Log('Search: scraped results: ' + result.name + ' | year = ' + str(result.year) + ' | id = ' + result.id + '| score = ' + str(result.score))
			else:
				Log("Search: ERROR: No tvshowname (from <title>) tag in " + xmlFile + ". Aborting!")
		else:
			Log("Search: No XML File for file, Adding media id" + media.id + "  Media Name: " + media.name)
			mod_time = os.path.getmtime(path1)
			results.Append(MetadataSearchResult(id=media.id, name=media.name, year=time.localtime(mod_time)[0], lang=lang, score=100))
			
	def update(self, metadata, media, lang):
		if Prefs['plextoken']:
			if not Prefs['plextoken'] == 'replace me':
				plextoken = "?X-Plex-Token={0}".format(Prefs['plextoken'])
				Log("Found plex token: " + plextoken)
			else:
				plextoken = ""
				Log("Default plex token found")
		else:
			Log("No plex token found")
			plextoken = ""
			
		Log("Update: Media ID = " + media.id + " Metadata ID = " + metadata.id +  " plex token: " + plextoken)
		#Log('Dumping self')
		#dumpvar(obj=self)
		#Log('Dumping Media')
		#dumpvar(obj=media)
		#Log('Dumping Metadata')
		#dumpvar(obj=metadata)
		id = media.id
		Log('Update: Update called for TV Show with id = ' + id + ' Media.title: ' + media.title + " GIUD: " + metadata.guid )
		pageUrl = "http://localhost:32400/library/metadata/" + id + "/tree{0}".format(plextoken)
		#page = HTTP.Request(pageUrl)
		xml = XML.ElementFromURL(pageUrl)
		metasplit = metadata.guid.replace('?','/').split('/')
		
		#doesn't work.
		#tvdb_id = ""
		#tvdb_id = Core.messaging.call_external_function('com.plexapp.agents.thetvdb','MessageKit:GetTvdbId')
		#if not tvdb_id is None:
		#	Log("Search TVDB ID: " + tvdb_id)
		
		#Log("Guid Split Count: " + len(metasplit))
		# if len(metasplit) > 4: 
			# Log("Looking at an episode GUID")
			# ep_name = metasplit[-2]
			# npvrXML = xml.xpath("//MetadataItem[@index='" + ep_name + "']")[0]
			# stemp = "Xml Count " , len(npvrXML)
			# Log(stemp)
			# id = String.Unquote(npvrXML.get('id'))
			# Log("ID = " + String.Unquote(npvrXML.get('id')))
			# for article in npvrXML:
				# Log(XML.StringFromElement(article))
			# Log("Loaded xml xpath: " + "//MetadataItem[@index='%s']" % ep_name)
			# #Log('xml = ' + XML.StringFromElement(npvrXML))
			# npvrxmlFile = npvrXML.xpath("MediaItem/MediaPart")[0]
			# #Log('npvrxmlFile = ' + XML.StringFromElement(npvrxmlFile))
			# stemp = "Xml Count " , len(npvrxmlFile)
			# Log(stemp)
			# #for article in npvrxmlFile:
			# #	Log(XML.StringFromElement(article))
			# path1 = String.Unquote(npvrxmlFile.get('file'))
			# pageUrl = "http://localhost:32400/library/metadata/" + id + "/tree"
			# Log("Loading Epside Tree Page: " + pageUrl)
			# page = HTTP.Request(pageUrl)
			# xml = XML.ElementFromURL(pageUrl)
		# else:
			# Log("Looking at a Show GUID")
			# ep_name = ""
			# #Log('xml = ' + XML.StringFromElement(xml))
			# npvrXML = xml.xpath('//MediaContainer/MetadataItem/MetadataItem/MetadataItem/MediaItem/MediaPart')[0]
			# stemp = "Xml Count " , len(npvrXML)
			# Log(stemp)
			# path1 = String.Unquote(npvrXML.get('file'))
		
		ep_name = ""
		#Log('xml = ' + XML.StringFromElement(xml))
		npvrXML = xml.xpath('//MediaContainer/MetadataItem/MetadataItem/MetadataItem/MediaItem/MediaPart')[0]
		stemp = "Xml Count " , len(npvrXML)
		Log(stemp)
		path1 = String.Unquote(npvrXML.get('file'))
		
		path = os.path.dirname(path1)
		fileExtension = path1.split(".")[-1].lower()
		Log("Update: Retrieved ext from plex: " + fileExtension)
		#com.plexapp.agents.npvrxml://90581/2016/308?lang=xn
		
		Log("Update: Retrieved media ep name plex: " + ep_name)
		xmlFile = path1.replace('.'+fileExtension, '.xml')

		# Grabs the TV Show data
		posterFilename = path + "/folder.jpg"
		if os.path.exists(posterFilename):
			posterData = Core.storage.load(posterFilename)
			metadata.posters['folder.jpg'] = Proxy.Media(posterData)
			Log('Update: Found poster image at ' + posterFilename)
		else:
			Log("Update: No poster data found")

		bannerFilename = path + "/folder-banner.jpg"
		if os.path.exists(bannerFilename):
			bannerData = Core.storage.load(bannerFilename)
			metadata.banners['folder-banner.jpg'] = Proxy.Media(bannerData)
			Log('Update: Found banner image at ' + bannerFilename)
		else:
			Log("Update: No banner data found")

		fanartFilename = path + "/fanart.jpg"
		if os.path.exists(fanartFilename):
			fanartData = Core.storage.load(fanartFilename)
			metadata.art['fanart.jpg'] = Proxy.Media(fanartData)
			Log('Update: Found fanart image at ' + fanartFilename)
		else:
			Log("Update: No fanart data found")
		
		if os.path.exists(xmlFile):
			Log("Loading xml File: " + xmlFile)
			nfoText = Core.storage.load(xmlFile)
			nfoTextLower = nfoText.lower()
				
			if nfoTextLower.count('<recording') > 0 and nfoTextLower.count('</recording>') > 0:
				Log("Update: Looks like an NPVR XML file (has <recording>)")
				#likely an xbmc nfo file
				try: npvrXML = XML.ElementFromString(nfoText).xpath('//recording')[0]
				except:
					Log('Update: ERROR: Cant parse XML in file: ' + xmlFile)
					return

				#summary
				Log('Update: Getting Episode summary from xml file')
				metadata.summary = "Summary text"
				Log('Update: Episode summary set to ' + metadata.summary)
				try: metadata.summary = npvrXML.xpath('./description')[0].text
				except:
					Log('Update: No summary posted to episode: ' + xmlFile)
					metadata.summary = "n/a"
					pass
				if  not metadata.summary:
					metadata.summary = "n/a"
					
				Log('Update: Episode summary set to ' + metadata.summary)
				#year
				try:
					Log('Update: Setting AirDate from <startTime>')
					try:
						air_date_s = npvrXML.xpath("startTime")[0].text
						Log('Update: AirDate_s ' + str(air_date_s))
						air_date = time.strptime(air_date_s, "%Y-%m-%d %H:%M:%S")
					except: 
						Log('Update: ERROR setting airdate')
						pass
					Log('Update: AirDate set: ' + str(air_date))
					if air_date:
						metadata.originally_available_at = datetime.datetime.fromtimestamp(time.mktime(air_date)).date()
				except: 
					Log('Update: ERROR setting the airdate from Starttime')
					pass
				#title
				#Log('Looking for title, setting to Date first:' + media.title)
				#title_o = media.title
				#try: title = npvrXML.xpath('./subtitle')[0].text
				#except: pass
				#if (not title):
				#	metadata.title = title_o
				#else:
				#	metadata.title = title
					
				#title
				Log('Looking for title, setting to Date first:' + media.title + " ep_name " + ep_name)
				#title_o = media.title
				try: title = npvrXML.xpath('./title')[0].text
				except: pass
				
				if (not ep_name):
					Log('Using Title')
					metadata.title = title
				else:
					Log('Using ep_name')
					metadata.title = ep_name
					
				Log('Episode parent title set to : ' + metadata.title)
				#studio
				Log('Update: Setting Studio from <channel>')
				try:
					stud_channel = npvrXML.findall("channel")[0].text
					Log('<channel> ' + stud_channel)
					metadata.studio = stud_channel
					Log('Update: Studio Set to ' + metadata.studio)
				except Exception, e: 
					Log('Update: ERROR settings studio: ' + str(e))
					pass
				#Rating
				Log('Update: Setting Rating from <rating>')
				try:
					rating = npvrXML.findall("rating")[0].text
					Log('<rating> ' + rating)
					metadata.content_rating = rating
					Log('Update: rating Set to ' + metadata.content_rating)
				except Exception, e: 
					metadata.content_rating = "unknown"
					Log('Update: ERROR settings rating: ' + str(e))
					pass
				#airdate
				try:
					air_date_s = npvrXML.xpath("startTime")[0].text
					Log('Update: AirDate_s ' + str(air_date_s))
					air_date_start = time.strptime(air_date_s, "%Y-%m-%d %H:%M:%S")
					air_date_start_epoch = time.mktime(air_date_start)
					air_date_end_s = npvrXML.xpath("endTime")[0].text
					Log('Update: AirDate_end_s ' + str(air_date_end_s) + '    ' + str(air_date_start))
					air_date_end = time.strptime(air_date_end_s, "%Y-%m-%d %H:%M:%S")
					Log('Update: Got End time to datetime:' + str(air_date_end) )
					air_date_end_epoch = time.mktime(air_date_end)
					time_taken = (air_date_end_epoch - air_date_start_epoch)
					Log('Update: Time taken: ' + str(time_taken))
					metadata.duration = int(time_taken) * 1000 # ms
					Log('Update: Duration set to ' + str(metadata.duration))
				except:
					Log('Update: Error setting air date or duration')
					pass
				
				Log("Update: ++++++++++++++++++++++++")
				Log("Update: TV Episode nfo Information")
				Log("Update: ------------------------")
				Log("Update: ID: " + str(metadata.id))
				Log("Update: Title: " + str(metadata.title))
				Log("Update: Summary: " + str(metadata.summary))
				Log("Update: Year: " + str(metadata.originally_available_at))
				Log("Update: Rating: " + str(metadata.content_rating))
				Log("Update: ++++++++++++++++++++++++")
			else:
				Log("Update: ERROR: <recording> tag not found in episode XML file " + xmlFile)
		else:
			Log("No XML File found for episode: " + xmlFile)
			
		# Grabs the season data
		@parallelize
		def UpdateEpisodes():
			if Prefs['plextoken']:
				if not Prefs['plextoken'] == 'replace me':
					plextoken = "?X-Plex-Token={0}".format(Prefs['plextoken'])
					Log("Found plex token: " + plextoken)
				else:
					plextoken = ""
					Log("Default plex token found")
			else:
				Log("No plex token found")
				plextoken = ""
			
			Log("UpdateEpisodes called plex token: " + plextoken)
			pageUrl="http://localhost:32400/library/metadata/" + metadata.id + "/children{0}".format(plextoken)
			seasonList = XML.ElementFromURL(pageUrl).xpath('//MediaContainer/Directory')

			seasons=[]
			for seasons in seasonList:
				try: seasonID=seasons.get('key')
				except: 
					Log('UpdateEpisodes: Error getting seasonID')
					return
					
				try: season_num=seasons.get('index')
				except: 
					Log('UpdateEpisodes: Error getting season num')
					return

				if seasonID.count('allLeaves') == 0:
				
					Log("Finding episodes")

					pageUrl="http://localhost:32400" + seasonID + plextoken
					Log("UpdateEpisodes: Page URl: " + pageUrl)

					episodes = XML.ElementFromURL(pageUrl).xpath('//MediaContainer/Video')
					Log("UpdateEpisodes: Found " + str(len(episodes)) + " episodes.")
			
					episodeXML = []
					for episodeXML in episodes:
						ep_num = episodeXML.get('index')
						ep_key = episodeXML.get('key')
		
						Log("UpdateEpisodes: Found episode with key: " + ep_key)

						# Get the episode object from the model
						episode = metadata.seasons[season_num].episodes[ep_num]		
						Log("UpdateEpisodes: Calling update episode for " + ep_key)

						# Grabs the episode information
						@task
						def UpdateEpisode(episode=episode, season_num=season_num, ep_num=ep_num, ep_key=ep_key, path=path1):
							Log("UpdateEpisode called for episode S" + str(season_num) + "E" + str(ep_num))
							if(ep_num.count('allLeaves') == 0):
								pageUrl="http://localhost:32400" + ep_key + "/tree{0}".format(plextoken)
								Log('UpdateEpisode: UPDATE: ' + pageUrl)
								path1 = XML.ElementFromURL(pageUrl).xpath('//MediaPart')[0].get('file')
								Log('UpdateEpisode: UPDATE: ' + path1)
								filepath=path1.split
								path = os.path.dirname(path1)
								id=ep_num
								fileExtension = path1.split(".")[-1].lower()


								# Grabs the TV Show data
								posterFilename = path + "/folder.jpg"
								if os.path.exists(posterFilename):
									posterData = Core.storage.load(posterFilename)
									metadata.seasons[season_num].posters[posterFilename] = Proxy.Media(posterData)
									Log('UpdateEpisode: Found season for ' + str(season_num) + ' poster image at ' + posterFilename)
								else:
									Log("UpdateEpisode: No poster data found")

								bannerFilename = path +  "/folder-banner.jpg"
								if os.path.exists(bannerFilename):
									bannerData = Core.storage.load(bannerFilename)
									metadata.seasons[season_num].banners[bannerFilename] = Proxy.Media(bannerData)
									Log('UpdateEpisode: Found season for ' + str(season_num) + ' banner image at ' + bannerFilename)
								else:
									Log("UpdateEpisode: No posterbanner data found")


								xmlFile = path1.replace('.'+fileExtension, '.xml')
								Log("UpdateEpisode: Looking for episode XML file " + xmlFile)
								if os.path.exists(xmlFile):
									Log("UpdateEpisode: xmlFile File exists...")
									nfoText = Core.storage.load(xmlFile)
									nfoTextLower = nfoText.lower()
									if nfoTextLower.count('<recording') > 0 and nfoTextLower.count('</recording>') > 0:
										Log("UpdateEpisode: Looks like an NPVR XML file (has <recording>)")
										#likely an xbmc nfo file
										try: npvrXML = XML.ElementFromString(nfoText).xpath('//recording')[0]
										except:
											Log('UpdateEpisode: ERROR: Cant parse Episode XML in file: ' + xmlFile)
											return

										#title
										Log('UpdateEpisode: Looking for title, setting to Ep Number first: ' + ep_num)
										title2 = ep_num
										try: title = npvrXML.xpath('./subtitle')[0].text
										except: 
											Log('UpdateEpisode: Error retrieving episode subtitle (title)')
											pass
										if (not title):
											episode.title = title2
										else:
											episode.title = title
										Log('UpdateEpisode: Episode title set to  ' + episode.title)
										#summary
										episode.summary = "Summary text"
										try: episode.summary = npvrXML.xpath('./description')[0].text
										except:
											Log('UpdateEpisode: No summary posted to episode: ' + xmlFile)
											episode.summary = "n/a"
											pass
										if not episode.summary:
											episode.summary = "n/a"
											
										Log('UpdateEpisode: Episode summary set to ' + episode.summary)
										#year
										try:
											Log('UpdateEpisode: Setting AirDate from <startTime>')
											try:
												air_date_s = npvrXML.xpath("startTime")[0].text
												Log('UpdateEpisode: AirDate_s ' + str(air_date_s))
												air_date = time.strptime(air_date_s, "%Y-%m-%d %H:%M:%S")
											except: 
												Log('UpdateEpisode: Error setting Air_date')
												pass
											Log('UpdateEpisode: AirDate set: ' + str(air_date))
											if air_date:
												episode.originally_available_at = datetime.datetime.fromtimestamp(time.mktime(air_date)).date()
										except: 
											Log('UpdateEpisode: Error setting originally_available value')
											pass
										#studio
										#Log('UpdateEpisode: Setting Studio from <channel>')
										#try:
										#	stud_channel = npvrXML.findall("channel")[0].text
										#	Log('UpdateEpisode: <channel> ' + stud_channel)
										#	episode.studio = npvrXML.findall("channel")[0].text
										#	Log('UpdateEpisode: Studio Set to ' + episode.studio)
										#except Exception, e: 
										#	Log('UpdateEpisode: error setting studio:' + str(e))
										#	pass
										#Rating
										Log('UpdateEpisode: Setting Rating from <rating>')
										try:
											rating = npvrXML.findall("rating")[0].text
											Log('<rating> ' + rating)
											episode.content_rating = rating
											Log('UpdateEpisode: rating Set to ' + episode.content_rating)
										except Exception, e: 
											episode.content_rating = "unknown"
											Log('UpdateEpisode: ERROR settings rating: ' + str(e) + ' Rating set to :' + episode.content_rating)
											pass
										#airdate
										try:
											air_date_s = npvrXML.xpath("startTime")[0].text
											Log('UpdateEpisode: AirDate_s ' + str(air_date_s))
											air_date_start = time.strptime(air_date_s, "%Y-%m-%d %H:%M:%S")
											air_date_start_epoch = time.mktime(air_date_start)
											air_date_end_s = npvrXML.xpath("endTime")[0].text
											Log('UpdateEpisode: AirDate_end_s ' + str(air_date_end_s) + '    ' + str(air_date_start))
											air_date_end = time.strptime(air_date_end_s, "%Y-%m-%d %H:%M:%S")
											Log('UpdateEpisode: Got End time to datetime:' + str(air_date_end) )
											air_date_end_epoch = time.mktime(air_date_end)
											time_taken = (air_date_end_epoch - air_date_start_epoch)
											Log('UpdateEpisode: Time taken: ' + str(time_taken))
											episode.duration = int(time_taken) * 1000 # ms
											Log('UpdateEpisode; Duration set to ' + str(episode.duration))
										except:
											Log('UpdateEpisode: Error setting air date or duration')
											pass
											
										Log("UpdateEpisode:  ++++++++++++++++++++++++")
										Log("UpdateEpisode: TV Episode nfo Information")
										Log("UpdateEpisode: ------------------------")
										Log("UpdateEpisode: Title: " + str(episode.title))
										Log("UpdateEpisode: Summary: " + str(episode.summary))
										Log("UpdateEpisode: Rating: " + str(episode.content_rating))
										Log("UpdateEpisode: Year: " + str(episode.originally_available_at))
										Log("UpdateEpisode: ++++++++++++++++++++++++")
									else:
										Log("UpdateEpisode: ERROR: <recording> tag not found in episode XML file " + xmlFile)
								
def dumpvar(obj):
	for attr in dir(obj):
		Log("obj.%s = %s" % (attr, getattr(obj, attr)))
	return
