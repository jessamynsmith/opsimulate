#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 James Wen

import os
import shutil
from subprocess import call

import click
import googleapiclient

import opsimulate.constants as constants
import opsimulate.helpers as helpers


@click.group()
def cli():
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = \
        constants.SERVICE_ACCOUNT_FILE


@cli.command('setup')
def setup():
    # Ensure OPSIMULATE home directory exists
    if not os.path.isdir(constants.OPSIMULATE_HOME):
        print("Generating opsimulate home directory at {}"
              .format(constants.OPSIMULATE_HOME))
        os.mkdir(constants.OPSIMULATE_HOME)


@cli.command('load_credentials')
@click.argument('credential_path', type=click.Path(exists=True))
def load_credentials(credential_path):
    helpers.validate_opsimulate_home_present()
    if os.path.isabs(credential_path):
        abs_credential_path = credential_path
    else:
        current_dir = os.getcwd()
        abs_credential_path = os.path.join(current_dir, credential_path)
    shutil.copyfile(abs_credential_path, constants.SERVICE_ACCOUNT_FILE)

    print("Copying GCP credentials into opsimulate home directory as: {}"
          .format(constants.SERVICE_ACCOUNT_FILE))


@cli.command('clean')
def clean():
    helpers.validate_credentials_loaded()
    helpers.clear_hint_history()

    # Destroy created Gitlab VM
    print("Attempting to tear down Gitlab VM")
    compute = helpers.get_gce_client()
    project = helpers.get_service_account_info().get('project_id')

    try:
        compute.instances().delete(
            project=project,
            zone=constants.ZONE,
            instance=constants.INSTANCE_NAME).execute()
    except googleapiclient.errors.HttpError as e:
        if e.resp.status == 404:
            print("Teardown of Gitlab VM instance '{}' unneeded because VM "
                  "does not exist".format(constants.INSTANCE_NAME))
        else:
            raise(e)
    else:
        print("Tore down Gitlab VM")

    try:
        compute.firewalls().delete(
            project=project,
            firewall=constants.PUBLIC_ACCESS_FIREWALL_RULE).execute()
    except googleapiclient.errors.HttpError as e:
        if e.resp.status == 404:
            print("Teardown of Gitlab public access unneeded because "
                  "appropriate firewall rule '{}' does not exist"
                  .format(constants.PUBLIC_ACCESS_FIREWALL_RULE))
        else:
            raise(e)
    else:
        print("Tore down Gitlab public access firewall rule")

    # Clean local machine of generated artifacts
    if os.path.isdir(constants.OPSIMULATE_HOME):
        print('Removing {} directory'.format(constants.OPSIMULATE_HOME))
        shutil.rmtree(constants.OPSIMULATE_HOME)


@cli.command('connect')
def connect():
    helpers.validate_opsimulate_home_present()
    helpers.validate_credentials_loaded()
    helpers.validate_vm_running()
    vm_instance_info = helpers.running_vm_instance()
    ip_address = vm_instance_info.get('networkInterfaces')[0] \
        .get('accessConfigs')[0].get('natIP')

    ssh_command = "ssh -i {} -o 'StrictHostKeyChecking no' {}@{}".format(
        constants.PRIVATE_KEY_FILE, constants.VM_USERNAME, ip_address)
    print("To connect to your running VM instance, execute the "
          "following command:")
    print(ssh_command)


@cli.command('deploy')
def deploy():
    helpers.validate_opsimulate_home_present()
    helpers.validate_credentials_loaded()
    # Setup student interface to server by setting up SSH + keys
    helpers.generate_ssh_key()
    # Use GCE API client and Gitlab debian package to deploy and setup
    helpers.create_gce_vm()
    helpers.enable_network_access_gitlab()


@cli.command('module_select')
@click.argument('module_path', type=click.Path(exists=True))
def module_select(module_path):
    helpers.validate_opsimulate_home_present()

    if os.path.isabs(module_path):
        abs_module_path = module_path
    else:
        current_dir = os.getcwd()
        abs_module_path = os.path.join(current_dir, module_path)

    helpers.validate_module_contents(abs_module_path)
    helpers.validate_module_scripts_executable(abs_module_path)
    helpers.validate_module_metadata(abs_module_path)
    helpers.clear_hint_history()

    with open(constants.SAVED_SELECTED_MODULE_PATH, 'w') as f:
        f.write(abs_module_path)
    print('Saved path of selected module to {}'.format(
        constants.SAVED_SELECTED_MODULE_PATH))


