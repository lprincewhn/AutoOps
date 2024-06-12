select i.instance_id, n.name, image_id, instance_type, platform, vpc_id, subnet_id, private_ip_address, public_ip_address, security_groups, security_group_names, key_name,cardinality(network_interfaces) as eni_count from "lambda:aws-cmdb"."ec2".ec2_instances i left join
(select instance_id,t.tag.value as name from "lambda:aws-cmdb"."ec2".ec2_instances i
CROSS JOIN UNNEST(i.tags) as t(tag)
where t.tag.key='Name') n on i.instance_id=n.instance_id
