#!/bin/bash

CLUSTER_NAME=$1

echo "[检查子网IP数量和标签]"
QUERY="Subnets[*].{SubnetId:SubnetId,Name:Tags[?Key==\`Name\`].Value|[0],CIDR:CidrBlock,AvailableIPs:AvailableIpAddressCount,kubernetes_io_cluster_${CLUSTER_NAME//-/_}:Tags[?Key==\`kubernetes.io/cluster/${CLUSTER_NAME//-/_}\`].Value|[0],kubernetes_io_role_elb:Tags[?Key==\`kubernetes.io/role/elb\`].Value|[0],kubernetes_io_role_internal_elb:Tags[?Key==\`kubernetes.io/role/internal-elb\`].Value|[0]}"
echo "*包含kubernetes.io/cluster/$CLUSTER_NAME标签的子网:"
aws ec2 describe-subnets \
  --filters "Name=tag-key,Values=kubernetes.io/cluster/$CLUSTER_NAME" \
  --query $QUERY --region ${REGION} --no-cli-pager --output table
echo "*将在以下子网创建集群："
aws ec2 describe-subnets \
  --subnet-ids ${PRIVATE_SUBNET1_ID} ${PRIVATE_SUBNET2_ID} ${PRIVATE_SUBNET3_ID} \
  --query $QUERY --region ${REGION} --no-cli-pager --output table
echo
echo -n "开始创建集群，选择 y 将开始使用本地目录${CLUSTER_NAME}中的定义文件创建集群 (y/n): "
read input
input_lower=$(echo "$input" | tr '[:upper:]' '[:lower:]')
if [ "$input_lower" = "n" ]; then
    exit
fi

echo "[创建集群]"
eksctl create cluster -f ./${CLUSTER_NAME}/cluster.yaml
eksctl utils write-kubeconfig --cluster ${CLUSTER_NAME} --region ${REGION}
echo "[更改Pod所属子网]"
export SHAREDNODE_SG=$(aws cloudformation describe-stacks --stack-name eksctl-${CLUSTER_NAME}-cluster --region ${REGION} \
    --query 'Stacks[0].Outputs[?OutputKey==`SharedNodeSecurityGroup`].OutputValue' --output text --no-cli-pager)
export CLUSTER_SG=$(aws cloudformation describe-stacks --stack-nameeksctl-${CLUSTER_NAME}-cluster --region ${REGION} \
    --query 'Stacks[0].Outputs[?OutputKey==`ClusterSecurityGroupId`].OutputValue' --output text --no-cli-pager)
envsubst < ./templates/eniconfig.yaml > ./${CLUSTER_NAME}/eniconfig.yaml
kubectl apply -f ./${CLUSTER_NAME}/eniconfig.yaml
kubectl patch daemonset aws-node \
    -n kube-system \
    -p '{"spec": {"template": {"spec": {"initContainers": [{"env":[{"name":"DISABLE_TCP_EARLY_DEMUX","value":"true"}],"name":"aws-vpc-cni-init"}]}}}}'
echo "[安装托管节点组，用于部署管理组件]"
eksctl create nodegroup -f ./${CLUSTER_NAME}/nodegroup-addon.yaml
echo "[安装EBS storage class"]
kubectl apply -f ./${CLUSTER_NAME}/ebs-sc.yaml
echo "[安装EFS storage class]"
kubectl apply -f ./${CLUSTER_NAME}/efs-sc.yaml
echo "[安装ebs-csi-driver]"
eksctl create iamserviceaccount --name ebs-csi-controller-sa --namespace kube-system --cluster ${CLUSTER_NAME} --region ${REGION} \
            --role-name ${CLUSTER_NAME}-ebs-csi-role \
            --attach-policy-arn arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy \
            --role-only --approve
helm repo add aws-ebs-csi-driver https://kubernetes-sigs.github.io/aws-ebs-csi-driver && helm repo update aws-ebs-csi-driver
helm upgrade --install aws-ebs-csi-driver \
            --version "${EBS_CSI_DRIVER_CHART_VERSION}" --namespace kube-system \
            aws-ebs-csi-driver/aws-ebs-csi-driver  \
            -f ./${CLUSTER_NAME}/ebs-csi-driver-helm-values.yaml
