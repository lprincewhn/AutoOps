#!/bin/bash

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

echo "[下载efs-csi-driver控制器所需AWS IAM策略]"
curl -so "templates/efs-csi-driver-iam-policy-v${EFS_CSI_DRIVER_VERSION}.json" \
https://raw.githubusercontent.com/kubernetes-sigs/aws-efs-csi-driver/refs/tags/v${EFS_CSI_DRIVER_VERSION}/docs/iam-policy-example.json
ls -l "templates/efs-csi-driver-iam-policy-v${EFS_CSI_DRIVER_VERSION}.json"

echo "[下载karpenter所需资源的CloudFormation堆栈，包括节点角色，控制器所需策略，SQS队列，所需侦听事件规则]"
curl -so "templates/karpenter-cloudformation-v${KARPENTER_VERSION}.yaml" \
-fSL "https://raw.githubusercontent.com/aws/karpenter-provider-aws/v${KARPENTER_VERSION}/website/content/en/preview/getting-started/getting-started-with-karpenter/cloudformation.yaml"
ls -l "templates/karpenter-cloudformation-v${KARPENTER_VERSION}.yaml"

echo "[下载aws-loadbalancer-controller的CRD定义]"
curl -so "templates/aws-loadbalancer-controller-crds-v${AWS_LOADBALANCER_CONTROLLER_VERSION}.yaml" \
https://raw.githubusercontent.com/aws/eks-charts/master/stable/aws-load-balancer-controller/crds/crds.yaml
ls -l "templates/aws-loadbalancer-controller-crds-v${AWS_LOADBALANCER_CONTROLLER_VERSION}.yaml"

echo "[下载aws-loadbalancer-controller所需AWS IAM策略]"
curl -so "templates/aws-loadbalancer-controller-iam-policy-v${AWS_LOADBALANCER_CONTROLLER_VERSION}.json" \
"https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v${AWS_LOADBALANCER_CONTROLLER_VERSION}/docs/install/iam_policy.json"
ls -l "templates/aws-loadbalancer-controller-iam-policy-v${AWS_LOADBALANCER_CONTROLLER_VERSION}.json"