#!/bin/bash

echo "[安装托管节点组，用于部署管理组件]"
envsubst < ./templates/nodegroup-addon.yaml > ./${CLUSTER_NAME}/nodegroup-addon.yaml
cat ./${CLUSTER_NAME}/nodegroup-addon.yaml
echo
echo -n "是否创建上述托管节点组 (y/n): "
read input
input_lower=$(echo "$input" | tr '[:upper:]' '[:lower:]')
if [ "$input_lower" = "y" ]; then
    eksctl create nodegroup -f ./${CLUSTER_NAME}/nodegroup-addon.yaml
else
    echo "跳过创建托管节点组。"
fi
