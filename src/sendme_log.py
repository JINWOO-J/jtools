#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
import boto3
from botocore.handlers import disable_signing

import os, time, datetime
import sys
import zipfile
import argparse
from termcolor import colored, cprint
from boto3.s3.transfer import TransferConfig
from halo import Halo
import requests
from multiprocessing.pool import ThreadPool
from timeit import default_timer

region_info = {
    "Seoul"   : ".s3",
    "Tokyo"   : "-jp.s3",
    "Virginia": "-va.s3",
    "Hongkong": "-hk.s3.ap-east-1",
    # "Singapore": "-sg.s3",
    # "Mumbai"   : "-mb.s3",
    # "Frankfurt": "-ff.s3",
}


def kvPrint(key, value, color="yellow"):
    class bcolors:
        HEADER = '\033[95m'
        OKBLUE = '\033[94m'
        OKGREEN = '\033[92m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'
    key_width = 9
    key_value = 3
    print(bcolors.OKGREEN + "{:>{key_width}} : ".format(key, key_width=key_width) + bcolors.ENDC, end="")
    print(bcolors.WARNING + "{:>{key_value}} ".format(str(value), key_value=key_value) + bcolors.ENDC)


def findFastestRegion():
    results = {}
    pool = ThreadPool(6)
    i = 0

    spinner = Halo(text=f"Finding fastest region", spinner='dots')
    spinner.start()

    for region_name, region_code in region_info.items():
        URL=f'https://icon-leveldb-backup{region_code}.amazonaws.com/route_check'
        exec_func = "getTime"
        exec_args = ( f"{URL}", region_name )
        results[i]= {}
        results[i]["data"] = pool.apply_async(getattr(sys.modules[__name__], exec_func), exec_args)
        i += 1
    pool.close()
    pool.join()

    last_latency = {}
    for i, p in results.items():
        data = p['data'].get()
        print(f"data => {data}") if args.verbose else False
        if time is not None:
            if len(last_latency) == 0:
                last_latency = data
            if last_latency.get("time") and data.get("time"):
                if last_latency.get("time", 99999) >= data.get("time"):
                    last_latency = data
        print(data) if args.verbose else False
    spinner.succeed(f'[Done] Finding fastest region')

    return last_latency

def getMyip():
    url = 'https://ifconfig.co/ip'
    return getTime(url).get("text").strip()


def getTime(url, name="NULL"):
    status_code = 999
    try:
        response = requests.get(f'{url}', timeout=5)
        response_text = response.text
        time = response.elapsed.total_seconds()
        status_code = response.status_code
    except:
        time = None
        response_text = None
        cprint(f"getTime error : {url} -> {sys.exc_info()[0]}", "red")
    return {"url": url, "time": time, "name": name, "text": response_text, "status": status_code}


def catchMeIfYouCan(encoded_text):
    from cryptography.fernet import Fernet
    cipher_suite = Fernet(encode_key)
    decoded_text = cipher_suite.decrypt(encoded_text)
    kkk, sss = decoded_text.decode('utf-8').split(",")
    return kkk, sss


def multi_part_upload_with_s3(filename=None, key_path=None, bucket=None, upload_type="single"):
    start_time = default_timer()
    bucket_name_prefix = "prep-logs"
    key, sec = catchMeIfYouCan(aawwss_text)
    aaa_env, sss_env = catchMeIfYouCan(aawwss_env)
    os.environ[aaa_env] = key
    os.environ[sss_env] = sec
    if bucket is None or bucket == "":
        BUCKET_NAME = f"{bucket_name_prefix}-kr"
    else:
        BUCKET_NAME = f"{bucket_name_prefix}{bucket}"
    cprint(f"\t bucket {bucket} -> {BUCKET_NAME}") if args.verbose else False
    if bucket == "-hk":
        s3 = boto3.resource(
            's3',
            region_name="ap-east-1"
        )
    else:
        s3 = boto3.resource(
            's3',
        )
    ##single parts
    if upload_type == "single":
        s3.meta.client.meta.events.register('choose-signer.s3.*', disable_signing)
        # config = TransferConfig(use_threads=True, multipart_threshold=1024*1024*8, multipart_chunksize=1024*1024*8)
        config = TransferConfig(multipart_threshold=838860800, max_concurrency=10, multipart_chunksize=8388608,
                                num_download_attempts=5, max_io_queue=100, io_chunksize=262144, use_threads=True)
    # multiparts mode -> AWS S3 CLI: Anonymous users cannot initiate multipart uploads
    elif upload_type == "multi":
        pass
        config = TransferConfig(multipart_threshold=1024 * 25, max_concurrency=10,
                                multipart_chunksize=1024 * 25, use_threads=True)
    else:
        cprint(f"Unknown upload_type-> {upload_type}","red")
    if filename is None:
        cprint(f"[ERROR] filename is None", "red")
        raise SystemExit()
    if key_path is None:
        key_path = filename
    try:
        s3.meta.client.upload_file(filename, BUCKET_NAME, key_path,
                                   # ExtraArgs={'ACL': 'public-read', 'ContentType': 'text/pdf'},
                                   Config=config,
                                   Callback=ProgressPercentage(filename)
                                   )
    except Exception as e:
        e = str(e).replace(":", ":\n")
        cprint(f"\n[ERROR] File upload fail / cause->{e}\n","red")
        raise SystemExit()

    elapsed = default_timer() - start_time
    time_completed_at = "{:5.3f}s".format(elapsed)

    cprint(f"\n\t time_completed_at = {time_completed_at}")


