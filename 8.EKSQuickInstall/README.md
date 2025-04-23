# EKSQuickInstall

This tool helps create an EKS cluster easily.

This tool use eksctl to create EKS cluster. To avoid different behaviour of diffrent eksctl versions, please always use 0.205.0 version of eksctl.
Install eksctl with following command:

```
curl -sLO "https://github.com/weaveworks/eksctl/releases/download/v0.205.0/eksctl_Linux_amd64.tar.gz"
tar -xzf eksctl_Linux_amd64.tar.gz
sudo mv ./eksctl /usr/local/bin
sudo chmod +x /usr/local/bin/eksctl
eksctl version
```

