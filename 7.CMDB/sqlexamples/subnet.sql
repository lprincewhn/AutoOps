select vpc,s.id,availability_zone,available_ip_count,cidr_block,state,substring(n.name, 6) as name from "lambda:aws-cmdb"."ec2".subnets s left join
(select id,t.tag as name from "lambda:aws-cmdb"."ec2".subnets s
CROSS JOIN UNNEST(s.tags) as t(tag)
where t.tag like 'Name:%') n on s.id=n.id
