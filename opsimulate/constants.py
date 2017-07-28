#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 James Wen

import os

HOME = os.path.expanduser("~")
OPSIMULATE_HOME = os.path.join(HOME, '.opsimulate')

KEYS_DIR_NAME = os.path.join(OPSIMULATE_HOME, 'keys')
PRIVATE_KEY_FILE = os.path.join(KEYS_DIR_NAME, 'opsimulate')
PUBLIC_KEY_FILE = os.path.join(KEYS_DIR_NAME, 'opsimulate.pub')

SAVED_SELECTED_MODULE_PATH = os.path.join(OPSIMULATE_HOME,
                                          'selected_module.txt')

HINT_HISTORY_FILE = os.path.join(OPSIMULATE_HOME, 'hint-history.yml')

MODULE_START_SCRIPT = 'initiate'
MODULE_CHECK_SCRIPT = 'check'
MODULE_RESOLVE_SCRIPT = 'resolve'
MODULE_METADATA = 'metadata.yml'

ACCEPTED_METADATA_KEYS = ['author', 'hints', 'description', 'introduction',
                          'solution']
REQUIRED_MODULE_SCRIPTS = [MODULE_START_SCRIPT, MODULE_CHECK_SCRIPT,
                           MODULE_RESOLVE_SCRIPT]
REQUIRED_MODULE_FILES = REQUIRED_MODULE_SCRIPTS + [MODULE_METADATA]

SERVICE_ACCOUNT_FILE = os.path.join(OPSIMULATE_HOME, 'service-account.json')

ZONE = 'us-east4-a'
MACHINE_TYPE = 'n1-standard-1'
UBUNTU_VERSION = 'ubuntu-1404-lts'
INSTANCE_NAME = 'opsimulate-gitlab'
VM_USERNAME = 'opsimulate'
GITLAB_TAG = 'gitlab'
HTTP_ACCESS_FIREWALL_RULE = 'gitlab-http-access'

GITLAB_READY_LOG_MESSAGE = 'INFO Finished running startup scripts'
GITLAB_LOG = '/var/log/syslog'
