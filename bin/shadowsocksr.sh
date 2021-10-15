#!/bin/ash
lol(){
i=`uci show shadowsocksr | grep shadowsocksr.@servers.*=servers | wc -l`
echo "Found $i servers:"
while [ $i -gt 0 ]
do
    i=$((i-1))
    echo "[$i]" `uci show shadowsocksr.@servers[$i].alias`
#    sleep 1
done
}
lol