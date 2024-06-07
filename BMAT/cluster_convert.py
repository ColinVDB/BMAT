#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar  5 14:26:35 2024

@author: colin
"""

import paramiko
import psutil
import os
from os.path import join as pjoin
from os.path import exists as pexists
import platform

if platform.system() == 'Windows':
    import win32wnet
    
    def enum_network_resources():
        result = []
        try:
            # Enumerate network resources
            net_resources = win32wnet.WNetOpenEnum(
                win32wnet.RESOURCE_GLOBALNET,
                win32wnet.RESOURCETYPE_ANY,
                0,
                None
            )
            while True:
                resources = win32wnet.WNetEnumResource(net_resources)
                if not resources:
                    break
                for resource in resources:
                    result.append({
                        'name': resource.lpRemoteName,
                        'local': resource.lpLocalName,
                        'type': resource.dwDisplayType,
                        'provider': resource.lpProvider
                    })
        except Exception as e:
            print("Error:", e)
        finally:
            win32wnet.WNetCloseEnum(net_resources)
        return result


def relative_subpath(parent_path, child_path):
    # Get the relative path from the parent to the child
    relative_path = os.path.relpath(child_path, parent_path)

    return relative_path


def is_subpath(parent_path, child_path):
    # Get the common path between the two paths
    common_path = os.path.commonpath([parent_path, child_path])

    # If the common path is equal to the parent path, then the child path is a subpath
    return common_path == parent_path


def find_samba_shares():
    samba_shares = []
    for partition in psutil.disk_partitions(all=True):
        if partition.fstype == 'cifs':
            samba_shares.append({
                'mount_point': partition.mountpoint,
                'remote_host': partition.device.split('//')[1].split('/')[0],
                'share_path': '/'.join(partition.device.split('//')[1].split('/')[1:])
            })
    return samba_shares


def map_local_to_cluster_path(bids_path):
    
    samba_shares = find_samba_shares()
    
    if samba_shares == []:
        print('[ERROR] no samba shares mounted on the computer')
        raise ClusterError("No Samba shares mounted on the computer")
    
    share = None
    for partition in samba_shares:
        if is_subpath(partition['mount_point'], bids_path):
            share = partition
            break
    
    if share == None:
        print(f'[ERROR] samba share associated to {bids_path} not found')
        raise ClusterError("samba share associated to {bids_path} not found")
        
    # check if plateforme nima or institute ions
    cluster_group = None
    print(share['share_path'].split('/')[0])
    
    if "nima" in share['share_path'].split('/')[0]:
        cluster_group = '/storage/platform/ions/nima'
    elif 'neur' in share['share_path'].split('/')[0] or 'cosy' in share['share_path'].split('/')[0] or 'cemo' in share['share_path'].split('/')[0]:
        cluster_group = pjoin('/storage/research/ions', share['share_path'].split('/')[0])
    else:
        print(f'[ERROR] path not part of IoNS')
        raise ClusterError("path not part of IoNS")
        
    # transfer bids_path to cluster_bids_path
    relative_path = relative_subpath(share['mount_point'], bids_path)
    
    cluster_bids_path = pjoin(cluster_group, relative_path)
    
    return cluster_bids_path


def upload_dicom_zip():
    
    pass


def upload_dicom_folder():
    
    pass


def unzip_dicom_zip():
    
    pass


def convert_dicom_to_bids():
    
    pass


class ClusterError(Exception):
    
    def __init__(self, message):
        super().__init__(message)


if __name__ == '__main__':
    pass