class ProgressPercentage(object):
    def __init__(self, filename):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0
        self._lock = threading.Lock()
        self._prevent_bytes = 0

    def __call__(self, bytes_amount):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            # tx = bytes_amount - self._prevent_bytes
            sys.stdout.write(
                "\r \t %s  %s / %s  (%.2f%%) " % (
                    self._filename, self._seen_so_far, self._size,
                    percentage))
            sys.stdout.flush


def upload_s3(filename=None):
    s3 = boto3.client('s3')
    filename = 'data/dummy.file'
    s3.upload_file(filename, BUCKET_NAME, filename)


def sizeof_fmt(num, suffix='B'):
    for unit in ['','K','M','G','T','P','E','Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Y', suffix)


def dump(obj, nested_level=0, output=sys.stdout):
    class bcolors:
        HEADER = '\033[95m'
        OKBLUE = '\033[94m'
        OKGREEN = '\033[92m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'

    spacing = '   '
    def_spacing = '   '
    if type(obj) == dict:
        print ('%s{' % ( def_spacing + (nested_level) * spacing ))
        for k, v in obj.items():
            if hasattr(v, '__iter__'):
                print ( bcolors.OKGREEN + '%s%s:' % (def_spacing +(nested_level + 1) * spacing, k) + bcolors.ENDC, end="")
                dump(v, nested_level + 1, output)
            else:
                print ( bcolors.OKGREEN + '%s%s:' % (def_spacing + (nested_level + 1) * spacing, k) + bcolors.WARNING + ' %s' % v + bcolors.ENDC, file=output)
        print ('%s}' % ( def_spacing + nested_level * spacing), file=output)
    elif type(obj) == list:
        print  ('%s[' % (def_spacing+ (nested_level) * spacing), file=output)
        for v in obj:
            if hasattr(v, '__iter__'):
                dump(v, nested_level + 1, output)
            else:
                print ( bcolors.WARNING + '%s%s' % ( def_spacing + (nested_level + 1) * spacing, v) + bcolors.ENDC, file=output)
        print ('%s]' % ( def_spacing + (nested_level) * spacing), file=output)
    else:
        print (bcolors.WARNING + '%s%s' %  ( def_spacing + nested_level * spacing, obj) + bcolors.ENDC)


def classdump(obj):
    class bcolors:
        HEADER = '\033[95m'
        OKBLUE = '\033[94m'
        OKGREEN = '\033[92m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'

    for attr in dir(obj):

        if hasattr( obj, attr ):
            # print(bcolors.OKGREEN + "obj.%s = "+bcolors.WARNING + "%s" + bcolors.ENDC %
            #       (attr, getattr(obj, attr)))
            value = getattr(obj, attr)
            print(bcolors.OKGREEN + f"obj.{attr} = " +
                  bcolors.WARNING + f"{value}" + bcolors.ENDC)


def checkFileType(filename):
    if os.path.isdir(filename):
        return "dir"
    elif os.path.isfile:
        return "file"