kubectl get all -n kube-system | grep ebs-csi
kubectl describe sa ebs-csi-controller-sa -n kube-system
echo "[安装efs-csi-driver]"
aws iam create-policy \
            --policy-name EKS_EFS_CSI_Driver_Policy \
            --policy-document file://./templates/efs-csi-driver-iam-policy-v"${EFS_CSI_DRIVER_VERSION}".json
eksctl create iamserviceaccount --name efs-csi-controller-sa --namespace kube-system --cluster ${CLUSTER_NAME} --region ${REGION} \
            --role-name ${CLUSTER_NAME}-efs-csi-role \
            --attach-policy-arn arn:aws:iam::${AWS_ACCOUNT_ID}:policy/EKS_EFS_CSI_Driver_Policy \
            --role-only --approve
helm repo add aws-efs-csi-driver https://kubernetes-sigs.github.io/aws-efs-csi-driver && helm repo update aws-efs-csi-driver
helm upgrade --install aws-efs-csi-driver \
            --version "${EFS_CSI_DRIVER_CHART_VERSION}" --namespace kube-system \
            aws-efs-csi-driver/aws-efs-csi-driver  \
            -f ./${CLUSTER_NAME}/efs-csi-driver-helm-values.yaml
kubectl get all -n kube-system | grep efs-csi
kubectl describe sa efs-csi-controller-sa -n kube-system
echo "[安装karpenter]"
aws cloudformation deploy --region ${REGION} \
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
helm upgrade --install karpenter oci://public.ecr.aws/karpenter/karpenter \
            --version "v${KARPENTER_VERSION}" --namespace karpenter --create-namespace \
            -f ./${CLUSTER_NAME}/karpenter-helm-values.yaml 
kubectl get all -n karpenter | grep karpenter
kubectl describe sa karpenter -n karpenter
echo "[安装aws-loadbalancer-controller]"
aws iam create-policy \
            --policy-name AWSLoadBalancerControllerIAMPolicy \
            --policy-document file://./templates/aws-loadbalancer-controller-iam-policy-v"${AWS_LOADBALANCER_CONTROLLER_VERSION}".json
eksctl create iamserviceaccount --name aws-load-balancer-controller --namespace kube-system --cluster ${CLUSTER_NAME} --region ${REGION} \
            --role-name ${CLUSTER_NAME}-aws-loadbalancer-controller-role \
            --attach-policy-arn arn:aws:iam::${AWS_ACCOUNT_ID}:policy/AWSLoadBalancerControllerIAMPolicy \
            --role-only --approve
kubectl apply -f ./templates/aws-loadbalancer-controller-crds-v"${AWS_LOADBALANCER_CONTROLLER_VERSION}".yaml
helm repo add eks https://aws.github.io/eks-charts && helm repo update eks
helm upgrade --install aws-load-balancer-controller \
            --version "${AWS_LOADBALANCER_CONTROLLER_CHART_VERSION}" -n kube-system \
            eks/aws-load-balancer-controller \
            -f ./${CLUSTER_NAME}/aws-loadbalancer-controller-helm-values.yaml
kubectl get all -n kube-system | grep aws-load-balancer-controller
kubectl describe sa aws-load-balancer-controller -n kube-system
sleep 30
echo "[安装ingress-nginx-controller"]
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx && helm repo update ingress-nginx
helm upgrade --install ingress-nginx \
          --version "${INGRESS_NGINX_CONTROLLER_CHART_VERSION}" --namespace ingress-nginx --create-namespace \
          ingress-nginx/ingress-nginx  \
          -f ./${CLUSTER_NAME}/ingress-nginx-helm-values.yaml
kubectl get all -n ingress-nginx | grep ingress-nginx
echo "[安装prometheus"]
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts && helm repo update prometheus-community
helm upgrade --install prometheus \
          --version "${PROMETHEUS_CHART_VERSION}" --namespace monitoring --create-namespace \
          prometheus-community/prometheus \
          -f ./${CLUSTER_NAME}/prometheus-helm-values.yaml
kubectl get all -n monitoring | grep prometheus
echo "[安装fluentbit"]
helm repo add fluent https://fluent.github.io/helm-charts && helm repo update fluent
helm upgrade --install fluent-bit \
          --version "${FLUENTBIT_CHART_VERSION}" --namespace logging --create-namespace \
          fluent/fluent-bit  \
          -f ./${CLUSTER_NAME}/fluentbit-helm-values.yaml
kubectl get all -n logging | grep fluent-bit
echo "[安装完毕，检查集群所有Pod和Service]"
kubectl get pod -A
kubectl get svc -A