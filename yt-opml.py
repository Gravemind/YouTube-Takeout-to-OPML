#!/usr/bin/env python3
import argparse
import json
import csv
from xml.etree import ElementTree as et

def main():
    parser = argparse.ArgumentParser(
        description="yt-opml.py takes Google's Takeout JSON or CSV for YouTube and converts it to an OPML file. The goal is to facilitate importing the OPML file into an RSS feed reader."
    )
    parser.add_argument(
        "--name",
        type=str,
        help="Name of the folder in OPML output file."
    )
    parser.add_argument(
        "input",
        type=str,
        help="The JSON or CSV file provided by Google."
    )
    parser.add_argument(
        "output",
        type=argparse.FileType("wb"),
        help="The OPML file to be imported into an RSS feed reader."
    )
    args = parser.parse_args()

    input_name = args.input.lower()
    if input_name.endswith(".json"):
        with open(args.input, "rb") as takeout:
            # YouTube's Takeout contains a subscriptions.json file. It's located at
            # "./Takeout/YouTube and YouTube Music/subscriptions/subscriptions.json"
            # The JSON file doesn't have a specification that I can find. It is a
            # list of subscriptions. The parts that are relevant to creating the
            # OPML file are
            #   {
            #     "snippet": {
            #       "title",
            #       "description",
            #       "resourceId": {
            #         "channelId"
            #       }
            #     }
            #   }
            #
            data = json.load(takeout)
            subscriptions = [
                (
                    sub["snippet"]["resourceId"]["channelId"],
                    sub["snippet"]["title"],
                    sub["snippet"]["description"],
                )
                for sub in data
            ]
    elif input_name.endswith(".csv"):
        with open(args.input, "r") as takeout:
            # takout CSV file header:
            #   Channel Id,Channel Url,Channel Title
            table = csv.reader(takeout)
            table = list(table)
            if not table or table[0][:3] != ["Channel Id", "Channel Url", "Channel Title"]:
                raise ValueError("unrecognized csv column names")
            table = table[1:]
            subscriptions = [
                (
                    row[0],  # channel_id
                    row[2],  # title
                    "",  # description
                )
                for row in table
                if row
            ]
    else:
        raise ValueError(f"unsupported file format {args.input.name!r}")

    # Initialize the OPML Element
    opml = et.Element("opml", version="2.0")
    head = et.SubElement(opml, "head")
    et.SubElement(head, "title").text = "Google Takeout"
    body = et.SubElement(opml, "body")
    youtube = et.SubElement(body, "outline",
        title=args.name or "YouTube Subscriptions",
        text=args.name or "YouTube Subscriptions",
        type="folder"
    )

    for (channel_id, title, description) in subscriptions:
        # This command maps the elements from the JSON file to their
        # corresponding attributes in the <outline> element of an OPML file.
        et.SubElement(youtube, "outline",
            title=title,
            text=title,
            description=description,
            type="rss",
            # This is the RSS feed for the channel.
            xmlUrl=f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}",
            # This is the channel's homepage.
            htmlUrl=f"https://www.youtube.com/channel/{channel_id}"
        )

    # Serialize the OPML Element to the output file
    tree = et.ElementTree(opml)
    tree.write(args.output,
        encoding="UTF-8",
        xml_declaration=True
    )

if __name__ == "__main__":
    main()
