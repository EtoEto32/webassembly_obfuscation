"""Verify the offline browser environment, without loading mining code."""
import http.server
import json
import socket
import subprocess
import threading
from selenium import webdriver
from selenium.webdriver.chrome.service import Service


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        content=b'<html><body><div id="status">local-only</div></body></html>'
        self.send_response(200)
        self.send_header('Content-Length',str(len(content)))
        self.end_headers()
        self.wfile.write(content)
    def log_message(self,*args): pass


def main():
    route=open('/proc/net/route').read().splitlines()[1:]
    assert not any(r.split()[1]=='00000000' for r in route),'Unexpected default route'
    interfaces=socket.if_nameindex()
    assert all(name=='lo' for _,name in interfaces),interfaces
    denied=False
    try:
        # Reserved documentation address; network-none means no packet can leave.
        with socket.create_connection(('192.0.2.1',443),timeout=1): pass
    except OSError: denied=True
    assert denied,'Outbound network unexpectedly available'
    server=http.server.ThreadingHTTPServer(('127.0.0.1',7676),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    options=webdriver.ChromeOptions()
    options.binary_location='/usr/bin/chromium'
    for arg in ['--headless=new','--no-sandbox','--disable-dev-shm-usage',
                '--disable-background-networking','--disable-component-update',
                '--disable-sync','--no-first-run','--disable-extensions']:
        options.add_argument(arg)
    driver=webdriver.Chrome(service=Service('/usr/bin/chromedriver'),options=options)
    try:
        driver.get('http://127.0.0.1:7676')
        assert driver.find_element('id','status').text=='local-only'
        print(json.dumps(dict(status='passed',test='local browser and network isolation only; no Wasm benchmark',
            interfaces=interfaces,outbound_blocked=denied,
            browser_version=driver.capabilities['browserVersion'],
            driver_version=driver.capabilities.get('chrome',{}).get('chromedriverVersion'),
            selenium_version=__import__('selenium').__version__,
            node_version=subprocess.check_output(['node','--version'],text=True).strip())))
    finally:
        driver.quit();server.shutdown()


if __name__=='__main__':main()
