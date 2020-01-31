# jtools

A tool for managing PRep Node resources as docker container

#### Latest docker tag
[![latest tag](https://images.microbadger.com/badges/version/jinwoo/jtools.svg)](https://microbadger.com/images/jinwoo/jtools "microbadger.com")
[![tag info](https://images.microbadger.com/badges/image/jinwoo/jtools.svg)](https://microbadger.com/images/jinwoo/jtools "microbadger.com")


#### Travis-build
[![Master Build Status](https://travis-ci.org/JINWOO-J/jtools.svg?branch=master)](https://travis-ci.org/JINWOO-J/jtools) 
[![Build History](https://buildstats.info/travisci/chart/jinwoo-j/jtools?branch=master&includeBuildsFromPullRequest=false&buildCount=30)](https://travis-ci.org/jinwoo-j/jtools)

## What's jtools

We've made it easy to use on a docker basis.

jinwoo/jtools -> Docker image with basic tools.

jinwoo/jtools-builder -> Docker image to create a prep-node

This tool includes:

### sendme_log.py

This is a script that can get the log quickly.


### static_builder.py

This script creates a whl file that configures a prep node.

Write json that contains the revision of the package to build as below

```json
static_version_info.json

{

    "iconcommons": {
        "url": "https://github.com/icon-project/icon-commons",
        "revision": "v.1.1.2"
    },
    "earlgrey": {
        "url": "https://github.com/icon-project/earlgrey",
        "revision": "bbca2974a2604e0a7f33341ed3fe7510bb6f4f90"
    },
    "loopchain" : {
        "url": "https://github.com/icon-project/loopchain",
        "revision": "2.4.16"
    },
    "iconservice": {
        "url": "https://github.com/icon-project/icon-service",
        "revision": "v1.5.18"
    },
    "iconrpcserver": {
        "url": "https://github.com/icon-project/icon-rpc-server",
        "revision": "1.4.6"
    },
    "icon_rc": {
        "url": "https://github.com/icon-project/rewardcalculator",
        "revision": "v1.1.3"
    }
}
```

The build directory should contain `static_version_info.json`,
The `whl` file is created in` build / output`.

```
$ docker run -it -v ${PWD}/build:/build jinwoo/jtools-builder stastic_builder.py  
 iconcommons ,  https://github.com/icon-project/icon-commons , v.1.1.2

Repository Name : iconcommons
✔ [DONE] [git clone] iconcommons  / git clone --quiet -n https://github.com/icon-project/icon-commons /build/iconcommons  -> 2.516sec

2019-08-22 17:52:55 7329ff1f983e569844ae55451e7a0f66996ed3ac  - (HEAD -> v.1.1.2, tag: v1.1.2, tag: v.1.1.2, origin/master, origin/HEAD, master)  Merge pull request #12 from icon-project/develop (3 months ago) <BOBO>
⠴ Build iconcommonsLooking in indexes: http://ftp.daumkakao.com/pypi/simple
⠦ Build iconcommons/usr/local/lib/python3.7/site-packages/setuptools/dist.py:481: UserWarning: The version specified ('v.1.1.2') is an invalid version, this may not work as expected with newer versions of setuptools, pip, and PyPI. Please see PEP 440 for more details.
  "details." % self.metadata.version
⠧ Build iconcommonsrunning bdist_wheel

                    .
                    .
                    .
                    .

	--- output files---
	 /build/output/earlgrey-0.0.4-py3-none-any.whl
	 /build/output/icon_rc
	 /build/output/iconservice-1.5.18-py3-none-any.whl
	 /build/output/iconrpcserver-1.4.6-py3-none-any.whl
	 /build/output/iconcommons-v.1.1.2-py3-none-any.whl
	 /build/output/loopchain-2.4.16-py3-none-any.whl
	 /build/output/rctool


```



## jtools docker setting
###### made date at 2020-01-03 14:50:02 
## Included files
### python libs
```
boto3==1.10.45
termcolor==1.1.0
halo==0.0.28
requests==2.20.0
iconsdk==1.2.0
preptools==1.0.2
python-hosts==0.4.7
grpcio==1.25.0
grpcio-tools==1.25.0
websocket-client==0.54.0
tbears
```
### static_version_info.json
static_version_info.json
```
{
  "iconcommons": {
    "url": "https://github.com/icon-project/icon-commons",
    "revision": "v1.1.2"
  },
  "earlgrey": {
    "url": "https://github.com/icon-project/earlgrey",
    "revision": "bbca2974a2604e0a7f33341ed3fe7510bb6f4f90"
  },
  "loopchain": {
    "url": "https://github.com/icon-project/loopchain",
    "revision": "2.4.20"
  },
  "iconservice": {
    "url": "https://github.com/icon-project/icon-service",
    "revision": "v1.5.20"
  },
  "iconrpcserver": {
    "url": "https://github.com/icon-project/icon-rpc-server",
    "revision": "1.4.9"
  },
  "icon_rc": {
    "url": "https://github.com/icon-project/rewardcalculator",
    "revision": "v1.2.0"
  }
}
```
