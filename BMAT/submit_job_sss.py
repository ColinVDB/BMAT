#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 16 10:58:44 2024

@author: colin
"""
import asyncio
import asyncssh
import contextvars
import functools
import paramiko
import threading
import os
from os.path import join as pjoin
from os.path import exists as pexists
import sys
import subprocess
# import time
import json


class PathMappingError(Exception):
    """Custom exception class"""
    def __init__(self, message):
        super().__init__(message)
        
        
class ServerInfoError(Exception):
    """Custom exception class"""
    def __init__(self, message):
        super().__init__(message)
        
        
class JobInfoError(Exception):
    """Custom exception class"""
    def __init__(self, message):
        super().__init__(message)
        

class JobSubmissionError(Exception):
    """Custom exception class"""
    def __init__(self, message):
        super().__init__(message)
        
        
class ServerConnectionError(Exception):
    """Custom exception class"""
    def __init__(self, message):
        super().__init__(message)
        
def get_session_list(bids, subj, ses_details, check_if_exist=True):
    """Helper function to get the list of sessions for a given subject."""
    sess = []
    if ses_details == 'all':
        for d in os.listdir(pjoin(bids, f'sub-{subj}')):
            if d.startswith('ses-'):
                sess.append(d.split('-')[1])
    else:
        for s in ses_details.split(','):
            if '-' in s:
                s0, s1 = map(int, s.split('-'))
                for si in range(s0, s1 + 1):
                    si_str = str(si).zfill(2)
                    if check_if_exist:
                        if os.path.isdir(pjoin(bids, f'sub-{subj}', f'ses-{si_str}')):
                            sess.append(si_str)
                    else:
                        sess.append(si_str)
                        
            else:
                if check_if_exist:
                    if os.path.isdir(pjoin(bids, f'sub-{subj}', f'ses-{s}')):
                        sess.append(s)
                else:
                    sess.append(s)
    return sess

def process_subject_range(bids, sub_range, ses_details, check_if_exist=True):
    """Helper function to process a range of subjects."""
    subjects_and_sessions = []
    sub0, sub1 = map(int, sub_range.split('-'))
    for subi in range(sub0, sub1 + 1):
        subi_str = str(subi).zfill(3)
        if not os.path.isdir(pjoin(bids, f'sub-{subi_str}')) and check_if_exist:
            continue
        sess = get_session_list(bids, subi_str, ses_details, check_if_exist=check_if_exist)
        subjects_and_sessions.append((subi_str, sess))
    return subjects_and_sessions

def find_subjects_and_sessions(bids, sub, ses, check_if_exist=True):
    
    subjects_and_sessions = []

    if sub == 'all':
        # Process all subjects
        for dirs in os.listdir(bids):
            if dirs.startswith('sub-'):
                subj = dirs.split('-')[1]
                sess = get_session_list(bids, subj, ses)
                subjects_and_sessions.append((subj, sess))
    else:
        # Process specified subjects
        for sub_item in sub.split(','):
            if '-' in sub_item:
                subjects_and_sessions.extend(process_subject_range(bids, sub_item, ses, check_if_exist=check_if_exist))
            else:
                if not os.path.isdir(pjoin(bids, f'sub-{sub_item}')) and check_if_exist:
                    print('bruh')
                    continue
                sess = get_session_list(bids, sub_item, ses, check_if_exist=check_if_exist)
                subjects_and_sessions.append((sub_item, sess))
    
    return sorted(subjects_and_sessions)


def is_subpath(main_path, sub_path):
    main_path = os.path.abspath(main_path)
    sub_path = os.path.abspath(sub_path)
    try:
        common_path = os.path.commonpath([main_path, sub_path])
        return common_path == sub_path
    except ValueError:
        return False


def map_path(bids_path, shared_folders):
    
    for shared_folder in shared_folders.keys():
        if is_subpath(bids_path, shared_folder):
            return pjoin(shared_folders[shared_folder], os.path.relpath(bids_path, shared_folder)).replace('\\','/')
    
    return None

def generate_shell_script(sbatch_command, output_file):
    # Extract SBATCH parameters
    sbatch_parameters = [f'#SBATCH {param}' for param in sbatch_command.split('\n') if param.startswith('--')]

    # Extract the command to execute (the --wrap option)
    command_to_execute = [param for param in sbatch_command.split('\n') if not param.startswith('--')]

    # Write SBATCH parameters and command to execute to shell script file
    with open(output_file, 'w') as f:
        f.write('#!/bin/bash' + '\n' + '\n')
        for param in sbatch_parameters:
            f.write(param + '\n')
        f.write('\n')  # Add a newline between SBATCH parameters and command
        for cmd in command_to_execute:
            f.write(cmd + '\n' + '\n')
            
            
def get_server_info():
    
    bmat_path = os.path.dirname(os.path.abspath(__file__))
    
    server_info = None
    with open(pjoin(bmat_path, 'server_info.json'), 'r') as f:
        server_info = json.load(f)
        
    if server_info == None:
        print('[ERROR] while loading server_info.json file')
    
    return server_info



def get_job_info(job_json):
    
    job_info = None
    with open(job_json, 'r') as f:
        job_info = json.load(f)
        
    if job_info == None:
        print('[ERROR] while loading job_info.json file')
    
    return job_info


def sbatch_command(bids, sub, ses, job_info, args=[], one_job=False):
    # print(f'{job_info=}')
    # print(f'{args=}')
        
    # add error and output in job_info
    slurm_infos = job_info["slurm_infos"]
    if one_job:
        slurm_infos["output"] = pjoin(job_info["log"], f"slurm-%j_{slurm_infos['job-name']}_one_job.out")
        slurm_infos["error"] = pjoin(job_info["log"], f"slurm-%j_{slurm_infos['job-name']}_one_job.err")
    else:
        slurm_infos["output"] = pjoin(job_info["log"], f"slurm-%j_{slurm_infos['job-name']}_sub-{sub}_ses-{ses}.out")
        slurm_infos["error"] = pjoin(job_info["log"], f"slurm-%j_{slurm_infos['job-name']}_sub-{sub}_ses-{ses}.err")
    
    # Create sbatch command
    sbatch_cmd = "sbatch "
    
    # add slurm_infos 
    for key, value in zip(slurm_infos.keys(), slurm_infos.values()):
        sbatch_cmd = sbatch_cmd + "--%s=%s " % (key, value)
    
    sbatch_cmd = ' '.join(sbatch_cmd.split())
    
    # create wrap_cmd 
    wrap_cmd = 'bash -l -c \'module purge ; '
    # adding modules to load
    wrap_modules = job_info["modules"]
    wrap_cmd = wrap_cmd + f"module load {' '.join(wrap_modules)} ; "
    venv = ""
    if job_info["venv"] != None:
        venv = job_info["venv"]
    if venv != "" or venv != None:
        wrap_cmd = wrap_cmd + f"source {venv} ; "
    # adding actual cmd
    job_arg = []
    for key, value in zip(job_info['args'].keys(), job_info['args'].values()):
        job_arg.append(key)
        job_arg.append(value)
    cmd = f"python3 {job_info['python_script']} {bids} {sub} {ses} {' '.join(args)} {' '.join(job_arg)}"
    cmd = ' '.join(cmd.split())
    
    wrap_cmd = wrap_cmd + cmd + " \'"
    
    # print('create wrap_cmd')
    # wrap_cmd = f'\"bash -l -c \'module purge ; module load {' '.join(wrap_modules)} ; source {venv} \'\"'
    
    sbatch_cmd = sbatch_cmd + " --wrap=\\\"" + wrap_cmd + "\\\""
    # sbatch_cmd = ' '.join(sbatch_cmd.split())
    # sbatch_cmd = sbatch_cmd.replace('\"', '\\\"')
    return sbatch_cmd


def submit_job(bids_path, sub, ses, job_json, args=[], use_asyncssh=True, passphrase=None, one_job=False, check_if_exist=True):
    
    print('submit_job')
    
    server_info = get_server_info()
    if server_info == None:
        raise ServerInfoError("Problems when reading the Server Info file")
    
    server_bids_path = map_path(bids_path, server_info['shared_folders'])
    if server_bids_path == None:
        raise PathMappingError("Problems when mapping the local Shared folder path to the remote server path")
    
    if isinstance(job_json, dict):
        job_info = job_json
    elif isinstance(job_json, str):
        job_info = get_job_info(job_json)
        if job_info == None:
            raise JobInfoError("Problems when reading the Job Info file")
    else:
        raise JobInfoError("Problems when reading the Job Info file")
                
    # check if arg is a loca path and map if needed 
    # !!! Attention: Not Optimal !!!
    args_path = []
    for arg in args:
        if pexists(arg):
            arg_map = map_path(arg, server_info['shared_folders'])
            args_path.append(arg_map)
        else:
            args_path.append(arg)
    args = args_path
    
    if one_job:
        subjects_and_sessions = (sub, ses)
    else:
        subjects_and_sessions = find_subjects_and_sessions(bids_path, sub, ses, check_if_exist=check_if_exist)
    # print(subjects_and_sessions)
                
    # Try the connection
    try:
        if use_asyncssh:
            jobs_submitted = asyncio.run(asyncssh_submit_job(server_bids_path, subjects_and_sessions, server_info, job_info, args, passphrase=passphrase, one_job=one_job))
            
        else:
            jobs_submitted = asyncio.run(paramiko_submit_job(server_bids_path, subjects_and_sessions, server_info, job_info, args))
            
        return jobs_submitted
    
    except JobSubmissionError as e:
        print(f'JobSubmissionError: {e}')
        raise JobSubmissionError(e)
    except Exception as e:
        print('Exception')
        raise ServerConnectionError(f"Server Connection error: {e}")
        
        
        
def submit_job_compose(bids_path, sub, ses, job_json, args=[], use_asyncssh=True, passphrase=None, one_job=False, check_if_exist=True):
    
    print('submit_job compose')
    
    server_info = get_server_info()
    if server_info == None:
        raise ServerInfoError("Problems when reading the Server Info file")
    
    server_bids_path = map_path(bids_path, server_info['shared_folders'])
    if server_bids_path == None:
        raise PathMappingError("Problems when mapping the local Shared folder path to the remote server path")
    
    if isinstance(job_json, list):
        job_info = job_json
    elif isinstance(job_json, str):
        job_info = get_job_info(job_json)
        if job_info == None:
            raise JobInfoError("Problems when reading the Job Info file")
    else:
        raise JobInfoError("Problems when reading the Job Info file")
                
    # check if arg is a loca path and map if needed 
    # !!! Attention: Not Optimal !!!
    args_path = []
    for arg_l in args:
        arg_l_path = []
        for arg in arg_l:
            if pexists(arg):
                arg_map = map_path(arg, server_info['shared_folders'])
                arg_l_path.append(arg_map)
            else:
                arg_l_path.append(arg)
        args_path.append(arg_l_path)
    args = args_path
    
    if one_job:
        subjects_and_sessions = (sub, ses)
    else:
        subjects_and_sessions = find_subjects_and_sessions(bids_path, sub, ses, check_if_exist=check_if_exist)
    # print(subjects_and_sessions)
                
    # Try the connection
    try:
        if use_asyncssh:
            jobs_submitted = asyncio.run(asyncssh_submit_job_compose(server_bids_path, subjects_and_sessions, server_info, job_info, args, passphrase=passphrase, one_job=one_job))
            
        else:
            return []
            # jobs_submitted = asyncio.run(paramiko_submit_job(server_bids_path, subjects_and_sessions, server_info, job_info, args))
            
        return jobs_submitted
    
    except JobSubmissionError as e:
        print(f'JobSubmissionError: {e}')
        raise JobSubmissionError(e)
    except Exception as e:
        print('Exception')
        raise ServerConnectionError(f"Server Connection error: {e}")



async def connect_to_ssh(host, username, key_path, passphrase=None):
    try:
        # Connect to SSH server asynchronously
        ssh = await asyncssh.connect(host, username=username, client_keys=[key_path], passphrase=passphrase)
        print(f"Connected to {host}")
        return ssh
    except asyncssh.Error as e:
        print(f"SSH connection error: {e}")
        return None
    
    
async def run_ssh_command(ssh, command):
    try:
        # Run command on the connected SSH server
        result = await ssh.run(command)
        return result
    except asyncssh.Error as e:
        print(f"Command execution error: {e}")
        return None


async def asyncssh_submit_job(server_bids_path, subjects_and_sessions, server_info, job_info, args=[], passphrase=None, one_job=False):

    # SSH connection setup
    # Connect to SSH server
    ssh = await connect_to_ssh(server_info["server"]["host"], server_info["server"]["user"], server_info["server"]["key"], passphrase=passphrase)
    if not ssh:
        raise ServerConnectionError("Problem during connection to the server")
    
    job_submitted = []
    if one_job:
        print('one job')
        sub = subjects_and_sessions[0]
        ses = subjects_and_sessions[1]
        print(sub, ses)
        try:
            # print('try')
            sbatch_cmd = sbatch_command(server_bids_path, sub, ses, job_info, args=args, one_job=one_job)
            
            print(sbatch_cmd)
            
            # Run command on SSH server
            result = await run_ssh_command(ssh, f'bash -l -c \"{sbatch_cmd}\"')
            output = result.stdout
            error = result.stderr
            print(output)
            print(error)
            
            job_submitted.append(output)
            
        except Exception as e:
            # close connection
            print(f'except {e}')
            ssh.close()
            await ssh.wait_closed()
            print('connection closed ')
            return job_submitted
            raise JobSubmissionError(f"Error {e} while submiting a job")
        
        # close connection
        ssh.close()
        await ssh.wait_closed()
        print('connection closed ')
        
    else:
        print(subjects_and_sessions)
        for sub, sess in subjects_and_sessions:
            for ses in sess:
                print(sub, ses)
                
                try:
                    sbatch_cmd = sbatch_command(server_bids_path, sub, ses, job_info, args=args, one_job=one_job)
                    
                    print(sbatch_cmd)
                    
                    # Run command on SSH server
                    result = await run_ssh_command(ssh, f'bash -l -c \"{sbatch_cmd}\"')
                    output = result.stdout
                    error = result.stderr
                    print(output)
                    print(error)
                    
                    job_submitted.append(output)
                    
                except Exception as e:
                    # close connection
                    print(f'except {e}')
                    ssh.close()
                    await ssh.wait_closed()
                    print('connection closed ')
                    return job_submitted
                    raise JobSubmissionError(f"Error {e} while submiting a job")
                
        # close connection
        ssh.close()
        await ssh.wait_closed()
        print('connection closed ')        
    return job_submitted



async def asyncssh_submit_job_compose(server_bids_path, subjects_and_sessions, server_info, job_info, args=[], passphrase=None, one_job=False):
    print('async_submit_job_compose')
    # SSH connection setup
    # Connect to SSH server
    ssh = await connect_to_ssh(server_info["server"]["host"], server_info["server"]["user"], server_info["server"]["key"], passphrase=passphrase)
    if not ssh:
        raise ServerConnectionError("Problem during connection to the server")
        
    if type(job_info) != list:
        raise TypeError("job_info is not a list")
        
    if len(job_info) != len(args):
        print(f'{job_info=}')
        print(f'{args=}')
        raise IndexError("job_info list not the same size as args list")
    
    job_submitted = []
    if one_job:
        print('one job')
        sub = subjects_and_sessions[0]
        ses = subjects_and_sessions[1]
        print(sub, ses)
        try:
            last_job_id = None
            for i in range(len(job_info)):
                
                if last_job_id != None:
                    print(f'compose with last job_id: {last_job_id}')
                    job_info[i]["slurm_infos"]["dependency"] = f'afterok:{last_job_id}'
                
                # print('try')
                sbatch_cmd = sbatch_command(server_bids_path, sub, ses, job_info[i], args=args[i], one_job=one_job)
                
                print(sbatch_cmd)
                
                # Run command on SSH server
                result = await run_ssh_command(ssh, f'bash -l -c \"{sbatch_cmd}\"')
                output = result.stdout
                error = result.stderr
                print(output)
                print(error)
                
                if output is not None and output != []:
                    if type(output) is list:
                        job = output[0]
                    else:
                        job = output
                
                last_job_id = job.split(' ')[-1].replace('\n', '')
                
                job_submitted.append(output)
            
        except Exception as e:
            # close connection
            print(f'except {e}')
            ssh.close()
            await ssh.wait_closed()
            print('connection closed ')
            return job_submitted
            raise JobSubmissionError(f"Error {e} while submiting a job")
        
        # close connection
        ssh.close()
        await ssh.wait_closed()
        print('connection closed ')
        
    else:
        print(subjects_and_sessions)
        for sub, sess in subjects_and_sessions:
            for ses in sess:
                print(sub, ses)
                
                try:
                    last_job_id = None
                    for i in range(len(job_info)):
                        
                        if last_job_id != None:
                            print(f'compose with last job_id: {last_job_id}')
                            job_info[i]["slurm_infos"]["dependency"] = f'afterok:{last_job_id}'
                            
                        sbatch_cmd = sbatch_command(server_bids_path, sub, ses, job_info[i], args=args[i], one_job=one_job)
                        
                        print(sbatch_cmd)
                        
                        # Run command on SSH server
                        result = await run_ssh_command(ssh, f'bash -l -c \"{sbatch_cmd}\"')
                        output = result.stdout
                        error = result.stderr
                        print(output)
                        print(error)
                        
                        if output is not None and output != []:
                            if type(output) is list:
                                job = output[0]
                            else:
                                job = output
                        
                        last_job_id = job.split(' ')[-1].replace('\n', '')
                        
                        job_submitted.append(output)
                    
                except Exception as e:
                    # close connection
                    print(f'except {e}')
                    ssh.close()
                    await ssh.wait_closed()
                    print('connection closed ')
                    return job_submitted
                    raise JobSubmissionError(f"Error {e} while submiting a job")
                
        # close connection
        ssh.close()
        await ssh.wait_closed()
        print('connection closed ')        
    return job_submitted



async def paramiko_submit_job(server_bids_path, subjects_and_sessions, server_info, job_info, args=[]):
    
    # Server Connection
    ssh = await paramiko_connect_ssh(server_info)
    if not ssh:
        raise ServerConnectionError("Problem during connection to the server")
    
    # ssh = asyncio.to_thread(paramiko_connect_ssh, server_info)
    # await ssh
    # print('paramiko instance')
    # # SSH connection setup
    # ssh = paramiko.SSHClient()
    # ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # ret = to_thread(paramiko_connect_ssh, ssh, server_info)
    # if ret == None:
    #     raise ServerConnectionError('Error connection')
    
    job_submitted = []
    for sub, sess in subjects_and_sessions:
        for ses in sess:
            print(sub, ses)
            
            try:
                sbatch_cmd = sbatch_command(server_bids_path, sub, ses, job_info, args=args)
                
                print(sbatch_cmd)
                
                # stdin, stdout, stderr = await loop.run_in_executor(None, lambda: ssh.exec_command(f'bash -l -c \"{sbatch_cmd} \"'))
                stdin, stdout, stderr = await paramiko_run_ssh_command(ssh, f'bash -l -c \"{sbatch_cmd} \"')
                output = stdout.read().decode()
                error = stderr.read().decode()
                print(output)
                print(error)
                
                job_submitted.append(output)
                
            except Exception as e:
                raise JobSubmissionError(f"Error {e} while submiting a job")
    
    # close connection
    ssh.close()
    print('connection closed ')
    return job_submitted                
    
    
def old_paramiko_submit_job(bids_path, sub, ses, job_json, args=[]):
        
    server_info = get_server_info()
    if server_info == None:
        raise ServerInfoError("Problems when reading the Server Info file")
    
    server_bids_path = map_path(bids_path, server_info['shared_folders'])
    if server_bids_path == None:
        raise PathMappingError("Problems when mapping the local Shared folder path to the remote server path")
    
    if isinstance(job_json, dict):
        job_info = job_json
    elif isinstance(job_json, str):
        job_info = get_job_info(job_json)
        if job_info == None:
            raise JobInfoError("Problems when reading the Job Info file")
    else:
        raise JobInfoError("Problems when reading the Job Info file")
        
    print('get info checked')
        
    # check if arg is a loca path and map if needed 
    # !!! Attention: Not Optimal !!!
    print(args)
    args_path = []
    for arg in args:
        if pexists(arg):
            arg_map = map_path(arg, server_info['shared_folders'])
            args_path.append(arg_map)
        else:
            args_path.append(arg)
    args = args_path
    print(args)
    
    
    print('try server connection')
    
    # Server Connection
    try:
        print('paramiko instance')
        # SSH connection setup
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        
        
        # # loop = asyncio.get_event_loop()
        # # Connect to the remote cluster
        # # Connect to SSH server asynchronously
        # # await loop.run_in_thread(None, lambda: ssh.connect(server_info["server"]["host"], username=server_info["server"]["user"], key_filename=server_info["server"]["key"]))
        
        # ssh.connect(server_info["server"]["host"], username=server_info["server"]["user"], key_filename=server_info["server"]["key"])
        # print('ssh connected')
        
        # connection_result = connect_ssh(server_info)
        # if isinstance(connection_result, paramiko.SSHClient):
        #     ssh = connection_result
        # else:
        #     raise connection_result  # Propagate connection error
        
        ssh_thread = threading.Thread(target=connect_ssh, args=(ssh, server_info))
        ssh_thread.start()
        
        # Wait for SSH connection to complete
        ssh_thread.join()
        
        # submit jobs 
        # for all subjects and sess
        subjects_and_sessions = []
        
        if sub == 'all':
            for dirs in os.listdir(bids_path):
                if 'sub-' in dirs:
                    subj = dirs.split('-')[1]
                    sess = []
                    if ses == 'all':
                        for d in os.listdir(pjoin(bids_path, f'sub-{subj}')):
                            if 'ses-' in d:
                                s = d.split('-')[1]
                                sess.append(s)
                    else:
                        ses_details = ses.split(',')
                        for s in ses_details:
                            if os.path.isdir(pjoin(bids_path, f'sub-{subj}', f'ses-{s}')):
                                sess.append(s)
                    subjects_and_sessions.append((subj, sess))
            
        else:
        
            sub_details = sub.split(',')
            ses_details = ses.split(',')
            
            for sub in sub_details:
                sess = []
                for ses in ses_details:
                    sess.append(ses)
                subjects_and_sessions.append((sub, sess))
                
        subjects_and_sessions = sorted(subjects_and_sessions)
                
        job_submitted = []
        
        # shell = ssh.invoke_shell()
        # print('shell invoked')
        
        # while True:
        #     if shell.recv_ready():
        #         shell_env = shell.recv(4096).decode()  # Adjust buffer size as needed
        #         print(shell_env, end='')
        #     else:
        #         break
        
        for sub, sess in subjects_and_sessions:
            for ses in sess:
                print(sub, ses)
                
                try:
                    print('begin sbatch command')
                    sbatch_cmd = sbatch_command(server_bids_path, sub, ses, job_info, args=args)
                    
                    print(sbatch_cmd)
                    print(f'bash -l -c \"{sbatch_cmd}\"')
                    # job_submitted.append('bruh-1234')
                    
                    # shell.send(f'{sbatch_cmd} \n')
                    # time.sleep(1)
                    
                    # job_id = shell.recv(4096).decode('utf-8')
                    # job_submitted.append(job_id)
                    
                    # stdin, stdout, stderr = await loop.run_in_executor(None, lambda: ssh.exec_command(f'bash -l -c \"{sbatch_cmd} \"'))
                    stdin, stdout, stderr = ssh.exec_command(f'bash -l -c \"{sbatch_cmd} \"')
                    output = stdout.read().decode()
                    error = stderr.read().decode()
                    print(output)
                    print(error)
                    
                    job_submitted.append(output)
                    
                except Exception as e:
                    raise JobSubmissionError(f"Error {e} while submiting a job")
        
        # close connection
        ssh.close()
        print('connection closed ')
        return job_submitted                
        
    except JobSubmissionError as e:
        print(f'JobSubmissionError: {e}')
        raise JobSubmissionError(e)
    except Exception as e:
        print('Exception')
        raise ServerConnectionError(f"Server Connection error: {e}")
    # finally:
    #     print('finally')
    #     ssh.close()
    #     return None
   

async def to_thread(func, /, *args, **kwargs):
    loop = asyncio.get_running_loop()
    ctx = contextvars.copy_context()
    func_call = functools.partial(ctx.run, func, *args, **kwargs)
    return await loop.run_in_executor(None, func_call)



async def paramiko_connect_ssh(server_info):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        await to_thread(ssh.connect, server_info["server"]["host"],
                        username=server_info["server"]["user"],
                        key_filename=server_info["server"]["key"])
        print('ssh connected')
        return ssh
    except Exception as e:
        print(f"Error in connect_ssh: {e}")
        raise ServerConnectionError(f"Server Connection error: {e}")

async def paramiko_run_ssh_command(ssh, command):
    try:
        stdin, stdout, stderr = await to_thread(ssh.exec_command, command)
        return stdin, stdout, stderr
    except Exception as e:
        print(f"Command execution error: {e}")
        return None
    
def connect_ssh(ssh, server_info):
    try:
        print('paramiko instance')
        # SSH connection setup
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print('bruh')
        # Connect to the remote cluster
        # ssh.connect(server_info["server"]["host"], username=server_info["server"]["user"], key_filename=server_info["server"]["key"])
        print('ssh connected')
    
    except Exception as e:
        print(f"Error in connect_ssh: {e}")
        raise ServerConnectionError(f"Server Connection error: {e}")   

    
# def connect_ssh(server_info):
#     try:
#         ssh = paramiko.SSHClient()
#         ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#         ssh.connect(server_info["server"]["host"],
#                     username=server_info["server"]["user"],
#                     key_filename=server_info["server"]["key"])
#         print('SSH connected')
#         return ssh

#     except Exception as e:
#         print(f'Error connecting to SSH: {e}')
#         return ServerConnectionError(f'Error connecting to SSH: {e}')
    
    
    
# =============================================================================
# submit_job Function from ChatGPT
# =============================================================================
def chatgpt_submit_job(bids_path, sub, ses, job_json, args=[]):
    server_info = get_server_info()
    if server_info is None:
        raise ServerInfoError("Problems when reading the Server Info file")
    
    server_bids_path = map_path(bids_path, server_info['shared_folders'])
    if server_bids_path is None:
        raise PathMappingError("Problems when mapping the local Shared folder path to the remote server path")
    
    if isinstance(job_json, dict):
        job_info = job_json
    elif isinstance(job_json, str):
        job_info = get_job_info(job_json)
        if job_info is None:
            raise JobInfoError("Problems when reading the Job Info file")
    else:
        raise JobInfoError("Problems when reading the Job Info file")

    args_path = []
    for arg in args:
        if pexists(arg):
            arg_map = map_path(arg, server_info['shared_folders'])
            args_path.append(arg_map)
        else:
            args_path.append(arg)
    args = args_path

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server_info["server"]["host"], username=server_info["server"]["user"], key_filename=server_info["server"]["key"])
        
        subjects_and_sessions = [(sub, [ses])] if sub != 'all' else [] # Simplified for this example
        job_submitted = []
        
        for sub, sess in subjects_and_sessions:
            for ses in sess:
                try:
                    sbatch_cmd = sbatch_command(server_bids_path, sub, ses, job_info, args=args)
                    stdin, stdout, stderr = ssh.exec_command(f'bash -l -c \"{sbatch_cmd} \"')
                    output = stdout.read().decode()
                    error = stderr.read().decode()
                    if error:
                        raise JobSubmissionError(error)
                    job_submitted.append(output.strip())
                except Exception as e:
                    raise JobSubmissionError(f"Error {e} while submitting a job")
        
        ssh.close()
        return job_submitted
    except Exception as e:
        raise ServerConnectionError(f"Server Connection error: {e}")
    



def old_submit_job(bids_path, sub, ses, modality, img):
    
    sss_bids_path = map_path(bids_path)

    # SSH connection parameters
    ssh_host = 'cc-login.icp.ucl.ac.be'
    ssh_user = 'vdbulckeco'
    ssh_private_key_path = '/home/colin/.ssh/id_rsa.ceci'
    
    # SSH connection setup
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # Connect to the remote cluster
    ssh.connect(ssh_host, username=ssh_user, key_filename=ssh_private_key_path)
    
    # Create the Ouput directory
    sub_ses_den = pjoin(bids_path, 'derivatives', 'Denoise', f'sub-{sub}', f'ses-{ses}') 
    if not pexists(sub_ses_den):
        os.makedirs(sub_ses_den)
    
    # SLURM job parameters
    job_name = f'DenoiseImg_sub-{sub}_ses-{ses}'
    output_log = pjoin(sss_bids_path, 'derivatives', 'Denoise', f'sub-{sub}', f'ses-{ses}', f'slurm-denoise.out')
    error_log = pjoin(sss_bids_path, 'derivatives', 'Denoise', f'sub-{sub}', f'ses-{ses}', f'slurm-denoise.err')
    nodes = 1
    ntasks = 1
    cpus_per_task = 1
    mem_per_cpu = 2096
    t = '00:10:00'
    job_script_path = '/storage/research/ions/cemo-pm/shared/scripts/bids_denoise_img.py'
    job_sh_path = '/storage/research/ions/cemo-pm/shared/scripts/bids_denoise_img.sh'
    
    # Construct the sbatch command with job parameters
    sbatch_script = f'''--job-name={job_name}
--output={output_log}
--error={error_log}
--nodes={nodes}
--ntasks={ntasks}
--cpus-per-task={cpus_per_task}
--mem-per-cpu={mem_per_cpu}
--time={t}
module purge 
module load ANTs
python3 {job_script_path} {sss_bids_path} {sub} {ses} -d {modality} -i {img}
rm {job_script_path}
rm {job_sh_path}
    '''
    
    generate_shell_script(sbatch_script, pjoin('/home/colin/Programs/BMAT/BMAT/LocalPipelines/test_job_sss', 'bids_denoise_img.sh'))
    
    # Copy file to execute
    try:
        ftp_client=ssh.open_sftp()
        ftp_client.put(pjoin('/home/colin/Programs/BMAT/BMAT/LocalPipelines/test_job_sss', 'bids_denoise_img.py'), '/storage/research/ions/cemo-pm/shared/scripts/bids_denoise_img.py')
        ftp_client.put(pjoin('/home/colin/Programs/BMAT/BMAT/LocalPipelines/test_job_sss', 'bids_denoise_img.sh'), '/storage/research/ions/cemo-pm/shared/scripts/bids_denoise_img.sh')
        # ftp_client.close()
    except FileNotFoundError as e:
        print(f"Local file not found: {e}")

    except IOError as e:
        print(f"Error accessing local file: {e}")

    except PermissionError as e:
        print(f"Permission denied: {e}")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Close the SFTP session and SSH connection
        ftp_client.close()
        
    
    sbatch_command = f'sbatch {job_sh_path}'
    
    # print(sbatch_command)
    # # Submit SLURM job using sbatch command
    # stdin, stdout, stderr = ssh.exec_command(sbatch_command)
    
    # # Print the output and errors
    # print("Job submission output:")
    # print(stdout.read().decode())
    # print("Job submission errors:")
    # print(stderr.read().decode())
    
    shell = ssh.invoke_shell()
    
    shell.send(f'{sbatch_command} \n')
    
    # time.sleep(1)
    
    while True:
        if shell.recv_ready():
            output = shell.recv(4096).decode()  # Adjust buffer size as needed
            print(output, end='')
        else:
            break
        print(output)
    
    shell.close()
    
    # def sss_cmd(sbatch_command):
    #     print(sbatch_command)
    #     shell = ssh.invoke_shell()
    #     shell.send(f'{sbatch_command} \n')
    #     # Receive and print output until no more data is available
    #     while True:
    #         if shell.recv_ready():
    #             output = shell.recv(4096).decode()  # Adjust buffer size as needed
    #             print(output, end='')
    #         else:
    #             break
    #         print(output)
    #     shell.close()
    
    # Close the SSH connection
    ssh.close()


if __name__ == '__main__':
    
    # with open('/home/colin/Programs/BMAT/BMAT/dcm2bids_sss.json', 'r') as f:
    #     job_info = json.load(f)
    
    # job_ids = submit_job('/mnt/cemo-pm/shared/test/bids_test', '005', '01', job_info, args=['/mnt/cemo-pm/shared/test/VANDEN-BULCKE-COLIN.zip', '-iso'], use_asyncssh=True, passphrase='Colma213!')
    # print(job_ids)
    pass
