#!/usr/bin/env python3
import csv
import os
import shutil
from sys import stdout

import lib

MESSAGE_RESYNC_REQUIRED = "An application configuration change has been detected where a --resync is required"

if __name__ == '__main__':
    for site in lib.read_site_configs():
        args = ["--confdir", site.config_dir, "--sync", "--download-only", "--cleanup-local-files"]
        stdout, stderr = lib.call_onedrive(args)
        if MESSAGE_RESYNC_REQUIRED in stdout or MESSAGE_RESYNC_REQUIRED in stderr:
            print("INFO: onedrive client says resync is required, retrying with --resync")
            lib.call_onedrive(args + ["--resync"])
