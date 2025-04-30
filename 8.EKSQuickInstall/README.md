# EKSQuickInstall

This tool helps create an EKS cluster easily, which could be use in blue-green deployment or disaster recovery.

This tool use eksctl to create EKS cluster. To avoid different behaviour of diffrent eksctl versions, please always use 0.205.0 version of eksctl.
Install eksctl with following command:

```
curl -sLO "https://github.com/weaveworks/eksctl/releases/download/v0.205.0/eksctl_Linux_amd64.tar.gz"
tar -xzf eksctl_Linux_amd64.tar.gz
sudo mv ./eksctl /usr/local/bin
sudo chmod +x /usr/local/bin/eksctl
eksctl version
```

### 1. Define your cluster by environment variables.

These environment variables are used to define an EKS cluster. All related YAML files will be generated from template files and these environment variables. Following is an example:
For some EKS addons such as csi, it will be installed by helm and the app version and both the correspondant chart version should be set as environment variables. Please use "helm search repo" command to get the chart version of each addon.

```bash
cat <<EOF > demo-1.env
export AWS_ACCOUNT_ID="597377428377"
export CLUSTER_NAME="demo-1"
export REGION="ap-northeast-1"
export CLUSTER_VERSION="1.25"
export VPC_ID="vpc-0fa219345714af743"
export AZ1="ap-northeast-1a"
export AZ2="ap-northeast-1c"
export AZ3="ap-northeast-1d"
export PRIVATE_SUBNET1_ID="subnet-0dfba9cbf1a243eb4"
export PRIVATE_SUBNET2_ID="subnet-053dc36a6eee2fd5d"
export PRIVATE_SUBNET3_ID="subnet-0df398e3d5080a264"

export AWS_VPC_K8S_CNI_CUSTOM_NETWORK_CFG="true"
export ENI_CONFIG_LABEL_DEF="topology.kubernetes.io/zone"
export POD_SUBNET1_ID="subnet-0c8ba1d4672bc104b"
export POD_SUBNET2_ID="subnet-044a7cec99f375706"
export POD_SUBNET3_ID="subnet-050f2aaab0ec26ee3"

export ADDON_NODEGROUP_NAME="ng-ondemand"
export ADDON_NODEGROUP_SSHKEY="keypair-tokyo-2024"
export ADDON_NODEGROUP_INSTANCE_TYPE="t3.medium"

export EBS_CSI_DRIVER="on"
export EBS_CSI_DRIVER_VERSION="1.25.0"
export EBS_CSI_DRIVER_CHART_VERSION="2.25.0" # helm search repo aws-ebs-csi-driver/aws-ebs-csi-driver --versions | grep 1.25.0

export EFS_CSI_DRIVER="on"
export EFS_CSI_DRIVER_VERSION="2.0.0"
export EFS_CSI_DRIVER_CHART_VERSION="3.0.0" # helm search repo aws-efs-csi-driver/aws-efs-csi-driver --versions | grep 2.0.0
export EFS_FILE_SYSTEM_ID="fs-0e5b58791778769c6"

export KARPENTER="on"
export KARPENTER_VERSION="0.27.3"

export INGRESS_NGINX_CONTROLLER="on"
export INGRESS_NGINX_CONTROLLER_VERSION="1.9.5"
export INGRESS_NGINX_CONTROLLER_CHART_VERSION="4.9.0" # helm search repo ingress-nginx/ingress-nginx --versions | grep 1.9.5

export AWS_LOADBALANCER_CONTROLLER="on"
export AWS_LOADBALANCER_CONTROLLER_VERSION="2.12.0"
export AWS_LOADBALANCER_CONTROLLER_CHART_VERSION="1.12.0" # helm search repo eks/aws-load-balancer-controller --versions | grep 2.12.0

export FLUENT_BIT="on"
export FLUENT_BIT_VERSION="3.2.10"
export FLUENT_BIT_CHART_VERSION="0.48.10"

export PROMETHEUS="on"
export PROMETHEUS_VERSION="v3.2.1"
export PROMETHEUS_CHART_VERSION="27.7.0"

EOF
. ./demo-1.env
```

### 2. Precheck
Check subnets and download needed files.
```
./0.precheck.sh
```

### 3. Deploy the cluster step by step

3.1 Install cluster
Generate the YAML of EKS cluster and create it with eksctl. 
```
./1.install_cluster.sh
```

3.2 Install nodegroup
Generate the YAML of EKS managed nodegroup, which the addon run on, and then create it.
```
./2.install_ng_addon.sh
```

3.3 Install storageclass (Optional)
Generate the YAML of storageclass and create it. Storage class should be installed prior to addons, because some addons such as prometheus need specific storage class. 
```
./3.install_storageclass.sh
```

3.4 Install addons
Generate the Helm values.yaml of addons and install them.
```
./4.install_addons.sh
```

### 4. Deploy the cluster in one command
In case you have deploy the cluster by step by step once, all files needed are generate in the directory named by cluster name. And you can re-deploy the cluster with only on command.
```
./all-in-one.sh <CLUSTER_NAME>
```