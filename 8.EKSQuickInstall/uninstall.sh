#!/bin/bash
echo -n "是否确认删除集群，选择 y 将开始删除 ${CLUSTER_NAME} 集群！！！ (y/n): "
read input
input_lower=$(echo "$input" | tr '[:upper:]' '[:lower:]')
if [ "$input_lower" = "y" ]; then
    helm uninstall prometheus -n monitoring
    STACKS=(
        "eksctl-${CLUSTER_NAME}-addon-iamserviceaccount-kube-system-efs-csi-controller-sa"
        "eksctl-${CLUSTER_NAME}-addon-iamserviceaccount-kube-system-ebs-csi-controller-sa"
        "eksctl-${CLUSTER_NAME}-addon-iamserviceaccount-karpenter-karpenter"
        "eksctl-${CLUSTER_NAME}-addon-iamserviceaccount-kube-system-aws-load-balancer-controller"
        "eksctl-${CLUSTER_NAME}-addon-vpc-cni"
        "Karpenter-${CLUSTER_NAME}"
        "eksctl-${CLUSTER_NAME}-nodegroup-${ADDON_NODEGROUP_NAME}"
        "eksctl-${CLUSTER_NAME}-cluster"
    )
    for s in "${STACKS[@]}"; do
        echo "正在删除 $s"
        aws cloudformation delete-stack --stack-name $s --region ${REGION} --no-cli-pager
        aws cloudformation wait stack-delete-complete --stack-name $s --region ${REGION}
        echo "堆栈 $s 已成功删除"
    done
fi

# TODO: Termitate EC2 launched by Karpenter
