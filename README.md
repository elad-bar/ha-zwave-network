# Home Assistant Z-Wave Network Viewer

## Description
Presents the nodes available in Z-Wave network

Once docker is up and running, it's accessible in `http://{IP or hostname}:6123`,

Click on a node to get more details on the sidebar.

[GitHub](https://github.com/elad-bar/ha-zwave-network/)

## Environment Variables
```
HA_URL:            Format PROTOCOL://IP:PORT
HA_TOKEN:          Long-live token from Home Assistant
SSL_KEY:           SSL Key Path (Optional)
SSL_CERTIFICATE:   SSL Certificate Path (Optional)
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
      - SSL_KEY=/ssl/ssl.key
      - SSL_CERTIFICATE=/ssl/ssl.pem
    volumes:
      - /ssl/ssl.key:/ssl/ssl.key:ro
      - /ssl/ssl.pem:/ssl/ssl.pem:ro


```

## SSL Support
To enable SSL support (HTTPS), 
fill in the environment variables `SSL_KEY` and `SSL_CERTIFICATE`,
Use the volume to share the SSL key and certificate with the container.  