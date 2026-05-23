# Copy this file to cookies.py and paste your nexusmods.com cookies below.
#
# How to capture:
#   1. Open Chrome devtools -> Network tab on www.nexusmods.com (logged in).
#   2. Manually click "Manual Download" on any mod page (e.g.
#      https://www.nexusmods.com/stardewvalley/mods/5371?tab=files&file_id=56774).
#   3. Find the POST to `Downloads?GenerateDownloadUrl`.
#   4. Right-click -> Copy as cURL.
#   5. Paste into https://curlconverter.com/ and copy the `cookies` dict.
#
# Cookies expire periodically. If downloads start 403'ing, re-capture.

cookies = {
    # "sid": "...",
    # "nexusmods_session": "...",
    # "cf_clearance": "...",
    # ...
}
