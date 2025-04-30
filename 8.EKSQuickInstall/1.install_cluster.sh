#!/bin/bash

echo -n "开始创建集群，选择 y 将开始创建本地目录${CLUSTER_NAME}，用于存放所有定义文件。如果目录已经存在，请注意备份！！！ (y/n): "
read input
input_lower=$(echo "$input" | tr '[:upper:]' '[:lower:]')
if [ "$input_lower" = "n" ]; then
    exit
fi
mkdir -p ${CLUSTER_NAME}
echo

echo "[创建集群]"
envsubst < ./templates/cluster.yaml > ./${CLUSTER_NAME}/cluster.yaml
cat ./${CLUSTER_NAME}/cluster.yaml
echo
echo -n "是否创建上述集群 (y/n): "
read input
input_lower=$(echo "$input" | tr '[:upper:]' '[:lower:]')
if [ "$input_lower" = "y" ]; then
    eksctl create cluster -f ./${CLUSTER_NAME}/cluster.yaml
else
    echo "跳过创建集群。"
fi
eksctl utils write-kubeconfig --cluster ${CLUSTER_NAME} --region ${REGION}
echo

if [ "AWS_VPC_K8S_CNI_CUSTOM_NETWORK_CFG" = "true" ]; then
    echo "[更改Pod所属子网]"
    export SHAREDNODE_SG=$(aws cloudformation describe-stacks --stack-name eksctl-${CLUSTER_NAME}-cluster --region ${REGION} \
        --query 'Stacks[0].Outputs[?OutputKey==`SharedNodeSecurityGroup`].OutputValue' --output text --no-cli-pager)
    export CLUSTER_SG=$(aws cloudformation describe-stacks --stack-nameeksctl-${CLUSTER_NAME}-cluster --region ${REGION} \
        --query 'Stacks[0].Outputs[?OutputKey==`ClusterSecurityGroupId`].OutputValue' --output text --no-cli-pager)
    envsubst < ./templates/eniconfig.yaml > ./${CLUSTER_NAME}/eniconfig.yaml
    echo
    echo -n "是否创建上述ENI Config (y/n): "
    read input
    input_lower=$(echo "$input" | tr '[:upper:]' '[:lower:]')
    if [ "$input_lower" = "y" ]; then
        kubectl apply -f ./${CLUSTER_NAME}/eniconfig.yaml
        kubectl patch daemonset aws-node \
          -n kube-system \
          -p '{"spec": {"template": {"spec": {"initContainers": [{"env":[{"name":"DISABLE_TCP_EARLY_DEMUX","value":"true"}],"name":"aws-vpc-cni-init"}]}}}}'
    fi
fi