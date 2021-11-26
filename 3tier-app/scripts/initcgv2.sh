#!/bin/bash

sudo su
cd /sys/fs/group
echo "+cpu" > cgroup.subtree_control
cat cgroup.subtree_control
mkdir t1
cd  ./t1
echo "+cpu" > cgroup.subtree_control
cat cgroup.subtree_control
mkdir t1/e1
cd  ./e1
echo "+cpu" > cgroup.subtree_control
cat cgroup.subtree_control
echo "threaded" > cgroup.type
cat cgroup.type
mkdir t2
cd  ./t2
echo "+cpu" > cgroup.subtree_control
mkdir t2/e2
cd  ./e2
echo "+cpu" > cgroup.subtree_control
cat cgroup.subtree_control
echo "threaded" > cgroup.type
cat cgroup.type