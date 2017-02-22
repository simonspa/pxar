#!/bin/sh

for v in 15 18 18
do
    for c in 3 3 6
    do
        echo 'Starting error finder for $v kV and $c mA'
        python ErrorFinder.py -d $1 -v $v -c $c
    done
done
