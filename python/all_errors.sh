#!/bin/sh

voltages=(15 18 18)
currents=(3 3 6)
for ((i=0;i<${#voltages[@]};++i)); do
    v=${voltages[i]}
    c=${currents[i]}
    echo Starting error finder for ${v} kV and ${c} mA
    python ErrorFinder.py -d $1 -vv ${v} -c ${c} -T 80
done
