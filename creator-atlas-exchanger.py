#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import platform
import sys

import plistlib


class Logger:

    def __init__(self):
        if platform.system() == 'Windows':
            self.HEADER = ''
            self.OKBLUE = ''
            self.OKGREEN = ''
            self.WARNING = ''
            self.FAIL = ''
            self.ENDC = ''
        else:
            self.HEADER = '\033[95m'
            self.OKBLUE = '\033[94m'
            self.OKGREEN = '\033[92m'
            self.WARNING = '\033[93m'
            self.FAIL = '\033[91m'
            self.ENDC = '\033[0m'

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


class ImageRef:

    def __init__(self, atlas: str, name: str, uuid: str, rawTextureUuid: str, atlasUuid: str, atlasRawTextureUuid: str):
        self._atlas = atlas
        self._name = name
        self._uuid = uuid
        self._rawTextureUuid = rawTextureUuid
        self._atlasUuid = atlasUuid
        self._atlasRawTextureUuid = atlasRawTextureUuid

    def __str__(self):
        return self._atlas + '[' + self._name + ']'

    def atlas(self):
        return self._atlas

    def name(self):
        return self._name

    def uuid(self):
        return self._uuid

    def rawTextureUuid(self):
        return self._rawTextureUuid

    def atlasUuid(self):
        return self._atlasUuid

    def atlasRawTextureUuid(self):
        return self._atlasRawTextureUuid


def get_plist_images(plist_path: str, image_dict: dict[str, ImageRef]):
    try:
        with open(plist_path, 'rb') as fp:
            plist = plistlib.load(fp, fmt=plistlib.FMT_XML)
    except:
        plist = None
        log.fail("read plist failed: " + str(sys.exc_info()[0]))

    if plist is not None:
        image_names = plist['frames'].keys()
        plist_meta_json = json.load(open(plist_path + '.meta'))

        atlas_name = plist_path
        atlas_uuid = plist_meta_json['uuid']
        atlas_rawTextureUuid = plist_meta_json['rawTextureUuid']

        meta = plist_meta_json['subMetas']
        for img_name in image_names:
            if meta.get(img_name, None) is not None:
                ref = meta[img_name]
            else:
                ref = meta[str(img_name).replace('/', '-')]

            if img_name in image_dict:
                raise Exception('duplicate image name: ' + img_name)

            image_dict[img_name] = ImageRef(atlas_name, img_name, ref['uuid'],
                                            ref['rawTextureUuid'], atlas_uuid, atlas_rawTextureUuid)

    else:
        raise Exception('plist not supported: ' + plist_path)


def get_plist(image_path: str) -> str:
    plist_path = image_path[:-4] + '.plist'
    if os.path.exists(plist_path) and os.path.isfile(plist_path):
        return plist_path
    else:
        return None


def get_image(image_path: str, image_dict: dict[str, ImageRef]):
    if image_path.lower().endswith('.png') or image_path.lower().endswith('.jpg'):
        image_name = os.path.basename(image_path)

        if image_name in image_dict:
            raise Exception('duplicate image name: ' + image_name)

        image_meta_json = json.load(open(image_path + '.meta'))
        meta = image_meta_json['subMetas']
        ref_key = image_name[:-4]  # .png len
        if meta.get(ref_key, None) is not None:
            ref = meta[ref_key]

        image_dict[image_name] = ImageRef(
            '', image_name, ref['uuid'], ref['rawTextureUuid'], '', '')
    else:
        raise Exception('not support image type: ' + image_path)


def get_folder_images(folder_path, image_dict: dict[str, ImageRef]):
    if not os.path.exists(folder_path):
        raise Exception('folder not exists: ' + folder_path)
    for root, _, files in os.walk(folder_path):
        for fn in files:
            file_path = os.path.join(root, fn)
            plist_path = get_plist(file_path)
            if plist_path is not None:
                get_plist_images(plist_path, image_dict)
            elif fn.lower().endswith('.png') or fn.lower().endswith('.jpg'):
                get_image(file_path, image_dict)


class ImageRefReplace:

    def __init__(self, image_from: ImageRef, image_to: ImageRef):
        self._image_from = image_from
        self._image_to = image_to

    def __str__(self):
        return self._image_from.atlas() + '[' + self._image_from.name() + '] -> ' + self._image_to.atlas() + \
            '[' + self._image_to.name() + ']'

    def from_uuid(self):
        return self._image_from.uuid()

    def to_uuid(self):
        return self._image_to.uuid()

    def from_rawTextureUuid(self):
        return self._image_from.rawTextureUuid()

    def to_rawTextureUuid(self):
        return self._image_to.rawTextureUuid()

    def from_atlasUuid(self):
        return self._image_from.atlasUuid()

    def to_atlasUuid(self):
        return self._image_to.atlasUuid()

    def from_atlasRawTextureUuid(self):
        return self._image_from.atlasRawTextureUuid()

    def to_atlasRawTextureUuid(self):
        return self._image_to.atlasRawTextureUuid()