class SearchDir:
    if os.environ.get("IS_DOCKER") == "true":
        guess_logpath = ["/data/mainnet/log", "/data/loopchain/log"]
    else:
        guess_logpath = ["data/mainnet/log", "data/loopchain/log"]

    dirname = "data"
    type = "dir"
    change_path = False
    exclude_dir = [".score_data", ".storage", ".git"]
    # def __init__(self, dirname, type, return_data=[]):
    #     self.dirname = dirname
    def __init__(self,  return_data=[]):
        self.return_data = []

    def setExcludePath(self,path):
        if type(path) == list:
            SearchDir.exclude_dir = path
        else:
            SearchDir.exclude_dir = [path]
        return self

    def setPath(self, path):
        if type(path) == list:
            SearchDir.guess_logpath = path
        else:
            SearchDir.guess_logpath = [path]
        self.dirname = path
        self.change_path = True
        return self

    def setType(self, type):
        self.type = type
        return self

    def add(self, tree):
        return self.return_data.append(tree)

    def merge(self, tree):
        return self.return_data.extend(tree)

    def find(self):
        try:
            filenames = os.listdir(self.dirname)
        except Exception as e:
            filenames = None
            cprint(f"Error: '{self.dirname}' - {e}", "red")
            raise SystemExit()

        if filenames:
            for filename in filenames:
                is_write = 0
                full_filename = os.path.join(self.dirname, filename)
                file_info = getFileInfo(full_filename)
                if file_info.get("type") is "dir":
                    exclude_match = False
                    for exclude in self.exclude_dir:
                        if filename.count(exclude) > 0: # not match
                            exclude_match = True
                        if exclude_match is True:
                            break
                    if exclude_match is False:
                        self.merge(SearchDir(self.return_data).setType(self.type).setPath(full_filename).find())
                if file_info.get("type") == "dir" and self.type is "dir":
                    if full_filename in self.guess_logpath:
                        is_write = 1
                elif file_info.get("type") == "file" and self.type is "file":
                    is_write = 1
                if is_write == 1:
                    self.add({
                        "full_filename": full_filename,
                        "size": file_info.get("size"),
                        "date": file_info.get("date"),
                        "unixtime": file_info.get("unixtime"),
                        "type": file_info.get("type")
                    })
        return self.return_data


def getFileInfo(file):
    if os.path.isdir(file):
        file_type = "dir"
    elif os.path.isfile(file):
        file_type = "file"
    try:
        file_info = os.stat(file)
        return_result = {
            "full_filename" : file,
            "size" :sizeof_fmt(file_info.st_size),
            "date" : datetime.datetime.fromtimestamp(file_info.st_mtime),
            "unixtime" : file_info.st_mtime,
            "type": file_type
        }
    except:
        return_result = {
            "full_filename" : file,
            "size": None,
            "date": None,
            "unixtime": None,
            "type": None
        }

    return return_result


def archive_zip(directory=None, filename=None):
    if directory and filename:
        zip = zipfile.ZipFile('archive.zip', 'w')
        for folder, subfolders, files in os.walk(directory):
            for file in files:
                print(file)
                zip.write(os.path.join(folder, file),
                          os.path.relpath(os.path.join(folder, file), directory),
                          compress_type = zipfile.ZIP_DEFLATED)

def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))


def archive_zip2(filelist=[], zip_filename="archive.zip"):

    zip = zipfile.ZipFile(f'{zip_filename}', 'w')

    spinner = Halo(text=f"Archive files - {zip_filename}\n", spinner='dots')
    spinner.start()
    for filename in filelist:
        try:
            print(f" -> {filename}")
            zip.write(filename,
                  os.path.relpath(filename),
                  compress_type=zipfile.ZIP_DEFLATED)
        except Exception as e:
            cprint(f"[ERR] {e}")
            spinner.fail(f'Fail {e}')
    spinner.succeed(f'Archive Done')


def sorted_key(list, key, reverse=True):
    return sorted(list, key=lambda x: x[key], reverse=reverse)


def extractKeyToList(listObj, key):
    return_list = []
    for idx, value in enumerate(listObj):
        return_list.append(value.get(key))

    return return_list

