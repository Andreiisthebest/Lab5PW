#!/usr/bin/env python3
import sys

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
        print(f"Making HTTP request to {url} (Not implemented yet)")
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
