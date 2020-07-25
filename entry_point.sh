echo "const HA_URL = \"$HA_URL\";" >> home-assistant.js
echo "const HA_TOKEN = \"$HA_TOKEN\";" >> home-assistant.js

python3 -m http.server 6123