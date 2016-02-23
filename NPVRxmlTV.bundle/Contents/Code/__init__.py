# xbmc-nfo importer
# spec'd from: http://wiki.xbmc.org/index.php?title=Import_-_Export_Library#Video_nfo_Files
#
# Original code author: Harley Hooligan
# Modified by Guillaume Boudreau
#
import os, re, time, datetime

class npvrxml(Agent.TV_Shows):
	name = 'NPVR TV .xml Importer'
	primary_provider = True
	languages = [Locale.Language.English]
	
		
	def Start():
		Log("Start")
		pass

	def search(self, results, media, lang):
		Log("Searching")
		pageUrl="http://localhost:32400/library/metadata/" + media.id + "/tree"
		page=HTTP.Request(pageUrl)
		Log(media.primary_metadata)
		Log("Curent media name: " + media.name)
		Log(XML.ElementFromURL(pageUrl).xpath('//MediaContainer/MetadataItem/MetadataItem/MetadataItem/MetadataItem'))
		npvrXML = XML.ElementFromURL(pageUrl).xpath('//MediaContainer/MetadataItem/MetadataItem/MetadataItem/MediaItem/MediaPart')[0]
		path1 = String.Unquote(npvrXML.get('file'))
		Log("Retrieved path from plex: " + path1)
		#path = os.path.dirname(path1)
		fileExtension = path1.split(".")[-1].lower()
		Log("Retrieved ext from plex: " + fileExtension)
		xmlFile = path1.replace('.'+fileExtension, '.xml')
		
		Log("Looking for XMLFile " + xmlFile)		
		if os.path.exists(xmlFile):
			Log("+++++++++++++++++++++ Opening XMLFile " + xmlFile)	
			nfoText = Core.storage.load(xmlFile)
			nfoTextLower = nfoText.lower()
			year = 0
			Log("Media Name:" + media.name)
			tvshowname = media.name
			Log("Checking for <recording> tag")	
			if nfoTextLower.count('<recording') > 0 and nfoTextLower.count('</recording>') > 0:
				Log('Found the tag, likely an NPVR XML file')	
				#likely an xbmc nfo file
				try: npvrXML = XML.ElementFromString(nfoText).xpath('//recording')[0]
				except:
					Log('ERROR: Cant parse XML in ' + xmlFile + '. Aborting!')
					return
				#tv show name
				Log('Looking for TV Show Title')
				try: tvshowname=npvrXML.xpath("title")[0].text
				except:
					Log("ERROR: No <title> tag in " + xmlFile + ". Aborting!")
					return
				Log('Found tv show title: ' + tvshowname)
				#tv show name
				Log('Looking for Year in <startTime> Tag')
				try: year=npvrXML.xpath("startTime")[0].text
				except:
					Log("Error grabbing year from <startTime>")
				Log('Show name: ' + tvshowname)
				Log('Year: ' + str(year[:4]))
			if tvshowname:
				Log('We have a show name updating results: ' + tvshowname)
				name = tvshowname
				results.Append(MetadataSearchResult(id=media.id, name=name, year=year[:4], lang=lang, score=100))
				for result in results:
					Log('scraped results: ' + result.name + ' | year = ' + str(result.year) + ' | id = ' + result.id + '| score = ' + str(result.score))
			else:
				Log("ERROR: No tvshowname (from <title>) tag in " + xmlFile + ". Aborting!")
		else:
			Log("No XML File for file, Adding media id" + media.id + "  Media Name: " + media.name)
			mod_time = os.path.getmtime(path1)
			results.Append(MetadataSearchResult(id=media.id, name=media.name, year=time.localtime(mod_time)[0], lang=lang, score=100))
			
	def update(self, metadata, media, lang):
		Log("Metadata GUID = " + metadata.guid[0])
		id = re.compile('.npvrxml\://([0-9]+)\?lang').findall(metadata.guid)[0]
		Log('Update called for TV Show with id = ' + id)
		pageUrl = "http://localhost:32400/library/metadata/" + id + "/tree"
		page = HTTP.Request(pageUrl)
		xml = XML.ElementFromURL(pageUrl)
		#Log('xml = ' + XML.StringFromElement(xml))
		npvrXML = xml.xpath('//MediaContainer/MetadataItem/MetadataItem/MetadataItem/MediaItem/MediaPart')[0]
		path1 = String.Unquote(npvrXML.get('file'))
		path = os.path.dirname(path1)

		# Grabs the TV Show data
		posterFilename = path + "/folder.jpg"
		if os.path.exists(posterFilename):
			posterData = Core.storage.load(posterFilename)
			metadata.posters['folder.jpg'] = Proxy.Media(posterData)
			Log('Found poster image at ' + posterFilename)

		bannerFilename = path + "/folder-banner.jpg"
		if os.path.exists(bannerFilename):
			bannerData = Core.storage.load(bannerFilename)
			metadata.banners['folder-banner.jpg'] = Proxy.Media(bannerData)
			Log('Found banner image at ' + bannerFilename)

		fanartFilename = path + "/fanart.jpg"
		if os.path.exists(fanartFilename):
			fanartData = Core.storage.load(fanartFilename)
			metadata.art['fanart.jpg'] = Proxy.Media(fanartData)
			Log('Found fanart image at ' + fanartFilename)

		# Grabs the season data
		@parallelize
		def UpdateEpisodes():
			Log("UpdateEpisodes called")
			pageUrl="http://localhost:32400/library/metadata/" + metadata.id + "/children"
			seasonList = XML.ElementFromURL(pageUrl).xpath('//MediaContainer/Directory')

			seasons=[]
			for seasons in seasonList:
				try: seasonID=seasons.get('key')
				except: pass
				try: season_num=seasons.get('index')
				except: pass

				if seasonID.count('allLeaves') == 0:
				
					Log("Finding episodes")

					pageUrl="http://localhost:32400" + seasonID

					episodes = XML.ElementFromURL(pageUrl).xpath('//MediaContainer/Video')
					Log("Found " + str(len(episodes)) + " episodes.")
			
					episodeXML = []
					for episodeXML in episodes:
						ep_num = episodeXML.get('index')
						ep_key = episodeXML.get('key')
		
						Log("Found episode with key: " + ep_key)

						# Get the episode object from the model
						episode = metadata.seasons[season_num].episodes[ep_num]				

						# Grabs the episode information
						@task
						def UpdateEpisode(episode=episode, season_num=season_num, ep_num=ep_num, ep_key=ep_key, path=path1):
							Log("UpdateEpisode called for episode S" + str(season_num) + "E" + str(ep_num))
							if(ep_num.count('allLeaves') == 0):
								pageUrl="http://localhost:32400" + ep_key + "/tree"
								path1 = XML.ElementFromURL(pageUrl).xpath('//MediaPart')[0].get('file')
								Log('UPDATE: ' + path1)
								filepath=path1.split
								path = os.path.dirname(path1)
								id=ep_num
								fileExtension = path1.split(".")[-1].lower()


								# Grabs the TV Show data
								posterFilename = path + "/folder.jpg"
								if os.path.exists(posterFilename):
									posterData = Core.storage.load(posterFilename)
									metadata.seasons[season_num].posters[posterFilename] = Proxy.Media(posterData)
									Log('Found season for ' + str(season_num) + ' poster image at ' + posterFilename)
		
								bannerFilename = path +  "/folder-banner.jpg"
								if os.path.exists(bannerFilename):
									bannerData = Core.storage.load(bannerFilename)
									metadata.seasons[season_num].banners[bannerFilename] = Proxy.Media(bannerData)
									Log('Found season for ' + str(season_num) + ' banner image at ' + bannerFilename)


								xmlFile = path1.replace('.'+fileExtension, '.xml')
								Log("Looking for episode XML file " + xmlFile)
								if os.path.exists(xmlFile):
									Log("xmlFile File exists...")
									nfoText = Core.storage.load(xmlFile)
									nfoTextLower = nfoText.lower()
									if nfoTextLower.count('<recording') > 0 and nfoTextLower.count('</recording>') > 0:
										Log("Looks like an NPVR XML file (has <recording>)")
										#likely an xbmc nfo file
										try: npvrXML = XML.ElementFromString(nfoText).xpath('//recording')[0]
										except:
											Log('ERROR: Cant parse XML in file: ' + xmlFile)
											return

										#title
										Log('Looking for title, setting to Ep Number first' + ep_num)
										title = ep_num
										try: title = npvrXML.xpath('./subtitle')[0].text
										except: pass
										if (not title):
											episode.title = ep_num
										else:
											episode.title = title
										Log('Episode title set to  ' + episode.title)
										#summary
										episode.summary = "Summary text"
										try: episode.summary = npvrXML.xpath('./description')[0].text
										except:
											Log('No summary posted to episode: ' + xmlFile)
											episode.summary = episode.title
										Log('Episode summary set to ' + episode.summary)
										#year
										try:
											Log('Setting AirDate from <startTime>')
											try:
												air_date_s = npvrXML.xpath("startTime")[0].text
												Log('AirDate_s ' + str(air_date_s))
												air_date = time.strptime(air_date_s, "%Y-%m-%d %H:%M:%S")
											except: pass
											Log('AirDate set: ' + str(air_date))
											if air_date:
												episode.originally_available_at = datetime.datetime.fromtimestamp(time.mktime(air_date)).date()
										except: pass
										#studio
										Log('Setting Studio from <channel>')
										try:
											Log('<channel> ' + npvrXML.findall("channel")[0].text)
											episode.studio = npvrXML.findall("channel")[0].text
											Log('Studio Set to ' + episode.studio)
										except: pass
										#airdate
										#try:
										air_date_s = npvrXML.xpath("startTime")[0].text
										Log('AirDate_s ' + str(air_date_s))
										air_date_start = time.strptime(air_date_s, "%Y-%m-%d %H:%M:%S")
										air_date_start_epoch = time.mktime(air_date_start)
										air_date_end_s = npvrXML.xpath("endTime")[0].text
										Log('AirDate_end_s ' + str(air_date_end_s) + '    ' + str(air_date_start))
										air_date_end = time.strptime(air_date_end_s, "%Y-%m-%d %H:%M:%S")
										Log('Got End time to datetime:' + str(air_date_end) )
										air_date_end_epoch = time.mktime(air_date_end)
										time_taken = (air_date_end_epoch - air_date_start_epoch)
										Log('Time taken: ' + str(time_taken))
										episode.duration = int(time_taken) * 1000 # ms
										Log('Duration set to ' + str(episode.duration))
										#except:
										#	Log('Error settiung duration')
										#	pass
										thumbFilename = xmlFile.replace('.nfo', '.tbn')
										if os.path.exists(thumbFilename):
											Log("Found episode thumb " + thumbFilename)
											episode.thumbs[thumbFilename] = Proxy.Media(Core.storage.load(thumbFilename))
										else:
											Log("Using folder.jpg from directory")
											try:
												episode.thumbs[posterFilename] = posterData
												Log("Folder.jpg loaded as episode poster")
											except: pass
										Log("++++++++++++++++++++++++")
										Log("TV Episode nfo Information")
										Log("------------------------")
										Log("Title: " + str(episode.title))
										Log("Summary: " + str(episode.summary))
										Log("Year: " + str(episode.originally_available_at))
										Log("++++++++++++++++++++++++")
									else:
										Log("ERROR: <recording> tag not found in episode XML file " + xmlFile)
								
