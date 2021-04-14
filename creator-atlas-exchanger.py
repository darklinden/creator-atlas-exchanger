#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
            if meta.get(k, None) is not None:
                ref = meta[k]
            else:
                ref = meta[str(k).replace('/', '-')]

            ret[k] = {
                'name': k,
                'uuid': ref['uuid'],
                'rawTextureUuid': ref['rawTextureUuid'],
            }

        basename = os.path.basename(plist_path)
        ret[basename] = {
            'name': basename,
            'uuid': j['uuid'],
            'rawTextureUuid': j['rawTextureUuid'],
        }

        return ret

    exit(-1)


# return map :
# '01.png' : <
# 'name': '01.png',
# 'uuid': 'd9c6fbc0-ddb0-497a-a670-a86bb0bb143d',
# 'rawTextureUuid': 'abcb3647-c223-4d8d-bf73-63cab31c5d46',
# 'ref' : [{
# 'path': '',
# 'name': '',
# 'uuid': 'd9c6fbc0-ddb0-497a-a670-a86bb0bb143d',
# 'rawTextureUuid': 'abcb3647-c223-4d8d-bf73-63cab31c5d46',
# }]>
def get_folder_images(folder_from, plist_images, plist_path, quiet):
    image_refers = plist_images
    warn = 0
    ref = 0
    yes_to_all = quiet or False
    plist_name = os.path.basename(plist_path)

    # fill image_refers
    for root, dirs, files in os.walk(folder_from):
        for fn in files:
            if fn.lower().endswith('.png'):
                img_path = os.path.join(root, fn)

                in_plist = False
                ref_key = ''
                for rk in plist_images:
                    n = plist_images[rk]
                    if img_path.endswith(n['name']):
                        ref_key = rk
                        in_plist = True
                        break

                if not in_plist:
                    log.warn(fn + ' in [ ' + root + ' ] not in plist')
                    print()
                    warn += 1
                    continue

                j = json.load(open(img_path + '.meta'))
                k = fn[:-4]  # .png len
                meta = j['subMetas'][k]

                log.head('will replace png named [ ' + fn + ' ] reference [ ' + img_path + ' ] with plist')

                do = None
                if not yes_to_all:
                    log.fail('return to continue, n/N to skip, A yes to all')
                    do = input()

                if do is not None and do.strip().startswith('A'):
                    yes_to_all = True

                if yes_to_all or (not do.strip().startswith('n')):
                    if image_refers[ref_key].get('ref', None) is None:
                        image_refers[ref_key]['ref'] = []
                    image_refers[ref_key]['ref'].append({
                        'path': img_path,
                        'name': ref_key,
                        'uuid': meta['uuid'],
                        'rawTextureUuid': meta['rawTextureUuid']
                    })

                ref += 1

            elif fn.lower().endswith('.plist'):
                plist_path = os.path.join(root, fn)

                try:
                    plist = biplist.readPlist(plist_path)
                except:
                    plist = None
                    log.fail("read plist failed: " + str(sys.exc_info()[0]))

                j = json.load(open(plist_path + '.meta'))
                plist_meta = j['subMetas']
                for k in plist['frames'].keys():
                    if plist_meta.get(k, None) is not None:
                        meta = plist_meta[k]
                    else:
                        meta = plist_meta[str(k).replace('/', '-')]

                    in_plist = False
                    ref_key = ''
                    for rk in plist_images:
                        n = plist_images[rk]
                        if k.endswith(n['name']):
                            ref_key = rk
                            in_plist = True
                            break

                    if not in_plist:
                        log.warn(k + ' in [ ' + plist_path + ' ] not in plist')
                        print()
                        warn += 1
                        continue

                    log.head('will replace png named [ ' + k + ' ] reference [ ' + plist_path + ' ] with plist')

                    do = None
                    if not yes_to_all:
                        log.fail('return to continue, n/N to skip, A yes to all')
                        do = input()

                    if do is not None and do.strip().startswith('A'):
                        yes_to_all = True

                    if yes_to_all or (not do.strip().startswith('n')):
                        if image_refers[ref_key].get('ref', None) is None:
                            image_refers[ref_key]['ref'] = []
                        image_refers[ref_key]['ref'].append({
                            'path': plist_path,
                            'name': ref_key,
                            'uuid': meta['uuid'],
                            'rawTextureUuid': meta['rawTextureUuid']
                        })

                        if image_refers[plist_name].get('ref', None) is None:
                            image_refers[plist_name]['ref'] = []
                        has = False
                        for x in image_refers[plist_name]['ref']:
                            if x['uuid'] == j['uuid']:
                                has = True
                                break
                        if not has:
                            image_refers[plist_name]['ref'].append({
                                'path': plist_path,
                                'name': fn,
                                'uuid': j['uuid'],
                                'rawTextureUuid': j['rawTextureUuid']
                            })

                    ref += 1

    return image_refers, warn, ref


