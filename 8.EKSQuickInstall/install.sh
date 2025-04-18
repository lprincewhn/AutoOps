#!/bin/bash

echo "[检查子网IP数量和标签]"
QUERY="Subnets[*].{SubnetId:SubnetId,Name:Tags[?Key==\`Name\`].Value|[0],CIDR:CidrBlock,AvailableIPs:AvailableIpAddressCount,kubernetes_io_cluster_$CLUSTER_NAME:Tags[?Key==\`kubernetes.io/cluster/$CLUSTER_NAME\`].Value|[0],kubernetes_io_role_elb:Tags[?Key==\`kubernetes.io/role/elb\`].Value|[0],kubernetes_io_role_internal_elb:Tags[?Key==\`kubernetes.io/role/internal-elb\`].Value|[0]}"
echo "*包含kubernetes.io/cluster/$CLUSTER_NAME标签的子网:"
aws ec2 describe-subnets \
  --filters "Name=tag-key,Values=kubernetes.io/cluster/$CLUSTER_NAME" \
  --query $QUERY --region ${REGION} --no-cli-pager --output table
echo "*将在以下子网创建集群："
aws ec2 describe-subnets \
  --subnet-ids ${PRIVATE_SUBNET1_ID} ${PRIVATE_SUBNET2_ID} ${PRIVATE_SUBNET3_ID} \
  --query $QUERY --region ${REGION} --no-cli-pager --output table
echo
echo -n "是否继续创建集群，选择 y 将开始创建本地目录${CLUSTER_NAME}，用于存放所有定义文件。如果目录已经存在，请注意备份！！！ (y/n): "
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

echo "[安装ebs-csi-driver"]
if [ "$EBS_CSI_DRIVER" = "on" ]; then
    echo -n "是否使用AWS托管策略AmazonEBSCSIDriverPolicy创建角色 ${CLUSTER_NAME}-ebs-csi-role (y/n): "
    read input
    input_lower=$(echo "$input" | tr '[:upper:]' '[:lower:]')
    if [ "$input_lower" = "y" ]; then
        eksctl create iamserviceaccount --name ebs-csi-controller-sa --namespace kube-system --cluster ${CLUSTER_NAME} --region ${REGION} \
            --role-name ${CLUSTER_NAME}-ebs-csi-role \
            --attach-policy-arn arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy \
            --role-only --approve
        echo
    else
        echo "跳过创建ebs-csi-driver角色。"
    fi
    envsubst < ./templates/ebs-csi-driver-helm-values.yaml > ./${CLUSTER_NAME}/ebs-csi-driver-helm-values.yaml
    cat ./${CLUSTER_NAME}/ebs-csi-driver-helm-values.yaml
    echo
    echo -n "是否使用以上参数安装/更新ebs-csi-driver (y/n): "
    read input
    input_lower=$(echo "$input" | tr '[:upper:]' '[:lower:]')
    if [ "$input_lower" = "y" ]; then
        helm repo add aws-ebs-csi-driver https://kubernetes-sigs.github.io/aws-ebs-csi-driver && helm repo update aws-ebs-csi-driver
        helm upgrade --install aws-ebs-csi-driver \
            --version "${EBS_CSI_DRIVER_CHART_VERSION}" --namespace kube-system \
            aws-ebs-csi-driver/aws-ebs-csi-driver \
            -f ./${CLUSTER_NAME}/ebs-csi-driver-helm-values.yaml
        echo "安装完毕，检查pod和sa状态"
        kubectl get all -n kube-system | grep ebs-csi
        kubectl describe sa ebs-csi-controller-sa -n kube-system
    else
        echo "跳过安装ebs-csi-driver。"
    fi
    echo
fi

