#!/usr//bin/env python
# -*- coding:UTF-8 -*-

import os
import json
import time
from concurrent.futures import ProcessPoolExecutor

import xml_helper

ISOTIMEFORMAT = '%Y-%m-%d %X'


def print_time(text='NowTime: '):
    print('%s%s' % (text, time.strftime(ISOTIMEFORMAT, time.localtime())))


def get_base_apk_path():
    return raw_input('Please input the base apk\'s path: ')


def get_res_root_path():
    return raw_input('Please input the res file\'s path: ')


def unpack():
    os.system('mkdir %s' % _apk_source_base_folder)
    os.system('apktool d %s -o %s -f' % (_base_apk_path, _apk_source_base_folder))


_base_apk_path = get_base_apk_path().strip()
_res_root_path = get_res_root_path().strip()


def get_source_file_path(channel):
    return '%s/apk-%s-source' % (_res_root_path, channel)


_apk_source_base_folder = get_source_file_path('base')

_apk_res_config = None

pool = None
task_list = []

# 读取配置
with open(_res_root_path + '/config.json') as config_f:
    _apk_res_config = json.load(config_f)


def modify_apk_source():
    task_pool = ProcessPoolExecutor(max_workers=3)
    for config in _apk_res_config:
        task_list.append(task_pool.submit(modify_and_build, config))


def modify_and_build(config):
    channel = config['channel']
    cp_directory(_apk_source_base_folder, get_source_file_path(channel))
    modify_channel(channel)
    for key in config:
        value = config[key]
        if key == 'apk_name':
            modify_apk_name(channel, value)
        if key == 'apk_package':
            modify_apk_package(channel, value)
            modify_provider(channel, value)
        if key == 'res':
            modify_res(channel, value)
        if key == 'config':
            modify_config(channel, value)
    build_apk(channel, config['signing_configs'])
    if check_job_state():
        print_time('End make app...')


def check_job_state():
    for task in task_list:
        if not task.done():
            return False
    return True


def modify_channel(channel):
    path = '%s/AndroidManifest.xml' % (get_source_file_path(channel))
    tree = xml_helper.read_xml(path)
    nodes = xml_helper.find_nodes(tree, 'application/meta-data')
    result_nodes = xml_helper.get_node_by_keyvalue(nodes, {get_attrib_in_android_xml('name'): "CHANNEL"})
    xml_helper.change_node_properties(result_nodes, {get_attrib_in_android_xml('value'): channel})
    xml_helper.write_xml(tree, path)


def modify_apk_name(channel, apk_name):
    _strings_xml_file_path = get_apk_strings_xml_file_path(channel)
    modify_xml_file(_strings_xml_file_path, 'string', 'app_name', apk_name)


def modify_apk_package(channel, package):
    path = '%s/AndroidManifest.xml' % (get_source_file_path(channel))
    tree = xml_helper.read_xml(path)
    root = tree.getroot()
    root.attrib['package'] = package
    xml_helper.write_xml(tree, path)


def modify_provider(channel, package):
    path = '%s/AndroidManifest.xml' % (get_source_file_path(channel))
    tree = xml_helper.read_xml(path)
    nodes = xml_helper.find_nodes(tree, 'application/provider')
    xml_helper.change_node_properties(nodes, {get_attrib_in_android_xml('authorities'): '%s.provider' % (package)})
    xml_helper.write_xml(tree, path)


def modify_res(channel, res):
    for res_type in res:
        modify_image = res[res_type]
        for image_name in modify_image:
            image_path = '%s/%s/%s-v4/%s' % (get_source_file_path(channel), 'res', res_type, image_name)
            os.system('rm %s' % image_path)
            cp_file('%s/%s-res/%s/%s' % (_res_root_path, channel, res_type, image_name), image_path)


def modify_config(channel, configs):
    # 读取配置
    config_file_path = '%s/assets/config.json' % (get_source_file_path(channel))

    with open(config_file_path, 'r') as config_file_r:
        apk_config = json.load(config_file_r)

    for key in configs:
        apk_config[key] = configs[key]

    with open(config_file_path, 'w') as config_file_w:
        json.dump(apk_config, config_file_w)


def build_apk(channel, signing_configs):
    store_name = signing_configs['store_name']
    key_alias = signing_configs['key_alias']
    key_pwd = signing_configs['key_pwd']
    store_pwd = signing_configs['store_pwd']
    store_path = '%s/%s' % (_res_root_path, store_name)
    source_file_path = get_source_file_path(channel)
    signed_apk_name = get_apk_name(channel)
    unsign_apk_name = 'apk-%s-unsign.apk' % channel
    signin_apk_name_path = '%s/%s' % (_res_root_path, signed_apk_name)
    unsignin_apk_name_path = '%s/%s' % (_res_root_path, unsign_apk_name)
    os.system('rm -rf %s/original/META-INF' % source_file_path)
    os.system('apktool b %s -o %s/%s' % (source_file_path, _res_root_path, unsign_apk_name))
    os.system('jarsigner -sigalg MD5withRSA -digestalg SHA1 -keystore %s -storepass %s -signedjar %s %s %s' % (
        store_path, store_pwd, signin_apk_name_path, unsignin_apk_name_path, key_alias))
    os.system('rm %s/%s' % (_res_root_path, unsign_apk_name))


def get_apk_strings_xml_file_path(channel):
    return '%s/res/values/strings.xml' % (get_source_file_path(channel))


def modify_xml_file(file_path, tag, node_name, value):
    tree = xml_helper.read_xml(file_path)
    nodes = xml_helper.find_nodes(tree, tag)
    result_nodes = xml_helper.get_node_by_keyvalue(nodes, {"name": node_name})
    xml_helper.change_node_text(result_nodes, value)
    xml_helper.write_xml(tree, file_path)


def cp_directory(source, destination):
    os.system('cp -r %s/. %s' % (source, destination))


def cp_file(source, destination):
    os.system('cp %s %s' % (source, destination))


def get_attrib_in_android_xml(attrib):
    return '{http://schemas.android.com/apk/res/android}%s' % attrib


def get_apk_name(channel):
    split_strs = _base_apk_path.split('/')
    base_apk_name = split_strs[len(split_strs) - 1]
    return base_apk_name.replace('release', channel)


if __name__ == '__main__':
    print_time('Start make app...')
    print_time('Start unpackage...')
    # unpack()
    print_time('End unpackage...')

    modify_apk_source()