@cli.command('module_start')
def module_start():
    helpers.validate_opsimulate_home_present()
    helpers.validate_credentials_loaded()
    helpers.validate_module_selected()
    helpers.validate_vm_running()
    helpers.clear_hint_history()

    print("Initiating module problem")

    ip_address = helpers.running_vm_ip_address()
    module_start_script = helpers.file_from_selected_module(
        constants.MODULE_START_SCRIPT)

    module_start_command = \
        "ssh -i {} -o 'StrictHostKeyChecking no' {}@{} 'bash -s' < {}".format(
            constants.PRIVATE_KEY_FILE, constants.VM_USERNAME, ip_address,
            module_start_script)

    if call(module_start_command, shell=True) == 0:
        print("Initiated module problem")
    else:
        print("Initiating module problem failed")


@cli.command('module_hint')
@click.option('--seen', '-s', is_flag=True, default=False)
def module_hint(seen):
    helpers.validate_opsimulate_home_present()
    helpers.validate_module_selected()

    if seen:
        # Print all seen hints
        print("Here's all the hints you've seen so far:")
        hints = helpers.get_seen_hints()
        for hint in hints:
            print(hint)
    else:
        print("Here's a hint:")
        hint = helpers.get_new_hint()
        print(hint)


@cli.command('module_check')
def module_check():
    helpers.validate_opsimulate_home_present()
    helpers.validate_credentials_loaded()
    helpers.validate_module_selected()
    helpers.validate_vm_running()

    print('Checking if module problem has been fixed...')

    ip_address = helpers.running_vm_ip_address()
    module_check_script = helpers.file_from_selected_module(
        constants.MODULE_CHECK_SCRIPT)

    module_check_command = \
        "ssh -i {} -o 'StrictHostKeyChecking no' {}@{} 'bash -s' < {}".format(
            constants.PRIVATE_KEY_FILE, constants.VM_USERNAME, ip_address,
            module_check_script)

    if call(module_check_command, shell=True) == 0:
        print("Module problem has been fixed. Great job!")
    else:
        print("Module problem is still an issue. Keep trying, you got this!")


@cli.command('module_resolve')
def module_resolve():
    helpers.validate_opsimulate_home_present()
    helpers.validate_credentials_loaded()
    helpers.validate_module_selected()
    helpers.validate_vm_running()
    helpers.clear_hint_history()

    print('Resolving module problem...')

    ip_address = helpers.running_vm_ip_address()
    module_resolve_script = helpers.file_from_selected_module(
        constants.MODULE_RESOLVE_SCRIPT)

    module_resolve_command = \
        "ssh -i {} -o 'StrictHostKeyChecking no' {}@{} 'bash -s' < {}".format(
            constants.PRIVATE_KEY_FILE, constants.VM_USERNAME, ip_address,
            module_resolve_script)

    if call(module_resolve_command, shell=True) == 0:
        print("Module problem has been resolved.")
    else:
        print("Cannot resolve module problem")
        print("The module problem might have been already resolved")
        print("Run 'opsimulate module_check' to see if the problem "
              "is still active")


@cli.command('status')
def status():
    print('Opsimulate Status')
    if os.path.isfile(constants.SAVED_SELECTED_MODULE_PATH):
        with open(constants.SAVED_SELECTED_MODULE_PATH, 'r') as f:
            selected_module_path = f.read().strip()
        if not selected_module_path:
            selected_module_path_message = 'No module selected'
        else:
            selected_module_path_message = selected_module_path
    else:
        selected_module_path_message = 'No module selected'
    print('Selected Module: {}'.format(selected_module_path_message))

    if os.path.isfile(constants.SERVICE_ACCOUNT_FILE):
        service_account_credentials_message = constants.SERVICE_ACCOUNT_FILE
    else:
        service_account_credentials_message = \
            'No GCP service account credentials present'
    print('GCP SA Credentials: {}'.format(service_account_credentials_message))
