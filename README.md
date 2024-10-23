# Notion Help Center

## Description

Simple CLI Tool for Notion Help
Uses Notion's Help Articles as Context

## Attached Files

I've attached two example files to display the output
`notion_content.json` contains the urls as keys and a list of chunked lines as values
`enriched_content.json` is a list of chunks of 750 characters maximum for all the information retrieved from the help pages

## Implementation

- Start at the help page
- Find all links in the help page which have help in the route
- Use Beautiful Soup to find all text components, ignore all media for the current page
- Recursively go to all help pages and perform the same
- Stop at a specified max depth
- Chunk retrieved information to to a maximum of 750 characters
- Send the chunks to openAI to make them human readable

## How to Run

create a .env file which will contain

```
OPENAI_API_KEY=
```

then run

```
source local-env
```

to set the environment var

install requirements

```
pip install -r requirements.txt
```

finally, to kick off the program

```
python main.py
```
