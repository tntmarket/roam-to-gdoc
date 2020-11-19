#!/usr/bin/env python3
import argparse
import os
import sys
import tempfile
import time
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

from roam_to_gdoc.zip import unzip_and_save_json_archive
from roam_to_gdoc.scrape import patch_pyppeteer, scrape, Config


@logger.catch(reraise=True)
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", default=None, nargs="?",
                        help="Directory of your notes are stored. Default to notes/")
    parser.add_argument("--debug", action="store_true",
                        help="Help debug by opening the browser in the foreground. Note that the "
                             "git repository will not be updated with that option.")
    parser.add_argument("--database", default=None,
                        help="If you have multiple Roam databases, select the one you want to save."
                             "Can also be configured with env variable ROAMRESEARCH_DATABASE.")
    parser.add_argument("--sleep-duration", type=float, default=2.,
                        help="Duration to wait for the interface. We wait 100x that duration for"
                             "Roam to load. Increase it if Roam servers are slow, but be careful"
                             "with the free tier of Github Actions.")
    args = parser.parse_args()

    patch_pyppeteer()
    path = Path().absolute()

    if (path / ".env").exists():
        logger.info("Loading secrets from {}", path / ".env")
        load_dotenv(path / ".env", override=True)
    else:
        logger.debug("No secret found at {}", path / ".env")
    if "ROAMRESEARCH_USER" not in os.environ or "ROAMRESEARCH_PASSWORD" not in os.environ:
        logger.error("Please define ROAMRESEARCH_USER and ROAMRESEARCH_PASSWORD, "
                     "in the .env file of your notes repository, or in environment variables")
        sys.exit(1)
    config = Config(args.database, debug=args.debug, sleep_duration=float(args.sleep_duration))

    with tempfile.TemporaryDirectory() as json_zip_path:
        json_zip_path = Path(json_zip_path)

        scrape(json_zip_path, config)
        if config.debug:
            logger.debug("waiting for the download...")
            time.sleep(20)
            return
        unzip_and_save_json_archive(json_zip_path, path / "tmp")


if __name__ == "__main__":
    main()
