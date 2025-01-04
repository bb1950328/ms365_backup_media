#!/usr/bin/env bash

rsync -Pa "data_current" "backup_$(date +'%Y_%m_%d_%H_%M')"