def get_parser():
    ## TODO get hostname, public-ip -> bucketname = {hostname}_{public-ip} ,
    ## TODO find a fastest region -> multi bucket -> replication
    parser = argparse.ArgumentParser(description='Send me log')

    parser.add_argument('-f', '--find',  action='count', help=f'Find fastest region, just checking', default=0)
    parser.add_argument('--network', type=str, help=f'Network name', choices=["MainNet", "TestNet"], default="MainNet")
    parser.add_argument('-d', '--log-dir', metavar='log-dir', type=str, help=f'log directory location', default=None)
    parser.add_argument('--static-dir', metavar='static-dir', type=str, nargs="+",  help=f'include log directory location', default=None)

    parser.add_argument('--include-dir', metavar='include-dir', type=str, nargs="+",  help=f'include log directory location', default=None)
    parser.add_argument('--exclude-dir', metavar='exclude-dir', type=str, nargs="+",  help=f'exclude log directory location', default=None)

    parser.add_argument('--remove', metavar='remove', type=str, help=f'remove option', default=True)

    parser.add_argument('-td', '--target-date',  type=str, choices=["all", "today"], help=f'upload target date', default=f'today')
    parser.add_argument('-n', '--name',  type=str, help=f'Set filename for upload ', default=None)
    parser.add_argument('-u', '--upload', action='count', help=f'force upload mode', default=0)
    parser.add_argument('-uf', '--upload-filename', type=str, help=f'upload upload mode', default=0)
    parser.add_argument('-ut', '--upload-type',  type=str, help=f'upload type',choices=["single", "multi"], default="multi")
    parser.add_argument('-v', '--verbose', action='count', help=f'verbose mode ', default=0)
    parser.add_argument('-r', '--region', metavar="region", type=str, help=f'region ', default=None)
    return parser


def main():
    global upload_filename
    upload_filename=None
    if args.find:
        dump(findFastestRegion())
        raise SystemExit()

    if args.log_dir:
        if checkFileType(args.log_dir) == "dir":
            latest_log_dir = args.log_dir
            latest_log_modify = getFileInfo(args.log_dir).get("date")
        else:
            cprint(f"[ERROR] '{args.log_dir}' is not directory","red")
            raise SystemExit()
        if args.include_dir:
            log_dir = sorted_key(SearchDir().setExcludePath(exclude_dir).setType("dir").find(), "unixtime")
    else:
        log_dir = sorted_key(SearchDir().setExcludePath(exclude_dir).setType("dir").find(), "unixtime")
        # dump(log_dir)
        try:
            latest_log_dir = log_dir[0].get("full_filename")
            latest_log_modify = log_dir[0].get("date")
        except:
            print("[ERROR] Cannot find log directory")
            dump(log_dir)
            raise SystemExit()

    logfiles=SearchDir().setType("file").setPath(latest_log_dir).find()

    kvPrint("Your log directory", f'{latest_log_dir} \t\t[{latest_log_modify}]')
    kvPrint("Target date", args.target_date)
    kvPrint("Excluding directory", exclude_dir)
    cprint(f"\n---------- Found log files ({args.target_date})  ----------", "white")

    today = datetime.datetime.today().strftime("%Y-%m-%d")
    today_time = datetime.datetime.today().strftime("%Y%m%d_%H%M%S")

    target_filenames = []
    file_count = 0

    for k, file in enumerate(logfiles):
        date = file['date'].strftime("%Y-%m-%d")
        diff_date = datetime.datetime.strptime(
            today, "%Y-%m-%d") - datetime.datetime.strptime(date, "%Y-%m-%d")

        exclude_match = False
        for exclude in exclude_dir:
            if file['full_filename'].count(exclude) > 0: # not match
                exclude_match = True
            if exclude_match is True:
                break

        if exclude_match is False:
            if args.target_date == "today":
                # if today == date:
                if diff_date.days <= 1:
                    file_count = file_count + 1
                    target_filenames.append(file['full_filename'])
                    print(
                        f"[{file_count}] today :: {file['full_filename']:40}  {file['size']:10} {file['date']} ({diff_date.days})")
            else:
                file_count = file_count + 1
                target_filenames.append(file['full_filename'])
                print(
                    f"[{file_count}] all :: {file['full_filename']:70}  {file['size']:10} {file['date']} ({diff_date.days})")

    cprint("---------------------------------------------\n", "white")
    if len(target_filenames) == 0:
        cprint(f"File not found", "red")
        raise SystemExit()
    if args.name:
        name = args.name
    else:
        name = input("Enter your prep-name: ")

    name = str(name).replace(' ', '_')

    myip = getMyip()
    if len(myip) > 50: #TODO ip 가져올때 예외 처리 하기
        myip = "NULL"

    upload_filename = f"{name}-{myip}-{today_time}.zip"

    if len(name) == 0:
        cprint(f'[ERR] need a your prep-node name',"red")
        raise SystemExit()
    elif any( string in name for string in "^{}?,`!@#$%^&*();:'\""):
        cprint(f'[ERR] Can\'t using special character ( allowed : [ ] < > _ )',"red")
        raise SystemExit()

    # if args.static_dir:
    #     cprint(f"static_mode={args.static_dir}")
    #     target_filenames = args.static_dir
    #     target_filenames = sorted_key(SearchDir().setPath(args.dir).setExcludePath(exclude_dir).setType("dir").find(), "unixtime")
    #

    if args.static_dir:
        dir_string = ""
        for dir in args.static_dir:
            dir_string = f"{dir_string} {dir}"
        cmd = f'tar -I pigz -cvf {upload_filename} {dir_string}'
        print(f'cmd = {cmd}')
        os.system(f'{cmd}')
    elif args.upload_filename:
        upload_filename = args.upload_filename
    else:
        archive_zip2(target_filenames, f"{upload_filename}")

    # upload_filesize = sizeof_fmt(os.stat(upload_filename).st_size)
    upload_filesize = getFileInfo(upload_filename).get("size")
    cprint(f'>> upload target: {args.network}/{upload_filename}, size: {upload_filesize}')

    if args.upload:
        answer = "y"
    else:
        answer = input("\n Are you going to upload it? It will be send to ICONLOOP's S3 (y/n)")

    if answer == "y":
        if args.region:
            cprint(f"region => {args.region}", "green")
            region = {'url': f'https://icon-leveldb-backup.{region_info.get(args.region)}.amazonaws.com/route_check', 'time': 0, 'name': args.region,
             'text': 'OK\n', 'status': 200}
        else:
            region = findFastestRegion()

        bucket_code = (region_info.get( region.get("name")).split("."))[0]
        cprint(f'[OK] Fastest region -> {region.get("name")}', "green")
        kvPrint(f'bucket_code', bucket_code) if args.verbose else False
        multi_part_upload_with_s3(f"{upload_filename}", f"{args.network}/{upload_filename}", bucket_code, args.upload_type)
        cprint(f"\n[OK] File uploaded successfully", "green")
    else:
        cprint(f"\n Stopped", "red")

