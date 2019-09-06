# Copyright (c) Nicholas Hylands
# I wrote the code, but feel free to use this anywhere without any reference to any license or anything whatsoever.

from os.path import expanduser
import urllib
import urllib2
from bs4 import BeautifulSoup
import htmlentitydefs
import re
import os
import multiprocessing
import sys
import ez_epub
import time
import shutil
import ConfigParser

#storyInfo Index
#0 = chapter count
#1 = story name

#Config stuff
Config = ConfigParser.ConfigParser()
Config.read("config.ini")

home = expanduser("~")

FFDirUnderHome = Config.getboolean("Main", "FanfictionDirectoryUnderHome")
FFDirUnderHome = True
if FFDirUnderHome:
    FanfictionFolder = home + Config.get("Main", "FanfictionDirectory")
else:
    FanfictionFolder = Config.get("Main", "FanfictionDirectoryIfNotUnderHome")
    
if not os.path.exists(FanfictionFolder):
        os.makedirs(FanfictionFolder)
        
headers = { 'User-Agent' : 'Mozilla/5.0' }

#for use in Main function when spawning threads.
def round_down(num, divisor):
    return num - (num%divisor)

#title is actually the chapter number
#storyDir is actually the title of the story
def WriteChapterText(myText, title, storyDir):
    if not os.path.exists(storyDir + "/"):
        os.makedirs(storyDir + "/")
    target = open(storyDir + "/chapter" + title + ".html", 'w')
    target.truncate()
    target.write(myText.encode('ascii'))
    target.close()
    #print "Printed chapter: " + title

#this will let us grab the chapter text for a story.
def GrabStoryTextFromPage(StoryID, chapterNum):
    #chapterPage = urllib2.urlopen("http://www.fanfiction.net/s/" + StoryID + "/" + chapterNum);
    #chap_web_pg = chapterPage.read();
    mSoup = BeautifulSoup(GetRawPageText(StoryID, chapterNum))
    result = mSoup.find(id='storytext')
    return result

def GetRawPageText(StoryID, chapterNum):
    
    urlToGrab = "https://www.fanfiction.net/s/" + StoryID + "/" + str(chapterNum)
    req = urllib2.Request(urlToGrab, None, headers)
    chapterPage = urllib2.urlopen(req)
    chap_web_pg = chapterPage.read();
    return chap_web_pg
    
def GetStoryInfo(StoryID):
    chapterPage = urllib2.urlopen("https://www.fanfiction.net/s/" + StoryID + "/1")
    web_pg = chapterPage.read()
    cCount = re.search('- Chapters: (.*) - Words:', web_pg)
     
    #print "Chapter Count: " + cCount.group(1)
    cTitle = re.search("<b class='xcontrast_txt'>" + "(.*)" + "</b>", web_pg)
    storyInfo = []
    if cCount is None:
        storyInfo.append(1)
    else:
        storyInfo.append(int(cCount.group(1)))
    storyInfo.append(cTitle.group(1))
    return storyInfo

#Our main function for threading.
def chapterGrabber(storyID, chapterStart, chapterEnd, storyTitle, num_chapters, result_queue, oneChapter=False):
    if not oneChapter:
        for i in range(chapterStart,chapterEnd+1):
            mSoup = BeautifulSoup(GetRawPageText(storyID, i))
            result = mSoup.find(id='storytext')
            output = "Writing Chapter: " + str(i)
            result_queue.put(output)
            WriteChapterText(result, str(i), FanfictionFolder + "epub files " + storyTitle + "/OEBPS")
        if chapterEnd == num_chapters:
            result_queue.put("done!",True)
    else:
        mSoup = BeautifulSoup(GetRawPageText(storyID, 1))
        result = mSoup.find(id='storytext')
        output = "Writing Chapter: " + str(1)
        result_queue.put(output)
        WriteChapterText(result, str(1), FanfictionFolder + "epub files " + storyTitle + "/OEBPS")
        result_queue.put("done!",True)

