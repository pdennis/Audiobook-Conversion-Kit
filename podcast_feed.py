import os
import time
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom

def create_podcast_feed(audiobooks_dir='.', feed_title="Local Audiobooks", feed_description="Locally generated audiobooks"):
    """Create an RSS feed for locally generated audiobooks"""
    # Create the RSS feed structure
    rss = ET.Element("rss", version="2.0")
    rss.set("xmlns:itunes", "http://www.itunes.com/dtds/podcast-1.0.dtd")
    rss.set("xmlns:content", "http://purl.org/rss/1.0/modules/content/")
    rss.set("xmlns:atom", "http://www.w3.org/2005/Atom")

    channel = ET.SubElement(rss, "channel")
    
    # Basic feed information
    ET.SubElement(channel, "title").text = feed_title
    ET.SubElement(channel, "link").text = "https://pats-mac-studio.alpaca-turtle.ts.net"
    ET.SubElement(channel, "language").text = "en-us"
    ET.SubElement(channel, "itunes:author").text = "Audiobook Conversion Kit"
    ET.SubElement(channel, "description").text = feed_description
    ET.SubElement(channel, "itunes:summary").text = feed_description
    ET.SubElement(channel, "lastBuildDate").text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
    
    # Add self-reference link (recommended for podcast feeds)
    atom_link = ET.SubElement(channel, "atom:link")
    atom_link.set("href", "https://pats-mac-studio.alpaca-turtle.ts.net/feed")
    atom_link.set("rel", "self")
    atom_link.set("type", "application/rss+xml")
    
    # Find all audiobook files
    audiobook_files = []
    for file in Path(audiobooks_dir).glob("*_audiobook.mp3"):
        audiobook_files.append(file)
    
    # Sort by modification time, newest first
    audiobook_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    # Add items (episodes) to the feed
    for file in audiobook_files:
        # Get file stats
        stats = os.stat(file)
        file_size = stats.st_size
        mod_time = stats.st_mtime
        
        # Format date in RSS format
        pub_date = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime(mod_time))
        
        # Create episode title from filename
        title = file.stem.replace("_audiobook", "")
        
        # Add item to feed
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = title
        ET.SubElement(item, "itunes:title").text = title
        ET.SubElement(item, "pubDate").text = pub_date
        
        # Enclosure is the audio file
        enclosure = ET.SubElement(item, "enclosure")
        enclosure.set("url", f"https://pats-mac-studio.alpaca-turtle.ts.net/audio/{file.name}")
        enclosure.set("length", str(file_size))
        enclosure.set("type", "audio/mpeg")
        
        # Add a guid (unique identifier)
        ET.SubElement(item, "guid", isPermaLink="false").text = f"{file.name}_{mod_time}"
        
        # Add optional podcast-specific metadata
        ET.SubElement(item, "itunes:explicit").text = "false"
        
        # Add duration if we can calculate it (approximately 1MB per 1 minute for MP3)
        duration_minutes = file_size // (1024 * 1024)
        duration_seconds = (file_size % (1024 * 1024)) // (17 * 1024)  # Rough estimate
        ET.SubElement(item, "itunes:duration").text = f"{duration_minutes:02d}:{duration_seconds:02d}:00"
    
    # Format the XML with nice indentation
    rough_string = ET.tostring(rss, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    # Write to file
    feed_path = Path(audiobooks_dir) / "podcast.xml"
    with open(feed_path, "w", encoding="utf-8") as f:
        f.write(pretty_xml)
    
    return feed_path

def update_feed_after_audiobook(audiobook_path):
    """Update the podcast feed after a new audiobook is created"""
    dir_path = Path(audiobook_path).parent
    return create_podcast_feed(dir_path)

if __name__ == "__main__":
    feed_path = create_podcast_feed()
    print(f"Podcast feed created: {feed_path}")