select m.region, c.resource_tags_user_name, t.dimension.dim_value as instance_id, m.namespace, m.metric_name, from_unixtime(m.timestamp) as time, m.value as metric_value from "AwsDataCatalog"."<metric_database>"."<metric_table>" m
CROSS JOIN UNNEST(m.dimensions) as t(dimension)
RIGHT JOIN
(select max(resource_tags_user_name) as resource_tags_user_name,line_item_resource_id from "AwsDataCatalog"."<cur_database>"."<cur_table>" 
 where year=date_format(current_date - interval '1' month,'%Y') and month=date_format(current_date - interval '1' month,'%c')
 group by line_item_resource_id
) c on c.line_item_resource_id = t.dimension.dim_value
where m.namespace='AWS/EC2' and t.dimension.dim_name='InstanceId'
