#!/usr//bin/env python
# -*- coding:UTF-8 -*-


# 部署环境
# npm 环境
# git 环境
# jdk 环境
# android sdk 环境
# gradle 环境


# 源码管理
# 拉取 GitHub 特定分支代码
# 如果本地已有源码就拉取分支最新代码 -> 保持源码为最新
# npm 依赖需要写死
# 每次都需要重新安装 npm 依赖?

# 打包
# 根据配置文件 修改源码
# 图片 -> 替换
# 变量名 -> 修改变量文件
# 包名 -> 修改 app/build.gradle 文件
# 运行 gradle 打包命令


import os
import json
import uuid

from apk_builder import ApkBuilder


def random_task_id():
    return uuid.uuid1()


class ProjectManager:
    def __init__(self, task_id, project_source_dir):
        self.task_id = task_id
        self.project_source_dir = project_source_dir
        self.project_temp_dir = '%s/%s' % (os.getcwd(), self.task_id)
        pass

    def init(self):
        # 在当前目录下创建临时代码文件夹
        os.system('mkdir -p %s' % self.project_temp_dir)

        # 复制一份源码
        os.system('cp -r %s %s' % (self.project_source_dir, self.project_temp_dir))
        pass

    def get_project_root_dir(self):
        return '%s/%s' % (self.project_temp_dir, self.get_project_name(self.project_source_dir))

    def get_project_name(self, project_dir):
        paths = str(project_dir).split('/')
        return paths[len(paths) - 1]

    def clean(self):
        os.system('rm -rf %s' % self.project_temp_dir)
        pass


class PackagingStatusNotifyMgr:
    _packaging_status = {
        'init': 'init',
        'modify': 'modify',
        'building': 'building'
    }

    def __init__(self, task_id):
        self.task_id = task_id
        pass

    def notify(self, status):
        print ('打包任务%s已经进行到 -> %s' % (self.task_id, status))


if __name__ == '__main__':
    project_name = ''
    path = '%s/%s' % (os.getcwd(), project_name)
    config_json_temp = '%s/config.json' % os.getcwd()
    task_id = random_task_id()
    project_mgr = ProjectManager(task_id, path)

    notify_mgr = PackagingStatusNotifyMgr(task_id)

    notify_mgr.notify('init')
    project_mgr.init()

    with open(config_json_temp) as config_r:
        apk_builder = ApkBuilder(json.load(config_r), project_mgr.get_project_root_dir())
        notify_mgr.notify('modify')
        apk_builder.modify()
        notify_mgr.notify('building')
        apk_path = apk_builder.build()
        os.system('cp %s .' % apk_path)

    # project_mgr.clean()
    pass
