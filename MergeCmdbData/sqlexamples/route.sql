select substring(n.name, 6) as name, r.route_table_id,vpc,state, dst_cidr,dst_cidr_v6,dst_prefix_list,egress_igw,gateway,instance_id,nat_gateway,interface,transit_gateway,vpc_peering_con from "lambda:aws-cmdb"."ec2".routing_tables r left join
(select route_table_id,t.tag as name from "lambda:aws-cmdb"."ec2".routing_tables r
CROSS JOIN UNNEST(r.tags) as t(tag)
where t.tag like 'Name:%') n on r.route_table_id=n.route_table_id
