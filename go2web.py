#!/usr/bin/env python3
import sys
import socket
import ssl
import hashlib
import os
import time
from urllib.parse import urlparse, quote_plus, urljoin
from bs4 import BeautifulSoup

CACHE_DIR = ".go2web_cache"

def get_cache_path(url):
    """
    Generates a unique filename for the URL cache.
    """
    url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    return os.path.join(CACHE_DIR, url_hash)

def make_http_request(url, max_redirects=5):
    """
    Core function to make raw HTTP request using sockets.
    Returns the response body as string, or None on error.
    Handles redirects and caching.
    """
    if max_redirects < 0:
        print("Error: Too many redirects.")
        return None

    # Ensure URL starts with http:// or https:// if scheme is missing
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "http://" + url

    # Clean URL for caching (ignore fragments)
    parsed_url = urlparse(url)
    clean_url = parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path
    if parsed_url.query:
        clean_url += "?" + parsed_url.query

    cache_path = get_cache_path(clean_url)
    
    # Check cache (valid for 60 seconds for simplicity in this lab)
    if os.path.exists(cache_path):
        current_time = time.time()
        file_mod_time = os.path.getmtime(cache_path)
        if current_time - file_mod_time < 60:
            print(f"DEBUG: Serving from cache: {url}")
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                print(f"DEBUG: Cache read error: {e}")

    scheme = parsed_url.scheme
    host = parsed_url.hostname
    port = parsed_url.port
    path = parsed_url.path
    if not path:
        path = "/"
    if parsed_url.query:
        path += "?" + parsed_url.query

    if not port:
        port = 443 if scheme == "https" else 80

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        if scheme == "https":
            context = ssl.create_default_context()
            sock = context.wrap_socket(sock, server_hostname=host)
            
        sock.connect((host, port))
        
        # User-Agent header is often required for search engines
        request = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            f"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36\r\n"
            f"Connection: close\r\n\r\n"
        )
        sock.sendall(request.encode())
        
        response = b""
        while True:
            data = sock.recv(4096)
            if not data:
                break
            response += data
            
        sock.close()
        
        # Decode and split headers/body
        try:
            response_text = response.decode('utf-8', errors='ignore')
        except:
             response_text = response.decode('latin-1', errors='ignore')

        parts = response_text.split("\r\n\r\n", 1)
        headers_section = parts[0]
        body = parts[1] if len(parts) > 1 else ""
        
        headers_lines = headers_section.split("\r\n")
        status_line = headers_lines[0]
        
        # simplistic status parsing "HTTP/1.1 200 OK"
        try:
            status_code = int(status_line.split(" ")[1])
        except IndexError:
            # Handle cases where response is empty or malformed
             print("Error: Malformed response")
             return None
            
        if 300 <= status_code < 400:
            # Handle Redirect
            location = None
            for line in headers_lines[1:]:
                if line.lower().startswith("location:"):
                    location = line.split(":", 1)[1].strip()
                    break
            
            if location:
                # Handle relative redirect
                new_url = urljoin(url, location)
                print(f"Redirecting to: {new_url}")
                return make_http_request(new_url, max_redirects - 1)
            else:
                 print("Error: Redirect status without Location header.")
                 return None

        # Save to cache
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                f.write(body)
        except Exception as e:
            print(f"DEBUG: Cache write error: {e}")

        return body

    except Exception as e:
        print(f"Error making request: {e}")
        return None

def handle_url(url):
    body = make_http_request(url)
    if not body:
        return

    soup = BeautifulSoup(body, 'html.parser')
    for script in soup(["script", "style"]):
        script.extract()
            
    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = '\n'.join(chunk for chunk in chunks if chunk)
    print(text)

def handle_search(term):
    print(f"Searching for: {term}")
    search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(term)}"
    
    body = make_http_request(search_url)
    if not body:
        return

    soup = BeautifulSoup(body, 'html.parser')
    results = []
    
    # DuckDuckGo HTML structure:
    # Results are usually in div with class 'links_main' -> a class 'result__a'
    
    for link_tag in soup.find_all('a', class_='result__a'):
        title = link_tag.get_text(strip=True)
        link = link_tag.get('href')
        
        if link:
             results.append((title, link))
        
        if len(results) >= 10:
            break

    if not results:
        print("No results found. DuckDuckGo might have blocked the request or changed structure.")
        # Fallback to try generic anchor search if specific class fails
        if not results:
             for a in soup.find_all('a'):
                 href = a.get('href')
                 if href and href.startswith('http') and 'duckduckgo' not in href:
                     title = a.get_text(strip=True)
                     if title:
                        results.append((title, href))
                 if len(results) >= 10:
                     break
    
    if results:
        for i, (title, link) in enumerate(results, 1):
            print(f"{i}. {title}")
            print(f"   Link: {link}\n")

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
        handle_url(sys.argv[2])
    elif command == '-s':
        if len(sys.argv) < 3:
            print("Error: Missing search term for -s")
            return
        search_term = " ".join(sys.argv[2:])
        handle_search(search_term)
    else:
        print(f"Error: Unknown argument '{command}'")
        print_help()

if __name__ == "__main__":
    main()
