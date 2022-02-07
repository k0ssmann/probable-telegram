# OPAL Scraper

## What is this?

OPAL Scraper (OS) is a tool for automated scraping of OPAL repositories and downloading videos from Video Campus Sachsen (VCS). OS searches the given repositories for any videos hosted on VCS. Note that automated access to your university portal, OPAL or Video Campus Sachsen is illegal thus use this program at your own risk :)

OS currently supports only access via TU Chemnitz.

## Prerequisites

- Python >= 3.7
- BeautifulSoup 4
- ffmpeg

## Usage

Install the prerequisites and clone the repository

`git clone https://github.com/k0ssmann/probable-telegram`

OS can be used via a command line interface. To see available commands and their usage type

`./opal-scraper.py -h`

## Getting started

Before scraping OPAL and downloading lectures you need to set up your credentials for your university portal. To do this, simply type

`./opal-scraper.py --user USERNAME PASSWORD`

and fill in your respective username and password for your university portal. A json file is created where your username is stored, however, the password is safely stored in your systemy keyring.

Next, we want to make sure that the service provider doesn't know from the user agent that we are a bot. To do this, visit https://www.whatismybrowser.com/de/detect/what-is-my-user-agent

and copy the user agent. Then type

`./opal-scraper.py --uagent "UAGENT"`

and replace UAGENT with the user agent you copied before. Now you're ready to add repositories to scrape. To add a repository type

`./opal-scraper.py --add LABEL REPO` 

in the command line, where REPO is the link to the repository. For example: `./opal-scraper.py --add MSeko-01 https://bildungsportal.sachsen.de/opal/auth/RepositoryEntry/31665192962`.

Next, you want to update the available contents to download by typing 

`./opal-scraper.py --update`

and OS will now start scraping the repositories you've added before. When this is done simply type

`./opal-scraper.py --download` 

to start downloading videos from VCS. OS downloads the transport streams of the videos which are stored in directories like LABEL/tmp_SHAREKEY. Sharekeys are unique identifiers of videos uploaded to VCS. When the downloads are finished, all you've to do is to convert the transport streams to a playable video file by typing

`./opal-scraper.py --convert`

## TODO

- Refactoring of classes
- Error handling
- Add support for TUC cloud?
