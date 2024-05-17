# Copyright (C) 2024 Microsoft Corporation. All rights reserved.
#
# Author: Ahmed Messaoud <ahmed.messaoud@microsoft.com>
#
# This file is part of cloud-init. See LICENSE file for license information.

"""osconfig enables various management sources at first boot"""

import logging
from textwrap import dedent

from cloudinit import util, subp
from cloudinit.cloud import Cloud
from cloudinit.atomic_helper import write_json
from cloudinit.config import Config
from cloudinit.config.schema import MetaSchema, get_meta_doc
from cloudinit.distros import ALL_DISTROS
from cloudinit.settings import PER_INSTANCE

# The schema definition for each cloud-config module is a strict contract for
# describing supported configuration parameters for each cloud-config section.
# It allows cloud-config to validate and alert users to invalid or ignored
# configuration options before actually attempting to deploy with said
# configuration.

OSCONFIG_CONFIGURATION_FILEPATH = "/etc/osconfig/osconfig.json"
MODULE_DESCRIPTION = """\
Configure and install osconfig based on your management authority.

ex.
 - GitOps
 - Local Management / RD/DC
 - IotHub
"""

meta: MetaSchema = {
    "id": "cc_osconfig",
    "name": "OSConfig",
    "title": "Configure osconfig for instance",
    "description": MODULE_DESCRIPTION,
    "distros": [ALL_DISTROS],
    "frequency": PER_INSTANCE,
    "examples": [
        dedent(
            """\
        osconfig:
            local_management: 1"""
        ),
        dedent(
            """\
        osconfig:
            git_management: 1
            git_repository_url: https://github.com/Azure/azure-osconfig
            git_branch: name/branch"""
        ),
        dedent(
            """\
        osconfig:
            command_logging: 1
            full_logging: 1"""
        ),
    ],
    "activate_by_schema_keys": ["osconfig"],
}

__doc__ = get_meta_doc(meta)
LOG = logging.getLogger(__name__)

def update_config(distro, config):
    distro.manage_service("stop", "osconfig")
    # util.write_file(OSCONFIG_CONFIGURATION_FILEPATH, config)
    write_json(OSCONFIG_CONFIGURATION_FILEPATH, config)
    distro.manage_service("start", "osconfig")

def handle(name: str, cfg: Config, cloud: Cloud, args: list) -> None:
    if "osconfig" not in cfg:
        LOG.info("Skipping module named %s, no 'osconfig' key in configuration", name)
        return
    
    ############# Define configuration points #########################
    osconfig_cfg: dict = cfg.get("osconfig", {})

    # Local RC/DC
    osconfig_localManagement_cfg = osconfig_cfg.get("local_management")
    
    # GitOps
    osconfig_gitManagement_cfg = osconfig_cfg.get("git_management")
    osconfig_gitRepositoryUrl_cfg = osconfig_cfg.get("git_repository_url")
    osconfig_gitBranch_cfg = osconfig_cfg.get("git_branch")
    
    # Debugging
    osconfig_debugCommandLogging_cfg = osconfig_cfg.get("debug_command_logging")
    osconfig_debugFullLogging_cfg = osconfig_cfg.get("debug_full_logging")
    ##################################################################

    # Install osconfig if not already installed
    if not subp.which("osconfig"):
        cloud.distro.install_packages(["osconfig"])

    # Load the current OSConfig configuration
    mycfg =  util.load_json(util.load_text_file(OSCONFIG_CONFIGURATION_FILEPATH))

    # Mutually-exclusive configurations
    if osconfig_localManagement_cfg:
        mycfg['LocalManagement'] = osconfig_localManagement_cfg
    elif osconfig_gitManagement_cfg:
        mycfg['GitMananagement'] = osconfig_gitManagement_cfg
        mycfg['GitRepositoryUrl'] = osconfig_gitRepositoryUrl_cfg
        mycfg['GitBranch'] = osconfig_gitBranch_cfg

    if osconfig_debugCommandLogging_cfg:
        mycfg['CommandLogging'] = osconfig_debugCommandLogging_cfg

    if osconfig_debugFullLogging_cfg:
        mycfg['FullLogging'] = osconfig_debugFullLogging_cfg

    update_config(cloud.distro, mycfg)
