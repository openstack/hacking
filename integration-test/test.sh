#!/bin/bash

# Usage: test.sh openstack keystone
# Note: you can clone from a local file with REPO_ROOT=file:////~/path/to/repo
set -x
set -e

REPO_ROOT=${REPO_ROOT:-git://git.openstack.org}
if [[ -z "$2" ]]; then
    org=openstack
    project=nova
else
    org=$1
    project=$2
fi

tempdir="$(mktemp -d)"

pushd $tempdir
    if [[ $REPO_ROOT  == file://* ]]; then
        git clone $REPO_ROOT/$org/$project
    else
        git clone $REPO_ROOT/$org/$project --depth=1
    fi

    pushd $project
        set +e
        flake8 --select H --statistics
    popd
popd

rm -rf $tempdir
