#!/usr/bin/env bash

# Linux
wget -qO- https://binaries.cockroachdb.com/cockroach-v19.1.1.linux-amd64.tgz | tar  xvz
cp -i cockroach-v19.1.1.linux-amd64/cockroach ./track/distributed/cockroach/cockroach_linux
rm -rf cockroach-v19.1.1.linux-amd64

# Mac OS
# curl https://binaries.cockroachdb.com/cockroach-v19.1.1.darwin-10.9-amd64.tgz | tar -xJ
# cp -i cockroach-v19.1.1.darwin-10.9-amd64/cockroach ./track/distributed/cockroach/cockroach_macos
