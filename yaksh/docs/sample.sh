#!/bin/bash
[[ $# -eq 2 ]] && echo $(( $1 + $2 )) && exit $(( $1 + $2 ))
