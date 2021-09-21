#!/bin/bash

POP=$1
EMU=$2

pkill -9 -f tier2-0.0.1-SNAPSHOT
pkill -9 -f tier1-0.0.1-SNAPSHOT
pkill -9 -f client-0.0.1-SNAPSHOT

java -jar ../tier2/target/tier2-0.0.1-SNAPSHOT-jar-with-dependencies.jar --cpuEmu $EMU &
java -jar ../tier1/target/tier1-0.0.1-SNAPSHOT-jar-with-dependencies.jar --cpuEmu $EMU &
java -jar ../client/target/client-0.0.1-SNAPSHOT-jar-with-dependencies.jar --initPop $POP