def contains_src_uuid(image_refers, line):
    uuid = []
    rawTextureUuid = []
    for k in image_refers:
        o = image_refers[k]

        if o.get('ref', None) is None:
            continue

        for x in o['ref']:
            if len(x['uuid']) > 0 and str(line).find(x['uuid']) != -1:
                uuid.append({
                    'uuid': o['uuid'],
                    'name': o['name'],
                    'path': x['path'],
                    'src-uuid': x['uuid']
                })
            if len(x['rawTextureUuid']) > 0 and str(line).find(x['rawTextureUuid']) != -1:
                rawTextureUuid.append({
                    'rawTextureUuid': o['rawTextureUuid'],
                    'name': o['name'],
                    'path': x['path'],
                    'src-rawTextureUuid': x['rawTextureUuid']
                })
    return uuid, rawTextureUuid


def change_data_ref(data, key_to_change, value_from, value_to):
    change_count = 0
    for key in data.keys():
        o = data[key]
        if key == key_to_change:
            if value_from == 'any' or o == value_from:
                if o != value_to:
                    data[key] = value_to
                    change_count += 1
        else:
            if isinstance(o, dict):
                o, c = change_data_ref(o, key_to_change, value_from, value_to)
                data[key] = o
                change_count += c
            elif isinstance(o, list):
                new_list = []
                for i in range(0, len(o)):
                    oi, c = change_data_ref(o[i], key_to_change, value_from, value_to)
                    new_list.append(oi)
                    change_count += c
                data[key] = new_list
    return data, change_count


def change_image_sprite_frame_refer(image_refers, project_path) -> int:
    assets = os.path.join(project_path, 'assets')

    change_count = 0
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
                    s = content[j]
                    s = s.strip('\n')
                    log.blue(s)

                sf = ''
                for u in uuid:
                    if len(sf) > 0:
                        sf += ', '
                    sf += u['name'] + ' in ' + u['path']

                tx = ''
                for r in rawTextureUuid:
                    if len(tx) > 0:
                        tx += ', '
                    tx += r['name'] + ' in ' + r['path']

                log.head('will replace sprite frames [' + sf + '] and textures [' + tx + '] in ' + file_path)
                change_count += 1

                for u in uuid:
                    content[i] = content[i].replace(u['src-uuid'], u['uuid'])

                for r in rawTextureUuid:
                    content[i] = content[i].replace(r['src-rawTextureUuid'], r['rawTextureUuid'])

            f = open(file_path, 'w')
            f.writelines(content)
            f.close()

    return change_count


def deal_with_images(folder_from, plist_to, project_path, quiet):
    log.head('reading plist images ...')

    plist_images = get_plist_images(plist_to)

    log.head('get image ref in plist:')
    for k in plist_images.keys():
        log.blue(k)

    print()

    log.head('searching images ...')
    print()

    image_refers, warn_count, ref_count = get_folder_images(folder_from, plist_images, plist_to, quiet)

    for k in image_refers:
        o = image_refers[k]

        if o.get('ref', None) is not None:
            log.green('will exchange ref :')
            for j in o['ref']:
                log.blue('\t' + j['name'] + '  -  ' + j['path'])

            log.green('with ref :')
            log.blue('\t' + o['name'] + ' in ' + plist_to)
            print()

    log.fail('warn count: ' + str(warn_count))
    log.fail('ref count: ' + str(ref_count))
    print()

    do = 'Y'
    if not quiet:
        log.fail('continue? Y/n')
        do = input()

    change_count = 0
    if quiet or do.strip().startswith('Y'):
        change_count = change_image_sprite_frame_refer(image_refers, project_path)

    return change_count


def main():
    # self_install
    if len(sys.argv) > 1 and sys.argv[1] == 'install':
        self_install("creator-atlas-exchanger.py", "/usr/local/bin")
        return

    arg_len = len(sys.argv)

    folder_from = ""
    plist_to = ""
    project_path = ""
    quiet = False

    idx = 1
    while idx < arg_len:
        cmd_s = sys.argv[idx]
        if cmd_s[0] == "-":
            c = cmd_s[1:]
            if c == "f":
                v = sys.argv[idx + 1]
                folder_from = v
                idx += 2
            elif c == "t":
                v = sys.argv[idx + 1]
                plist_to = v
                idx += 2
            elif c == "p":
                v = sys.argv[idx + 1]
                project_path = v
                idx += 2
            elif c == "q":
                quiet = True
                idx += 1
        else:
            idx += 1

    if len(folder_from) == 0 or len(plist_to) == 0:
        print('using creator-atlas-exchanger '
              '\n\t-f [from folder path]'
              '\n\t-t [to plist path]'
              '\n\t-p [project path]'
              '\n\t[ -q quiet mode ]'
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

    change_log = []
    if os.path.isdir(plist_to):
        for root, dirs, files in os.walk(plist_to):
            for fn in files:
                if fn.lower().endswith('.plist'):
                    plist_path = os.path.join(root, fn)
                    change_count = deal_with_images(folder_from, plist_path, project_path, quiet)
                    change_log.append('with: [' + plist_path + '] changed references: ' + str(change_count))
    else:
        change_count = deal_with_images(folder_from, plist_to, project_path, quiet)
        change_log.append('with: [' + plist_to + '] changed references: ' + str(change_count))

    print()

    for line in change_log:
        log.green(line)

    log.green('Done.')


if __name__ == '__main__':
    main()
