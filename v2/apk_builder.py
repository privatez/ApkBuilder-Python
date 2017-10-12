#!/usr//bin/env python
# -*- coding:UTF-8 -*-

import os
import re
import json
import xml_helper

import sys

reload(sys)

sys.setdefaultencoding('utf8')


class ApkBuilder:
    def __init__(self, config, project_root_dir):
        self.config = config
        self.project_root_dir = project_root_dir
        pass

    def modify(self):
        for key in self.config:
            value = self.config[key]
            if key == 'appId':
                self.modify_app_id(value)
            if key == 'appName':
                self.modify_app_name(value)
            if key == 'text':
                self.modify_text(value)
            if key == 'color':
                self.modify_color(value)
            if key == 'image':
                self.modify_image(value)
            if key == 'logo':
                self.modify_app_logo(value)
        pass

    def modify_app_id(self, app_id):
        gradle_file_path = '%s/android/app/build.gradle' % self.project_root_dir

        f = open(gradle_file_path, "r")
        txt = f.read()
        f.close()

        txt = re.sub(r'applicationId "[^"]+"', 'applicationId "' + app_id + '"', txt)
        f = open(gradle_file_path, "w")
        f.write(txt)
        f.close()
        pass

    def modify_app_name(self, app_name):
        res_file_path = '%s/strings.xml' % self.get_android_res_dir('values')
        self.modify_xml_file(res_file_path, 'string', 'app_name', app_name)
        pass

    def modify_text(self, texts):
        self.modify_json_file(self.get_js_res_file_path('text'), texts)
        pass

    def modify_color(self, colors):
        self.modify_json_file(self.get_js_res_file_path('color'), colors)
        pass

    def modify_image(self, images):
        for key in images:
            os.system('cp -f %s %s' % (images[key], '%s/app/images' % self.project_root_dir))
        pass

    # mdpi: 48
    # hdpi: 72
    # xhdpi: 96
    # xxhdpi: 144
    # xxxhdpi: 192
    def modify_app_logo(self, images):
        for key in images:
            image = images[key]
            logo_dir_name = None
            if key == '48px':
                logo_dir_name = 'mipmap-mdpi'
            if key == '72px':
                logo_dir_name = 'mipmap-hdpi'
            if key == '96px':
                logo_dir_name = 'mipmap-xhdpi'
            if key == '144px':
                logo_dir_name = 'mipmap-xxhdpi'
            if key == '192px':
                logo_dir_name = 'mipmap-xxxhdpi'

            os.system('cp -f %s %s/ic_launcher.png' % (image, self.get_android_res_dir(logo_dir_name)))
        pass

    def modify_json_file(self, file_path, configs):
        with open(file_path, 'r') as config_file_r:
            config_json = json.load(config_file_r)

        for key in configs:
            if key in config_json:
                config_json[key] = configs[key]

        with open(file_path, 'w') as config_file_w:
            json.dump(config_json, config_file_w)
        pass

    def modify_xml_file(self, file_path, tag, node_name, value):
        tree = xml_helper.read_xml(file_path)
        nodes = xml_helper.find_nodes(tree, tag)
        result_nodes = xml_helper.get_node_by_keyvalue(nodes, {"name": node_name})
        xml_helper.change_node_text(result_nodes, value)
        xml_helper.write_xml(tree, file_path)
        pass

    def get_js_res_file_path(self, category):
        return '%s/app/res/%s.json' % (self.project_root_dir, category)

    def get_android_res_dir(self, category):
        return '%s/android/app/src/main/res/%s' % (self.project_root_dir, category)

    def build(self):
        # 打包 app
        os.system('cd %s/android && ./gradlew assembleRelease' % self.project_root_dir)

        return '%s/android/app/build/outputs/apk/app-release.apk' % self.project_root_dir