def contains_src_uuid(images_from: dict[str, ImageRef], images_to: dict[str, ImageRef], line: str) -> list[ImageRefReplace]:
    replaces = []
    for k in images_from:
        o = images_from[k]

        if len(o.uuid()) > 0 and str(line).find(o.uuid()) != -1:
            replaces.append(ImageRefReplace(o, images_to[o.name()]))
        if len(o.rawTextureUuid()) > 0 and str(line).find(o.rawTextureUuid()) != -1:
            replaces.append(ImageRefReplace(o, images_to[o.name()]))
        if len(o.atlasUuid()) > 0 and str(line).find(o.atlasUuid()) != -1:
            replaces.append(ImageRefReplace(o, images_to[o.name()]))
        if len(o.atlasRawTextureUuid()) > 0 and str(line).find(o.atlasRawTextureUuid()) != -1:
            replaces.append(ImageRefReplace(o, images_to[o.name()]))
    return replaces


def change_image_sprite_frame_refer(images_from: dict[str, ImageRef], images_to: dict[str, ImageRef], project_path: str) -> int:

    assets = os.path.join(project_path, 'assets')

    change_count = 0
    for root, _, files in os.walk(assets):
        for fn in files:
            if not (fn.lower().endswith('.anim') or fn.lower().endswith('.prefab') or fn.lower().endswith('.fire')):
                continue

            file_path = os.path.join(root, fn)

            log.head('working on ' + file_path + ' ...')

            f = open(file_path, encoding='utf-8')
            content = f.readlines()
            f.close()

            for i in range(0, len(content)):
                l = content[i]
                replaces = contains_src_uuid(images_from, images_to, l)
                if len(replaces) == 0:
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

                sf = '\t'
                for r in replaces:
                    if len(sf) > 0:
                        sf += '\n\t'
                    sf += str(r)

                log.head(
                    'will replace sprite frames\n' + sf + '\nin ' + file_path)
                change_count += 1

                for r in replaces:
                    if len(r.from_uuid()) > 0:
                        content[i] = content[i].replace(
                            r.from_uuid(), r.to_uuid())
                    if len(r.from_rawTextureUuid()) > 0:
                        content[i] = content[i].replace(
                            r.from_rawTextureUuid(), r.to_rawTextureUuid())
                    if len(r.from_atlasUuid()) > 0:
                        content[i] = content[i].replace(
                            r.from_atlasUuid(), r.to_atlasUuid())
                    if len(r.from_atlasRawTextureUuid()) > 0:
                        content[i] = content[i].replace(
                            r.from_atlasRawTextureUuid(), r.to_atlasRawTextureUuid())

            f = open(file_path, 'w', encoding='utf-8')
            f.writelines(content)
            f.close()

    return change_count


def deal_with_images(images_from: dict[str, ImageRef], images_to: dict[str, ImageRef], project_path: str):

    log.head('deal_with_images')

    for k in images_from:
        img_from = images_from[k]
        img_to = images_to[k]
        log.warn('\t' + img_from.atlas() + '[' + img_from.name() + '] -> ' + img_to.atlas() +
                 '[' + img_to.name() + ']')

    do = 'Y'
    log.fail('continue? Y/n')
    do = input()

    change_count = 0
    if do.strip().startswith('Y'):
        change_count = change_image_sprite_frame_refer(
            images_from, images_to, project_path)

    return change_count


def main():

    arg_len = len(sys.argv)

    folder_from = ""
    plist_to = ""
    project_path = ""

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
        else:
            idx += 1

    if len(folder_from) == 0 or len(plist_to) == 0:
        print('using creator-atlas-exchanger '
              '\n\t-f [from folder path]'
              '\n\t-t [to folder path]'
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

    # enum from folder
    from_images: dict[str, ImageRef] = {}
    get_folder_images(folder_from, from_images)

    # enum to plist
    to_images: dict[str, ImageRef] = {}
    get_folder_images(plist_to, to_images)

    # print images not in to
    not_in_to = []
    from_keys = list(from_images.keys())
    for i in range(0, len(from_keys)):
        key = from_keys[i]
        if key.endswith('.plist'):
            continue
        if key not in to_images:
            not_in_to.append(from_images[key])
            from_images.remove(key)

    if len(not_in_to) > 0:
        log.warn('images not in to: ')
        for img in not_in_to:
            log.warn('\t' + str(img))

    # print images not in from
    not_in_from = []
    to_keys = list(to_images.keys())
    for i in range(0, len(to_keys)):
        key = to_keys[i]
        if key.endswith('.plist'):
            continue
        if key not in from_images:
            not_in_from.append(to_images[key])
            to_images.remove(key)

    if len(not_in_from) > 0:
        log.warn('images not in from: ')
        for img in not_in_from:
            log.warn('\t' + str(img))

    if len(not_in_from) > 0 and len(not_in_to) > 0:
        do = ''
        log.fail('continue? Y/n')
        do = input()

        if do.strip() != 'Y':
            log.fail('exit.')
            return

    deal_with_images(from_images, to_images, project_path)

    print()
    log.green('Done.')


if __name__ == '__main__':
    main()
