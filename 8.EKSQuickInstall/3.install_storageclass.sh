#!/bin/bash

echo "[安装EBS storage class"]
if [ "$EBS_CSI_DRIVER" = "on" ]; then
    envsubst < ./templates/ebs-sc.yaml > ./${CLUSTER_NAME}/ebs-sc.yaml
    cat ./${CLUSTER_NAME}/ebs-sc.yaml
    echo
    echo -n "是否创建上述EBS storage class (y/n): "
    read input
    input_lower=$(echo "$input" | tr '[:upper:]' '[:lower:]')
    if [ "$input_lower" = "y" ]; then
        kubectl apply -f ./${CLUSTER_NAME}/ebs-sc.yaml
    else
        echo "跳过创建EBS storage class。"
    fi  
fi

echo "[安装EFS storage class]"
if [ "$EFS_CSI_DRIVER" = "on" ]; then
    envsubst < ./templates/efs-sc.yaml > ./${CLUSTER_NAME}/efs-sc.yaml
    cat ./${CLUSTER_NAME}/efs-sc.yaml
    echo
    echo -n "是否创建上述EFS storage class (y/n): "
    read input
    input_lower=$(echo "$input" | tr '[:upper:]' '[:lower:]')
    if [ "$input_lower" = "y" ]; then
        kubectl apply -f ./${CLUSTER_NAME}/efs-sc.yaml
    else
        echo "跳过创建EFS storage class。"
    fi    
fi


echo "[安装完毕，检查集群所有StorageClass]"
kubectl get sc -A