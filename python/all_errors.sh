#!/bin/sh

#voltages=(15 18 18 20 22 23 24 25 26 27 29 31 33 35 37 39)
voltages=( $(for i in {41..60..2}; do echo ${i}; done) )
voltages[50]=60
#currents=(3 3 6 7 8 9 10 11 12 13 14 15 16 17 18 19)
currents=( $(for i in {21..30}; do echo ${i}; done) )
for ((i=0;i<${#voltages[@]};++i)); do
    v=${voltages[i]}
    c=${currents[i]}
    echo Starting error finder for ${v} kV and ${c} mA
    python ErrorFinder.py -d $1 -vv ${v} -c ${c} -T 80 -s
done
