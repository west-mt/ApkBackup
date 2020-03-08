#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import tempfile
import subprocess
import argparse

def check_adb():
    return True

def check_aapt():
    return True

package_name_patt = re.compile(r'  Package \[(.+)\] \([a-f0-9]+\):')
version_name_patt = re.compile(r'    versionName=(.+)$')
apk_name_patt = re.compile(r'package:(.+)=(.+)')
application_label_patt = re.compile('application-label(-ja)?\:\'(.+)\'')

def list_packages(output=False):
    packages = {}

    # パッケージ名とバージョン一覧を取得
    for s in subprocess.check_output('adb shell dumpsys package packages', shell=True).decode('utf-8').split('\r\n'):
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
    for s in subprocess.check_output('adb shell pm list packages -f', shell=True).decode('utf-8').split('\r\n'):
        m = apk_name_patt.match(s)
        if m:
            app_id = m.group(2)
            apk_name = m.group(1)
            packages[app_id]['apk_name'] = apk_name

    # 画面出力
    if output:
        for p in sorted(packages):
            print('%s  (%s)' % (p, packages[p]['version']))

    return packages

def backup_package(pname):

    # パッケージ情報を取得
    packages = list_packages(output=False)

    # 指定したパッケージがインストールされているかチェック
    if pname not in packages:
        print('Error: not such package: %s' % pname)
        return

    # apkファイルを取り出し
    tempname = tempfile.mktemp(suffix='.apk')
    #print(tempname)
    cmd = 'adb pull %s %s' % (packages[pname]['apk_name'], tempname)
    print(cmd)
    subprocess.call(cmd, shell=True)

    if check_aapt():
        # aaptコマンドがあればアプリケーション名を取得
        app_label = ''
        cmd = 'aapt dump badging %s' % tempname
        for s in subprocess.check_output(cmd, shell=True).decode('utf-8').split('\n'):
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
    os.rename(tempname, ofname)    
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

        
