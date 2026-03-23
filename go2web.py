#!/usr/bin/env python3
import sys
import socket
import ssl
from urllib.parse import urlparse
from bs4 import BeautifulSoup

def make_request(url):
    # Ensure URL starts with http:// or https:// if scheme is missing
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "http://" + url
        
    parsed_url = urlparse(url)
    scheme = parsed_url.scheme
    host = parsed_url.hostname
    port = parsed_url.port
    path = parsed_url.path
    if not path:
        path = "/"
    if parsed_url.query:
        path += "?" + parsed_url.query

    if not port:
        if scheme == "https":
            port = 443
        else:
            port = 80

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        if scheme == "https":
            context = ssl.create_default_context()
            sock = context.wrap_socket(sock, server_hostname=host)
            
        sock.connect((host, port))
        
        request = f"GET {path} HTTP/1.0\r\nHost: {host}\r\n\r\n"
        sock.sendall(request.encode())
        
        response = b""
        while True:
            data = sock.recv(4096)
            if not data:
                break
            response += data
            
        sock.close()
        
        # Decode response
        try:
            response_text = response.decode('utf-8')
        except UnicodeDecodeError:
             response_text = response.decode('latin-1')

        # Separate headers and body
        parts = response_text.split("\r\n\r\n", 1)
        if len(parts) > 1:
            body = parts[1]
        else:
            body = parts[0]
            
        soup = BeautifulSoup(body, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
            
        text = soup.get_text()
        
        # Break into lines and remove leading/trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        print(text)

    except Exception as e:
        print(f"Error: {e}")

def print_help():
        print(f"Error: {e}")

def print_help():
    help_text = """go2web - Simple CLI for making HTTP requests

Usage:
    go2web -u <URL>         # make an HTTP request to the specified URL and print the response
    go2web -s <search-term> # make an HTTP request to search the term using your favorite search engine and print top 10 results
    go2web -h               # show this help
"""
    print(help_text)

def main():
    if len(sys.argv) < 2:
        print_help()
        return

    command = sys.argv[1]

    if command == '-h':
        print_help()
    elif command == '-u':
        if len(sys.argv) < 3:
            print("Error: Missing URL argument for -u")
            return
        url = sys.argv[2]
        make_request(url)
    elif command == '-s':
        if len(sys.argv) < 3:
            print("Error: Missing search term for -s")
            return
        search_term = " ".join(sys.argv[2:])
        print(f"Searching for: {search_term} (Not implemented yet)")
    else:
        print(f"Error: Unknown argument '{command}'")
        print_help()

if __name__ == "__main__":
    main()
