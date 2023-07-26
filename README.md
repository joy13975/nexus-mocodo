# Nexus Mod Collection Downloader

A very rough bunch of scripts to download entire mod collections from [Nexus Mods](https://next.nexusmods.com/stardewvalley). Does not require Vortex paid membership.

If anyone is actually interested in using this then maybe I will write better code/comments, but for now it's just me so it's a bit of a mess.

## Relevant Files

 - `collection.json`: the collection metadata you get when attempting to download a mod collection via Vortext (free user is fine). Swap it with your collection of choice.


 - `download_mods.py`: a script that downloads all mods from Nexus Mods according to the listing in `collection.json`.


 - `unzip_mods.py`: a script that automates unzipping. Sometimes zip files cannot be unzipped by python's `zipfile` lib and you need to manually use 3rd party apps to unzip.
