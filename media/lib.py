#!/usr/bin/env python3

import dataclasses
import pathlib
from typing import Iterable
import csv
import subprocess
import re
import select
import sys
import os

ERROR_MESSAGE_REAUTH_NEEDED = "ERROR: You will need to issue a --reauth"
ERROR_MESSAGE_SITE_NOT_FOUND = "ERROR: The requested SharePoint site could not be found."


@dataclasses.dataclass
class SiteConfig(object):
    site_name: str
    library_name: str
    drive_id: str
    url: str

    @property
    def _dir_name(self) -> str:
        return f"{self.site_name}_{self.library_name}"

    @property
    def config_dir(self) -> pathlib.Path:
        return get_config_dir_path() / self._dir_name

    @property
    def sync_dir(self) -> pathlib.Path:
        return get_current_data_dir_path() / self._dir_name


def get_root_dir_path() -> pathlib.Path:
    return pathlib.Path(__file__).parent


def get_config_dir_path() -> pathlib.Path:
    return get_root_dir_path() / "config"


def get_current_data_dir_path() -> pathlib.Path:
    return get_root_dir_path() / "data_current"


def get_sites_csv_path() -> pathlib.Path:
    return get_root_dir_path() / "sites.csv"


def get_site_names_csv_path() -> pathlib.Path:
    return get_root_dir_path() / "site_names.csv"


def get_config_template_path() -> pathlib.Path:
    return get_config_dir_path() / "template"


def read_site_configs() -> Iterable[SiteConfig]:
    with open(get_sites_csv_path()) as sfile:
        reader = csv.reader(sfile, delimiter=";")
        for site_name, library_name, drive_id, url, *_ in reader:
            yield SiteConfig(site_name, library_name, drive_id, url)


def write_site_configs(configs: Iterable[SiteConfig]) -> None:
    with open(get_sites_csv_path(), "w") as sfile:
        writer = csv.writer(sfile, delimiter=";")
        for cnf in configs:
            writer.writerow([cnf.site_name, cnf.library_name, cnf.drive_id, cnf.url])


def call_onedrive_impl(args: list[str]) -> tuple[str, str]:
    all_args = ["onedrive"] + args
    print("DEBUG: calling ", *all_args)
    p = subprocess.Popen(all_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p_streams = [p.stdout, p.stderr]
    sys_streams = [sys.stdout, sys.stderr]

    for ps in p_streams:
        os.set_blocking(ps.fileno(), False)

    captured_output = [bytearray() for _ in p_streams]

    while True:
        reads = [ps.fileno() for ps in p_streams]
        ret = select.select(reads, [], [])

        end = False

        for fd in ret[0]:
            for ps, sys_s, cap in zip(p_streams, sys_streams, captured_output):
                if fd == ps.fileno():
                    buffer = bytearray()
                    try:
                        while True:
                            read = os.read(ps.fileno(), 1)
                            if len(read) > 0:
                                buffer.extend(read)
                            else:
                                break
                    except BlockingIOError as e:
                        pass
                    decoded = buffer.decode("utf-8", "replace")
                    if len(buffer) > 0:
                        sys_s.write(decoded)
                        sys_s.flush()
                        cap.extend(buffer)
                    else:
                        end = True
                    break

        if (end or len(ret[0]) == 0) and p.poll() != None:
            break

    return tuple(cap.decode("utf-8", "replace") for cap in captured_output)


def extract_confdir_from_args(args: list[str]) -> pathlib.Path | None:
    for i in range(len(args)):
        if args[i] == "--confdir" and i + 1 < len(args):
            return pathlib.Path(args[i + 1])
    return None


def call_onedrive(args: list[str], auto_reauth=True) -> tuple[str, str]:
    stdout, stderr = call_onedrive_impl(args)
    if auto_reauth and (ERROR_MESSAGE_REAUTH_NEEDED in stdout or ERROR_MESSAGE_REAUTH_NEEDED in stderr):
        confdir = extract_confdir_from_args(args)
        confdir_args = ["--confdir", confdir] if confdir is not None else []
        print("INFO: automatically calling onedrive --reauth")
        call_onedrive_impl(confdir_args + ["--reauth"])
        # subprocess.run(["onedrive"]+confdir_args+["--reauth"], stdout=sys.stdout, stderr=sys.stderr, stdin=sys.stdin)
        stdout, stderr = call_onedrive_impl(args)
    return stdout, stderr


def get_sharepoint_config(config_dir: pathlib.Path, site_name: str, library_name: str) -> SiteConfig | None:
    stdout, stderr = call_onedrive(["--confdir", str(config_dir.absolute()), "--get-sharepoint-drive-id", site_name])

    if ERROR_MESSAGE_SITE_NOT_FOUND in stdout or ERROR_MESSAGE_SITE_NOT_FOUND in stderr:
        return None

    pattern = re.compile(
        r"^Site Name:\W*(.*)\W*$\W+Library Name:\W*(.*)\W*$\W+drive_id:\W*(.*)\W*$\W+Library URL:\W*(.*)\W*$",
        re.MULTILINE)

    print(f"DEBUG: searching output ({len(stdout)}) for drive_id and library URL...")
    for match in pattern.finditer(stdout):
        m_site_name = match.group(1)
        m_library_name = match.group(2)
        m_drive_id = match.group(3)
        m_libray_url = match.group(4)

        print("DEBUG: match", m_site_name, m_library_name, m_drive_id, m_libray_url)

        if m_site_name == site_name and m_library_name == library_name:
            return SiteConfig(m_site_name, m_library_name, m_drive_id, m_libray_url)
    return None


def get_accessible_site_names(config_dir: pathlib.Path) -> list[str] | None:
    stdout, stderr = call_onedrive(["--confdir", str(config_dir.absolute()),
                                    "--get-sharepoint-drive-id", "hopefully-not-existing-sitename-423897324234"])

    if ERROR_MESSAGE_SITE_NOT_FOUND not in stdout and ERROR_MESSAGE_SITE_NOT_FOUND not in stderr:
        return None

    msg = "The following SharePoint site names were returned:"
    msg_start = stdout.index(msg)
    last_end = msg_start + len(msg)
    names: list[str] = []
    while True:
        try:
            star_index = stdout.index("*", last_end)
        except ValueError:
            break
        try:
            endl_index = stdout.index("\n", star_index)
        except ValueError:
            endl_index = None
        names.append(stdout[star_index + 1:endl_index].strip())
        if endl_index is None:
            break
        else:
            last_end = endl_index

    return names
