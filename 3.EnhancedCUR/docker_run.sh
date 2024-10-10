#!/bin/bash
docker run -it --rm \
    -v ~/.aws:/home/glue_user/.aws \
    -v $(pwd)/:/home/glue_user/workspace/ \
    -e DISABLE_SSL=true \
    -e AWS_REGION=us-east-1 \
    -p 18080:18080 \
    -p 4040:4040 \
    --name glue_spark_submit \
    amazon/aws-glue-libs:glue_libs_4.0.0_image_01 spark-submit /home/glue_user/workspace/allocate-untag.py \
    --work-bucket cur-597377428377 \
    --year 2024 \
    --month 6 \
    --enable-glue-datacatalog true \
    --cur-database athenacurcfn_c_u_r_athena \
    --cur-table cur_athena_standardize \
    --tags-fields resource_tags_user_project \
    --verbose 0
    
docker run -it --rm \
    -v ~/.aws:/home/glue_user/.aws \
    -v $(pwd):/home/glue_user/workspace/jupyter_workspace/ \
    -e DISABLE_SSL=true \
    -p 4040:4040 \
    -p 18080:18080 \
    -p 8998:8998 \
    -p 8888:8888 \
    --name glue_jupyter_lab \
    amazon/aws-glue-libs:glue_libs_4.0.0_image_01 /home/glue_user/jupyter/jupyter_start.sh