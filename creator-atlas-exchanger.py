#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hashlib
import json
import os
import shutil
import subprocess
import sys

import biplist


class Logger:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def enable(self):
        self.HEADER = '\033[95m'
        self.OKBLUE = '\033[94m'
        self.OKGREEN = '\033[92m'
        self.WARNING = '\033[93m'
        self.FAIL = '\033[91m'
        self.ENDC = '\033[0m'

    def disable(self):
        self.HEADER = ''
        self.OKBLUE = ''
        self.OKGREEN = ''
        self.WARNING = ''
        self.FAIL = ''
        self.ENDC = ''

    def head(self, s):
        print(self.HEADER + str(s) + self.ENDC)

    def blue(self, s):
        print(self.OKBLUE + str(s) + self.ENDC)

    def green(self, s):
        print(self.OKGREEN + str(s) + self.ENDC)

    def warn(self, s):
        print(self.WARNING + str(s) + self.ENDC)

    def fail(self, s):
        print(self.FAIL + str(s) + self.ENDC)


log = Logger()

list_folder_name = ['res', 'src', 'subpackages']


def run_cmd(cmd):
    log.blue("run cmd: " + " ".join(cmd))
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if err:
        print(err)
    return out


def self_install(file, des):
    file_path = os.path.realpath(file)

    filename = file_path

    pos = filename.rfind("/")
    if pos:
        filename = filename[pos + 1:]

    pos = filename.find(".")
    if pos:
        filename = filename[:pos]

    to_path = os.path.join(des, filename)

    log.blue("installing [" + file_path + "] \n\tto [" + to_path + "]")
    if os.path.isfile(to_path):
        os.remove(to_path)

    shutil.copy(file_path, to_path)
    run_cmd(['chmod', 'a+x', to_path])


def mkdir_p(path):
    try:
        if path == "":
            return

        if os.path.isfile(path):
            print("remove file: " + path)
            os.remove(path)

        if not os.path.isdir(path):
            print("make dir: " + path)
            os.makedirs(path)

    except Exception as exc:
        print(exc)


def base_folder(path):
    path = os.path.normpath(path)
    path = str(path).rstrip(os.path.sep)
    pos = path.rfind(os.path.sep)
    if pos == -1:
        return ""
    else:
        path = path[:pos]
        path = path.rstrip(os.path.sep)
        return path


def generate_file_md5(file_path, block_size=2 ** 20):
    if not os.path.isfile(file_path):
        return ''

    m = hashlib.md5()
    with open(file_path, "rb") as f:
        while True:
            buf = f.read(block_size)
            if not buf:
                break
            m.update(buf)
    return m.hexdigest()


# return map :
# '01.png' : <
# 'name': '01.png',
# 'uuid': 'd9c6fbc0-ddb0-497a-a670-a86bb0bb143d',
# 'rawTextureUuid': 'abcb3647-c223-4d8d-bf73-63cab31c5d46'
# >
def get_plist_images(plist_path):
    try:
        plist = biplist.readPlist(plist_path)
    except:
        plist = None
        log.fail("read plist failed: " + str(sys.exc_info()[0]))

    if plist is not None:
        ret = {}
        images = plist['frames'].keys()
        j = json.load(open(plist_path + '.meta'))
        meta = j['subMetas']
        for k in images:
            ret[k] = {
                'name': k,
                'uuid': meta[k]['uuid'],
                'rawTextureUuid': meta[k]['rawTextureUuid'],
            }
        return ret

    exit(-1)


# return map :
# '01.png' : <
# 'name': '01.png',
# 'uuid': 'd9c6fbc0-ddb0-497a-a670-a86bb0bb143d',
# 'rawTextureUuid': 'abcb3647-c223-4d8d-bf73-63cab31c5d46',
# 'src-uuid': 'd9c6fbc0-ddb0-497a-a670-a86bb0bb143d',
# 'src-rawTextureUuid': 'abcb3647-c223-4d8d-bf73-63cab31c5d46',
# >
def get_folder_images(folder_from, plist_images):
    image_refers = plist_images
    image_names = plist_images.keys()
    warn = 0
    ref = 0
    for root, dirs, files in os.walk(folder_from):
        for fn in files:
            if not fn.lower().endswith('.png'):
                continue

            if fn not in image_names:
                log.warn(fn + ' in ' + root + ' not in plist')
                warn += 1
                continue

            img_path = os.path.join(root, fn)
            j = json.load(open(img_path + '.meta'))
            k = fn[:-4]  # .png len
            meta = j['subMetas'][k]

            image_refers[fn]['src-path'] = img_path
            image_refers[fn]['src-uuid'] = meta['uuid']
            image_refers[fn]['src-rawTextureUuid'] = meta['rawTextureUuid']
            ref += 1

    return image_refers, warn, ref