def banner():
    print("="*57)
    print(' _____ _____ _____ ____  _____ _____    __    _____ _____')
    print('|   __|   __|   | |    \|     |   __|  |  |  |     |   __|')
    print('|__   |   __| | | |  |  | | | |   __|  |  |__|  |  |  |  |')
    print('|_____|_____|_|___|____/|_|_|_|_____|  |_____|_____|_____|')

    print("")
    print("\t\t\t\t   by JINWOO")
    print("="*57)


# for i in range( 1, 10000000):
#     ProgressPercentage("data/loopchain/log/dummy.file").__call__(i)
# raise SystemExit

if __name__ == '__main__':
    global args, exclude_dir, encode_key, aawwss_text, aawwss_env
    encode_key = b"ZhiS-yXbkk_KPbGkqIw85FX2aHRhSBrG-yVOQiTiZeg="
    aawwss_text = b"gAAAAABeIXCBukgBLiLfCPt8xD-zWLHxc6OfMfmZjsR02mY0CGYA_3mdevoURb_BRs_19nQdUEDNEpNag9xawP9m7Ug1CWNKDdha5_2J36AL9CG-I9" \
                  b"-9wHaUGD1GUuDfdxitfLcebKMtcy9VGDqr8A8vrYLeEb8NDQ== "
    aawwss_env = b"gAAAAABeIXy9YdGvJCmmxbBTnsbb-APE1RCKiYvciOYXMU-EXrXhjlvg6XJgb38MyY0cRzMM3TfiIyXrNbDTntA7R9cY_" \
                 b"EWuSuCcdK9LlnKVuL2qc_ITkVMQ5lgl-gNcgKCrqQS7xMTB"
    parser = get_parser()
    args = parser.parse_args()

    exclude_dir = [".score_data", ".storage", ".git"]
    banner()

    if args.include_dir is not None:
        print(args.include_dir)
        exclude_dir = list(set(exclude_dir) - set(args.include_dir))

    if args.exclude_dir is not None:
        exclude_dir = list(set(exclude_dir + args.exclude_dir))

    # print(f"exclude_dir = {exclude_dir}")

    try:
        main()
    except KeyboardInterrupt:
        cprint("\nKeyboardInterrupt","green")
        pass
    finally:
        if upload_filename is not None and os.path.isfile(upload_filename) and args.remove:
            print(f'Remove temporary zip file -> {upload_filename}')
            os.remove(upload_filename)


    # upload_s3()
