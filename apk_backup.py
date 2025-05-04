#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import re
import sys
import shutil
import tempfile
import subprocess

def find_cmd(cmd):
    for cname in (f'{cmd}', f'{cmd}.exe'):
        if shutil.which(cname):
            return cname
    return None

package_name_patt = re.compile(r'  Package \[(.+)\] \([a-f0-9]+\):')
version_name_patt = re.compile(r'    versionName=(.+)$')
#apk_name_patt = re.compile(r'package:(.+)=([-_a-fA-Z0-9.]+)')
apk_name_patt = re.compile(r'package:(.+)=(.+)')
application_label_patt = re.compile('application-label(-ja)?\:\'(.+)\'')

def list_packages(output=False):
    packages = {}
    adb_cmd = find_cmd('adb')

    # パッケージ名とバージョン一覧を取得
    for s in subprocess.check_output(f'{adb_cmd} shell dumpsys package packages', shell=True).decode('utf-8').split('\n'):
        # CR+LF対策
        if len(s) > 0 and s[-1] == '\r':
            s = s.rstrip()
        m = package_name_patt.match(s)
        if m:
            app_id = m.group(1)
            version = ''

            if app_id in packages:
                continue
        m = version_name_patt.match(s)
        if m:
            version = m.group(1)
            packages[app_id] = {'version': version}

    # 各パッケージのapkファイル名を取得
    for s in subprocess.check_output(f'{adb_cmd} shell pm list packages -f', shell=True).decode('utf-8').split('\n'):
        # CR+LF対策
        if len(s) > 0 and s[-1] == '\r':
            s = s.rstrip()
        m = apk_name_patt.match(s)
        if m:
            app_id = m.group(2)
            apk_name = m.group(1)
            #print(s, app_id, apk_name)
            if app_id in packages:
                packages[app_id]['apk_name'] = apk_name
            else:
                packages[app_id] = {'apk_name': apk_name, 'version': ''}

    # 画面出力
    if output:
        for p in sorted(packages):
            print('%s (%s)' % (p, packages[p]['version']))

    return packages

def backup_package(pname):

    # パッケージ情報を取得
    packages = list_packages(output=False)

    # 指定したパッケージがインストールされているかチェック
    if pname not in packages:
        print('Error: not such package: %s' % pname)
        return

    adb_cmd = find_cmd('adb')
    # apkファイルを取り出し
    tempname = tempfile.mktemp(suffix='.apk')
    #print(tempname)
    cmd = f'{adb_cmd} pull {packages[pname]["apk_name"]} {tempname}'
    print(cmd)
    subprocess.call(cmd, shell=True)

    aapt_cmd = find_cmd('aapt')
    if aapt_cmd:
        # aaptコマンドがあればアプリケーション名を取得
        app_label = ''
        cmd = f'{aapt_cmd} dump badging {tempname}'
        for s in subprocess.check_output(cmd, shell=True).decode('utf-8').split('\n'):
            # CR+LF対策
            if len(s) > 0 and s[-1] == '\r':
                s = s.rstrip()
            m = application_label_patt.match(s)
            
            if m:
                app_label = m.group(2)
                #print(app_label)
        if app_label != '':
            # アプリケーション名が分かればそれを出力ファイル名に
            ofname = '%s_%s__%s.apk' % (app_label, packages[pname]['version'], pname)
        else:
            ofname = '%s_%s.apk' % (pname, packages[pname]['version'])
    else:
        # aaptコマンドがなければパッケージ名を出力ファイル名に
        ofname = '%s_%s.apk' % (pname, packages[pname]['version'])

    # apkファイル名を変更
    shutil.move(tempname, ofname)    
    print('->', ofname)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Backup apk from Android device.')
    parser.add_argument('-l', '--list', action='store_true', help='List install packages')
    parser.add_argument('-b', '--backup', nargs=1, help='Backup specific package')

    args = parser.parse_args()
    if args.list:
        list_packages(output=True)
    elif args.backup:
        backup_package(args.backup[0])
    else:
        parser.print_help()
        sys.exit()

        
