#!/bin/bash
cat $1 | cut -d: -f2 | paste -d: $3 - $2