echo "[安装efs-csi-driver]"
if [ "$EFS_CSI_DRIVER" = "on" ]; then
    cat ./templates/efs-csi-driver-iam-policy-v"${EFS_CSI_DRIVER_VERSION}".json
    echo
    echo -n "是否创建上述策略并用该策略创建角色 ${CLUSTER_NAME}-efs-csi-role (y/n): "
    read input
    input_lower=$(echo "$input" | tr '[:upper:]' '[:lower:]')
    if [ "$input_lower" = "y" ]; then
        aws iam create-policy \
            --policy-name EKS_EFS_CSI_Driver_Policy \
            --policy-document file://./templates/efs-csi-driver-iam-policy-v"${EFS_CSI_DRIVER_VERSION}".json
        eksctl create iamserviceaccount --name efs-csi-controller-sa --namespace kube-system --cluster ${CLUSTER_NAME} --region ${REGION} \
            --role-name ${CLUSTER_NAME}-efs-csi-role \
            --attach-policy-arn arn:aws:iam::${AWS_ACCOUNT_ID}:policy/EKS_EFS_CSI_Driver_Policy \
            --role-only --approve
    else
        echo "跳过创建efs-csi-driver策略和角色。"
    fi
    envsubst < ./templates/efs-csi-driver-helm-values.yaml > ./${CLUSTER_NAME}/efs-csi-driver-helm-values.yaml
    cat ./${CLUSTER_NAME}/efs-csi-driver-helm-values.yaml
    echo
    echo -n "是否使用以上参数安装/更新efs-csi-driver (y/n): "
    read input
    input_lower=$(echo "$input" | tr '[:upper:]' '[:lower:]')
    if [ "$input_lower" = "y" ]; then
        helm repo add aws-efs-csi-driver https://kubernetes-sigs.github.io/aws-efs-csi-driver && helm repo update aws-efs-csi-driver
        helm upgrade --install aws-efs-csi-driver \
            --version "${EFS_CSI_DRIVER_CHART_VERSION}" --namespace kube-system \
            aws-efs-csi-driver/aws-efs-csi-driver \
            -f ./${CLUSTER_NAME}/efs-csi-driver-helm-values.yaml
        echo "安装完毕，检查pod和sa状态"
        kubectl get all -n kube-system | grep efs-csi
        kubectl describe sa efs-csi-controller-sa -n kube-system
    else
        echo "跳过安装efs-csi-driver。"
    fi
    echo
fi

echo "[安装karpenter]"
if [ "$KARPENTER" = "on" ]; then
    cat templates/karpenter-cloudformation-v${KARPENTER_VERSION}.yaml
    echo
    echo -n "是否创建上述Karpenter所需AWS组件，包括节点角色，节点事件规则和队列 (y/n): "
    read input
    input_lower=$(echo "$input" | tr '[:upper:]' '[:lower:]')
    if [ "$input_lower" = "y" ]; then
        aws cloudformation deploy \
            --stack-name "Karpenter-${CLUSTER_NAME}" \
            --template-file "templates/karpenter-cloudformation-v${KARPENTER_VERSION}.yaml" \
            --capabilities CAPABILITY_NAMED_IAM \
            --parameter-overrides "ClusterName=${CLUSTER_NAME}"
        eksctl create iamidentitymapping --cluster ${CLUSTER_NAME} --group system:bootstrappers,system:nodes \
            --username system:node:{{EC2PrivateDNSName}} \
            --arn arn:aws:iam::${AWS_ACCOUNT_ID}:role/KarpenterNodeRole-${CLUSTER_NAME}
        eksctl create iamserviceaccount --name karpenter --namespace karpenter --cluster ${CLUSTER_NAME} --region ${REGION} \
            --role-name ${CLUSTER_NAME}-karpenter \
            --attach-policy-arn arn:aws:iam::${AWS_ACCOUNT_ID}:policy/KarpenterControllerPolicy-${CLUSTER_NAME} \
            --role-only --approve
    else
        echo "跳过创建Karpenter所需AWS组件。"
    fi
    envsubst < ./templates/karpenter-helm-values.yaml > ./${CLUSTER_NAME}/karpenter-helm-values.yaml
    cat ./${CLUSTER_NAME}/karpenter-helm-values.yaml
    echo
    echo -n "是否根据以上参数创建/更新Karpenter (y/n): "
    read input
    input_lower=$(echo "$input" | tr '[:upper:]' '[:lower:]')
    if [ "$input_lower" = "y" ]; then
        helm upgrade --install karpenter oci://public.ecr.aws/karpenter/karpenter \
            --version "v${KARPENTER_VERSION}" --namespace karpenter --create-namespace \
            -f ./${CLUSTER_NAME}/karpenter-helm-values.yaml
        echo "安装完毕，检查pod和sa状态"
        kubectl get all -n karpenter | grep karpenter
        kubectl describe sa karpenter -n karpenter
    else
        echo "跳过创建Karpenter。"
    fi
    echo
