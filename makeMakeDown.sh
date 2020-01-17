#!/bin/sh
today=$(date +"%Y-%m-%d %T")
cp README_HEADER.md README_HEADER_TMP.md
IMAGE_NAMES="jtools"
for image in $IMAGE_NAMES
do
    echo "## $image docker setting" >README_TAIL.md
    echo "###### made date at $today " >>README_TAIL.md

    echo '## Included files' >>README_TAIL.md
    echo '### python libs' >>README_TAIL.md
    echo '```' >>README_TAIL.md
    cat src/requirements.txt >> README_TAIL.md
    echo '```' >>README_TAIL.md

    echo '### static_version_info.json' >>README_TAIL.md
    echo 'static_version_info.json' >>README_TAIL.md
    echo '```' >>README_TAIL.md
    cat src/static_version_info.json | jq >> README_TAIL.md
    echo '```' >>README_TAIL.md


done

cat README_HEADER_TMP.md  > README.md
echo "" >> README.md
cat README_TAIL.md  >> README.md

rm -f text1 text2 text3 text4 README_HEADER_TMP.md README_TAIL.md