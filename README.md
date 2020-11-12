# Home Assistant Z-Wave Network Viewer

## Description
Z-Wave network graph for Home Assistant, 
Supports both ZWave and OZW integrations. 

Once docker is up and running, it's accessible in `http://{IP or hostname}:6123`,

Click on a node to get more details on the sidebar.

[GitHub](https://github.com/elad-bar/ha-zwave-network/)

## Environment Variables
```
HA_URL:            Format PROTOCOL://IP:PORT
HA_TOKEN:          Long-live token from Home Assistant
SSL_KEY:           SSL Key Path (Optional)
SSL_CERTIFICATE:   SSL Certificate Path (Optional)
DEBUG:             Setting to True will change log level to DEBUG, default is False (INFO)
SERVER_PORT:       Set server port, default is 6123
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
      - DEBUG=False
      - SERVER_PORT=6123
    volumes:
      - /ssl/ssl.key:/ssl/ssl.key:ro
      - /ssl/ssl.pem:/ssl/ssl.pem:ro


```

## SSL Support
To enable SSL support (HTTPS), 
fill in the environment variables `SSL_KEY` and `SSL_CERTIFICATE`,
Use the volume to share the SSL key and certificate with the container.  

## Web Server
#### GET / or /index.html
Presents the web page of Z-Wave network viewer

#### GET /data/nodes.json
Retrieves network viewer formatted nodes as JSON for debug 

## Troubleshooting
Before posting issue, please collect as much information as you can for faster resolving,
Use browser console to identify the error,
Use the JSON button at the right upper corner to open the debug node's JSON in new window,
post that JSON as part of the reported issue for faster debugging.   

Container generates debug volume with all JSONs and log files,
When there is an issue, it will be much easier to reproduce the errors using those files

## Changelog:

#### 2020-11-12

- Better HA disconnection handling

#### 2020-11-06

- Fix web-socket connection without certificate

#### 2020-10-31 #2

- Check if identifier is numeric (Instance ID)

#### 2020-10-31 #1

- Better error handling
- Added error line for all logs related to exceptions
- Handle WebSocket state changes to reconnect when needed
- Skip WebSocket SSL verification 
   

#### 2020-10-23

- WebServer changed to Flask
- Added support to change the port using environment variable `SERVER_PORT`
- Added support to change the default log level from INFO to DEBUG using environment variable `DEBUG`
- Added support to read data from `/debug` volume instead of HA (for debugging purposes) using environment variable `LOCAL`
- Continuous connection using WebSocket to HA for future support in WebSocket to the UI
