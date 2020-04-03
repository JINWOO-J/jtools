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
$ docker run -it -v ${PWD}/build:/build jinwoo/jtools-builder static_builder.py  
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

It is installed as a package based on network_info. (https://github.com/jinwoo-j/icon_network_info) <br>
If you set zicon as in the example below, it is downloaded from "https://networkinfo.solidwallet.io/conf/zicon.json".

```
$ docker run -it -v ${PWD}/build:/build jinwoo/jtools-builder static_builder.py  -c zicon  # mainnet, testnet, zicon ...

   {
      loopchain:      {
         url:         https://github.com/icon-project/loopchain
         revision:         2.5.2
      }
      iconservice:      {
         url:         https://github.com/icon-project/icon-service
         revision:         1.6.1
      }
      iconrpcserver:      {
         url:         https://github.com/icon-project/icon-rpc-server
         revision:         1.4.9
      }
      icon_rc:      {
         url:         https://github.com/icon-project/rewardcalculator
         revision:         v1.2.1
      }
   }

2020-04-01 17:30:20 eefc37cdb6b2fe181853746d1ad24fc44b8a9fc9  - (HEAD -> 1.6.1, tag: 1.6.1, origin/master, origin/HEAD, master)  Merge pull request #434 from icon-project/release-1.6.1 (2 days ago) <Chiwon Cho>
✔ [DONE] Build iconservice , work_path=/build/iconservice -> 0.002sec
✔ [DONE] Install python dependencies , pip3 install -q -r requirements.txt -> 0.715sec
⠏ Build a wheel filerunning bdist_wheel
                    .
                    .
                    .
                    .
	--- output files---
	 /build/output/loopchain-2.5.2-py3-none-any.whl
	 /build/output/iconservice-1.6.1-py3-none-any.whl
	 /build/output/iconrpcserver-1.4.9-py3-none-any.whl
	 /build/output/icon_rc
	 /build/output/rctool

```