def parseHtmlFiles(storyTitle,numChapters):
    results = []
    for i in range(1,numChapters+1):
        section = ez_epub.Section()
        section.title = "chapter" + str(i)
        target = open( FanfictionFolder + "epub files " + storyTitle + "/OEBPS/chapter" + str(i) + ".html", 'r')
        text = target.read()
        #text = "hello"
        section.text.append(text)
        results.append(section)
    return results
    
def main():
    import timing
    
    arg_names = ['storyID','chunk size']

    book = ez_epub.Book()

    #eventually use story URL, with some way of parsing it. For now, we're just gonna grab the ID.
    mainStoryID = "7474227"
    globalChunkSize = 5

    if len(sys.argv) > 1:
        if len(sys.argv[1]) == 7 or len(sys.argv[1]) == 8:
            mainStoryID = sys.argv[1]
        elif sys.argv[1] == "help":
            print """
            run with args:
            [story ID] [|chunk size]
            chunk-size is the amount of chapters you want each thread to handle.
            smaller chunks is faster, but there is a limit.
            default is five.
            """
            sys.exit()
        else:
            print """
            run with args:
            [story ID] [|chunk size]
            chunk-size is the amount of chapters you want each thread to handle.
            smaller chunks is faster, but there is a limit.
            default is five.
            0 is impossible.
            """
            sys.exit()
        if len(sys.argv) > 2:
            if sys.argv[2] is not 0:
                globalChunkSize = sys.argv[2]
            else:
                print "cannot divide by zer0"
                sys.exit()
    else:
        print "run with command 'help' for help"
        sys.exit()

    filename = "storydir/story.html"
    
    storyID = mainStoryID
    storyInfo = GetStoryInfo(storyID)
    print storyInfo
    chunkSize = int(globalChunkSize)
    numChapters = storyInfo[0]
    storyTitle = storyInfo[1]
    
    #setup our book...
    print "Title: " + storyTitle
    book.title = storyTitle
    book.authors = ["Extracted by Nyxeka"]
    numChaptersToGet = range(1,numChapters+1)
    #get our first set of chunks, these will be extracted <chunkSize> at a time.
    firstChunks = round_down(numChapters,chunkSize)
    #these will be the remaining chapters to pull.
    lastChunk = numChapters - firstChunks
    processs = []
    result_queue = multiprocessing.Queue()
    if numChapters > 1:
        if firstChunks > 0:
            for i in range(1,firstChunks/chunkSize+1):
                process = multiprocessing.Process(target=chapterGrabber, args = [storyID,((i*chunkSize)-chunkSize)+1,i*chunkSize,storyTitle,firstChunks,result_queue])
                print "Starting thread... " + str(i)
                process.start()
                #processs.append(process)
        process = multiprocessing.Process(target=chapterGrabber, args = [storyID,firstChunks+1,firstChunks+lastChunk,storyTitle,firstChunks,result_queue])
        print "Starting thread for last chunk"
        process.start()
    else:
        process = multiprocessing.Process(target=chapterGrabber, args = [storyID,firstChunks+1,firstChunks+lastChunk,storyTitle,firstChunks,result_queue, True])
        print "Starting thread for last chunk"
        process.start()
        
    while 1:
        string = result_queue.get()
        print string
        if string == "done!":
            break
    print "waiting so that we can actually see the files... this is broken sometimes so we wait"
    time.sleep(0.5)
    print "preparing epub file..."
    book.sections = parseHtmlFiles(storyTitle,numChapters)
    print "making epub file..."
    book.make(FanfictionFolder + storyTitle)
    
    print "deleting old files..."
    for root, dirs, files in os.walk(FanfictionFolder + "epub files " + storyTitle, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(FanfictionFolder + "epub files " + storyTitle)
    for root, dirs, files in os.walk(FanfictionFolder + storyTitle, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(FanfictionFolder + storyTitle)
    print "success!"

if __name__ == '__main__':
    main()
