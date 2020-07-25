# Home Assistant Z-Wave Network Viewer

## Description
Presents the nodes available in Z-Wave network

Once docker is up and running, it's accessible in `http://{IP or hostname}:6123`,

Click on a node to get more details on the sidebar.

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
    ports:
      - 6123:6123
    environment:
      - HA_URL=http://127.0.0.1:8123
      - HA_TOKEN=token
```

## Home Assistant Allow CORS origin
Since the call will be performed from another domain / IP and port,
CORS origin setting must be approved by Home-Assistant, to do that add: 

```yaml
http:
  cors_allowed_origins:
    - URL of Docker
```