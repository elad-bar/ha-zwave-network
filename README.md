# Home Assistant Z-Wave Network Viewer

## Description
Presents the nodes available in Z-Wave network

## Environment Variables
```
HA_URL:     Format PROTOCOL://IP:PORT
HA_TOKEN:   Long-live token from Home Assistant
```

## Docker Compose
```
version: '2'
services:
  ha-zwave-network:
    image: "eladbar/ha-zwave-network:latest"
    container_name: "ha-zwave-network"
    hostname: "ha-zwave-network"
    restart: unless-stopped
    environment:
      - HA_URL=http://127.0.0.1:8123
      - HA_TOKEN=token
```
