#!/usr/bin/env python3
import csv
import os
import shutil
import lib

if __name__ == '__main__':
    with open(lib.get_config_template_path()) as tfile:
        template = tfile.read()

    used_paths = set()
    for site in lib.read_site_configs():
        if not os.path.isdir(site.config_dir):
            os.mkdir(site.config_dir)
        config = template.replace("###SYNC_DIR###", str(site.sync_dir.absolute())).replace("###ID###", site.drive_id).replace("###URL###", site.url)
        config_file_path = site.config_dir / "config"
        if config_file_path.exists():
            print(f"INFO: updating {config_file_path}")
        else:
            print(f"INFO: creating {config_file_path}")
        with open(config_file_path, "w") as cfile:
            cfile.write(config)
        used_paths.add(site.config_dir.absolute())

    for config_dir in lib.get_config_dir_path().iterdir():
        if config_dir.is_dir() and config_dir.absolute() not in used_paths:
            shutil.rmtree(config_dir)
            print(f"INFO: deleting {config_dir}")
