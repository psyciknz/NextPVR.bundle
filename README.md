NextPVR-Plex
============

Plex Channel for viewing NextPVR content.  Has the ability to stream live TV in any tuner supported by http://nextpvr.com (which is almost any BDA enabled tuner).

Instructions for adding NextPVR recordings to Plex: https://sites.google.com/a/andc.co.nz/externalportal/nextpvr-plex-library
Quick option added to the agent preferences, where a plex token was required, Follow the support intructions https://support.plex.tv/hc/en-us/articles/204059436-Finding-an-authentication-token-X-Plex-Token to obtaining a valid plex token.

The Plex channel has it's own log in Plex Media Server\Logs\PMS Plugin Logs\com.plexapp.agents.npvrxml.log.  This will normally be needed for any issues.

3 Options for viewing your channels in Plex:
Live - Lists channels and the current show - requires a working EPG (in nextpvr)
Channel List - Using a named channel group (defined in nextpvr) to list channels and ignoring the EPG.  Useful for a Hauppauge Colossus.
Channel Group List - lists all the channel groups and the channels for each.