def contains_src_uuid(image_refers, line):
    uuid = []
    rawTextureUuid = []
    for k in image_refers:
        o = image_refers[k]
        if str(line).find(o['src-uuid']) != -1:
            uuid.append(o)
        if str(line).find(o['src-rawTextureUuid']) != -1:
            rawTextureUuid.append(o)
    return uuid, rawTextureUuid


def change_image_sprite_frame_refer(image_refers, project_path):
    assets = os.path.join(project_path, 'assets')

    for root, dirs, files in os.walk(assets):
        for fn in files:
            if not (fn.lower().endswith('.anim') or fn.lower().endswith('.prefab') or fn.lower().endswith('.fire')):
                continue

            file_path = os.path.join(root, fn)

            log.head('working on ' + file_path + ' ...')

            f = open(file_path)
            content = f.readlines()
            f.close()

            for i in range(0, len(content)):
                l = content[i]
                uuid, rawTextureUuid = contains_src_uuid(image_refers, l)
                if len(uuid) == 0 and len(rawTextureUuid) == 0:
                    continue

                start = i - 2
                if start < 0:
                    start = 0
                end = i + 3
                if end > len(content):
                    end = len(content)

                log.head('found lines to replace: ' + str(i))

                for j in range(start, end):
                    log.blue(content[j])

                sf = ''
                for u in uuid:
                    if len(sf) > 0:
                        sf += ', '
                    sf += u['name']

                tx = ''
                for r in rawTextureUuid:
                    if len(tx) > 0:
                        tx += ', '
                    tx += r['name']

                log.head('will replace sprite frames [' + sf + '] and textures [' + tx + '] in ' + file_path)

                sig = input()

                if len(sig):
                    continue

                for u in uuid:
                    content[i] = content[i].replace(u['src-uuid'], u['uuid'])

                for r in rawTextureUuid:
                    content[i] = content[i].replace(r['src-rawTextureUuid'], r['rawTextureUuid'])

            f = open(file_path, 'w')
            f.writelines(content)
            f.close()


def deal_with_images(folder_from, plist_to, project_path):
    log.head('reading plist images ...')

    plist_images = get_plist_images(plist_to)

    log.head('searching images ...')
    print()

    image_refers, warn_count, ref_count = get_folder_images(folder_from, plist_images)

    for k in image_refers:
        o = image_refers[k]
        log.green('will exchange ref :')
        log.blue('\t' + o['src-path'])
        log.green('with ref :')
        log.blue('\t' + o['name'] + ' in ' + plist_to)
        print()

    log.fail('warn count: ' + str(warn_count))
    log.fail('ref count: ' + str(ref_count))
    log.fail('continue? Y/n')

    do = input()

    if do.strip().startswith('Y'):
        change_image_sprite_frame_refer(image_refers, project_path)


def main():
    # self_install
    if len(sys.argv) > 1 and sys.argv[1] == 'install':
        self_install("creator-atlas-exchanger.py", "/usr/local/bin")
        return

    arg_len = len(sys.argv)

    folder_from = ""
    plist_to = ""
    project_path = ""

    idx = 1
    while idx < arg_len:
        cmd_s = sys.argv[idx]
        if cmd_s[0] == "-":
            c = cmd_s[1:]
            v = sys.argv[idx + 1]
            if c == "f":
                folder_from = v
            elif c == "t":
                plist_to = v
            elif c == "p":
                project_path = v
            idx += 2
        else:
            idx += 1

    if len(folder_from) == 0 or len(plist_to) == 0:
        print('using creator-atlas-exchanger '
              '\n\t-f [from folder path]'
              '\n\t-t [to plist path]'
              '\n\t-p [project path]'
              "\n\tto run")
        return

    if not os.path.isabs(folder_from):
        folder_from = os.path.join(os.getcwd(), folder_from)

    if not os.path.isabs(plist_to):
        plist_to = os.path.join(os.getcwd(), plist_to)

    if not os.path.isabs(project_path):
        if project_path == '.':
            project_path = os.getcwd()
        else:
            project_path = os.path.join(os.getcwd(), project_path)

    deal_with_images(folder_from, plist_to, project_path)

    log.green('Done.')


if __name__ == '__main__':
    main()
