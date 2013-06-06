#!/bin/bash

# Usage: test.sh openstack keystone
# Note: you can clone from a local file with REPO_ROOT=file:////~/path/to/repo
set -x
set -e
REPO_ROOT=${REPO_ROOT:-https://review.openstack.org/p}
if [[ -z "$2" ]]; then
    org=openstack
    project=nova
else
    org=$1
    project=$2
fi
git clone $REPO_ROOT/$org/$project --depth=1
cd $project
set +e
flake8 --select H --statistics
cd ..
rm -rf $project
