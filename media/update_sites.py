#!/usr/bin/env python3
import os
import pathlib
import sys
import subprocess
import lib
import csv
import itertools
import shutil


def find_any_confdir() -> pathlib.Path | None:
    for site in lib.read_site_configs():
        if os.path.isdir(site.config_dir):
            return site.config_dir
    return None


if __name__ == '__main__':
    first_confdir = find_any_confdir()
    if first_confdir is None:
        print("ERROR: no existing config dir found.", file=sys.stderr)
    else:
        print(f"INFO: using {first_confdir} as config dir to get the drive ids")
        updated_sites: list[lib.SiteConfig] = []
        new_sites: list[lib.SiteConfig] = []
        removed_sites: list[lib.SiteConfig] = []
        unchanged_sites: list[lib.SiteConfig] = []

        for site in lib.read_site_configs():
            updated = lib.get_sharepoint_config(first_confdir, site.site_name, site.library_name)
            if updated is None:
                removed_sites.append(site)
            elif updated != site:
                updated_sites.append(updated)
            else:
                unchanged_sites.append(updated)

        with open(lib.get_site_names_csv_path()) as sfile:
            reader = csv.reader(sfile, delimiter=";")
            for site_name, library_name in reader:
                already_existing = False
                for s in updated_sites + new_sites + unchanged_sites:
                    if s.site_name == site_name and s.library_name == library_name:
                        already_existing = True
                        break
                if not already_existing:
                    config = lib.get_sharepoint_config(first_confdir, site_name, library_name)
                    if config:
                        new_sites.append(config)

        accessible_site_names = lib.get_accessible_site_names(first_confdir)

        console_width = shutil.get_terminal_size((80, 20)).columns
        print("=" * console_width)

        sites_to_write = updated_sites + new_sites + unchanged_sites

        duplicate_sites: list[lib.SiteConfig] = []
        sites_grouped = itertools.groupby(sites_to_write, key=lambda s: (s.site_name, s.library_name))
        sites_to_write_without_duplicates: list[lib.SiteConfig] = []
        for _, same_sites in sites_grouped:
            same_sites = list(same_sites)
            sites_to_write_without_duplicates.append(same_sites[0])
            duplicate_sites.extend(same_sites[1:])

        sites_to_write = sites_to_write_without_duplicates
        sites_to_write.sort(key=lambda s: (s.site_name, s.library_name))

        named_lists = [["Unchanged", unchanged_sites],
                       ["Removed", removed_sites],
                       ["Duplicate", duplicate_sites],
                       ["Updated", updated_sites],
                       ["New", new_sites],
                       ]
        for lname, li in named_lists:
            if len(li) > 0:
                print("INFO:", lname, "sites:")
                for site in li:
                    print("\t" + str(site))

        if accessible_site_names is not None:
            missing = set(accessible_site_names)
            for site in sites_to_write:
                try:
                    missing.remove(site.site_name)
                except KeyError:
                    pass
            if len(missing) > 0:
                print("INFO: the following sites would be accessible, but are not in the configured site list:")
                for m in missing:
                    print("\t" + m)

        print("=" * console_width)

        lib.write_site_configs(sites_to_write)
        print(f"INFO: wrote {len(sites_to_write)} site configs to {lib.get_sites_csv_path()}")