fi

echo "[安装ingress-nginx-controller"]
if [ "$INGRESS_NGINX_CONTROLLER" = "on" ]; then
    envsubst < ./templates/ingress-nginx-helm-values.yaml > ./${CLUSTER_NAME}/ingress-nginx-helm-values.yaml
    cat ./${CLUSTER_NAME}/ingress-nginx-helm-values.yaml
    echo
    echo -n "是否根据以上参数安装/更新ingress-nginx-controller (y/n): "
    read input
    input_lower=$(echo "$input" | tr '[:upper:]' '[:lower:]')
    if [ "$input_lower" = "y" ]; then
        helm upgrade --install ingress-nginx ingress-nginx \
          --repo https://kubernetes.github.io/ingress-nginx \
          --version "${INGRESS_NGINX_CONTROLLER_CHART_VERSION}" --namespace ingress-nginx --create-namespace \
          -f ./${CLUSTER_NAME}/ingress-nginx-helm-values.yaml
        echo "安装完毕，检查组件"
        kubectl get all -n ingress-nginx | grep ingress-nginx
    else
        echo "跳过创建ingress-nginx-controller。"
    fi
fi

echo "[安装aws-loadbalancer-controller]"
if [ "$AWS_LOADBALANCER_CONTROLLER" = "on" ]; then
    cat ./templates/aws-loadbalancer-controller-iam-policy-v"${AWS_LOADBALANCER_CONTROLLER_VERSION}".json
    echo
    echo -n "是否创建上述策略并用该策略创建角色 ${CLUSTER_NAME}-aws-loadbalancer-controller-role (y/n): "
    read input
    input_lower=$(echo "$input" | tr '[:upper:]' '[:lower:]')
    if [ "$input_lower" = "y" ]; then
        aws iam create-policy \
            --policy-name AWSLoadBalancerControllerIAMPolicy \
            --policy-document file://./templates/aws-loadbalancer-controller-iam-policy-v"${AWS_LOADBALANCER_CONTROLLER_VERSION}".json
        eksctl create iamserviceaccount --name aws-load-balancer-controller --namespace kube-system --cluster ${CLUSTER_NAME} --region ${REGION} \
            --role-name ${CLUSTER_NAME}-aws-loadbalancer-controller-role \
            --attach-policy-arn arn:aws:iam::${AWS_ACCOUNT_ID}:policy/AWSLoadBalancerControllerIAMPolicy \
            --role-only --approve
    else
        echo "跳过创建aws-load-balancer-controller策略和角色。"
    fi
    kubectl apply -f ./templates/aws-loadbalancer-controller-crds-v"${AWS_LOADBALANCER_CONTROLLER_VERSION}".yaml
    envsubst < ./templates/aws-loadbalancer-controller-helm-values.yaml > ./${CLUSTER_NAME}/aws-loadbalancer-controller-helm-values.yaml
    cat ./${CLUSTER_NAME}/aws-loadbalancer-controller-helm-values.yaml
    echo
    echo -n "是否使用以上参数安装/更新aws-loadbalancer-controller (y/n): "
    read input
    input_lower=$(echo "$input" | tr '[:upper:]' '[:lower:]')
    if [ "$input_lower" = "y" ]; then
        helm repo add eks https://aws.github.io/eks-charts && helm repo update eks
        helm upgrade --install aws-load-balancer-controller \
            --version "${AWS_LOADBALANCER_CONTROLLER_CHART_VERSION}" -n kube-system \
            eks/aws-load-balancer-controller \
            -f ./${CLUSTER_NAME}/aws-loadbalancer-controller-helm-values.yaml
        echo "安装完毕，检查pod和sa状态"
        kubectl get all -n kube-system | grep aws-load-balancer-controller
        kubectl describe sa aws-load-balancer-controller -n kube-system
    else
        echo "跳过安装aws-load-balancer-controller。"
    fi
    echo
fi

echo "[安装完毕，检查集群所有Pod]"
kubectl get pod -A