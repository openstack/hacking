#!/bin/bash

# Usage: test.sh openstack keystone path-to-repo
# path-to-repo is an optional parameter, if it exists
# no cloning will happen and the local directory will be used,
# the first two parameter get ignored.
# Note: you can clone from a local file with REPO_ROOT=file:////~/path/to/repo

set -x
set -e

REPO_ROOT=${REPO_ROOT:-https://git.openstack.org}
HACKING="$(pwd)"

if [[ $# -lt 2 ]] ; then
    echo "Script needs at least two arguments:"
    echo "$0 organization name [path-to-repo]"
    exit 1
fi
org=$1
project=$2

if [[ $# -eq 3 ]] ; then
    projectdir=$3
    clone=0
else
    projectdir=$project
    clone=1
fi

if [ "$clone" = "1" ] ; then

    tempdir="$(mktemp -d)"

    trap "rm -rf $tempdir" EXIT
    pushd $tempdir
    git clone $REPO_ROOT/$org/$project --depth=1
fi

pushd $projectdir
set +e

# Install project with test-requirements so that hacking's
# local-check-factory works
pip install -r test-requirements.txt
pip install .
# Reinstall hacking, the above might have uninstalled it
pip install $HACKING

flake8 --select H --statistics
RET=$?
popd

if [ "$clone" = "1" ] ; then
    popd
fi

exit $RET
