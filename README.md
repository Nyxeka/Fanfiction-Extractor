Fanfiction-Extractor
====================

Multi-threaded fanfiction extractor written in python

This script was designed to download fanfiction stories from fanfiction.net, and then convert the downloaded text into an epub file. 
epub is rather easy to make, being just a .zip file with a bunch of html files inside, one html file per chapter.

Main: r2p.py

Run with: python r2p.py [story-id] [|chunk-size]

example: python r2p.py 1234567

example 2: python r2p.py 1234567 4

chunk size decides how many chapters each thread will handle. This defaults to 5, which means a story with 100 chapters will spawn 20 threads.

story id: ffnetURL.net/s/1234567

DISCLAIMER:
ez_epub is Copyright (c) 2012, Bin Tan
All rights reserved.
