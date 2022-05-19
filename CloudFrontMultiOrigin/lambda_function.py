import json
import logging
import traceback

logging.basicConfig()
logger = logging.getLogger("multi-origin")

def lambda_handler(event, context):
    request = event['Records'][0]['cf']['request']
    try:
        if request['origin'].get('custom') and request['origin'].get('custom').get('customHeaders'):
            # 自定义源站才走这个逻辑
            customHeaders = request['origin'].get('custom').get('customHeaders')
            # 用于开关L@E的DEBUG日志输出
            debug = customHeaders.get('lambda-debug')
            logger.setLevel(logging.DEBUG if debug else logging.INFO)
            logger.debug(f'Request: {request}')
            # 原始源站域名
            domainName = request['origin']['custom']['domainName']
            logger.info(f'Origin Domainname: {domainName}')            
            # 获取客户端所在国家，分配的回源策略必须设置为转发CloudFront-Viewer-Country这个Header
            viewerCountry = request['headers'].get('cloudfront-viewer-country')
            logger.info(f'Viewer Country: {viewerCountry}')
            if viewerCountry and customHeaders.get('countries-list') and  customHeaders.get('origin-list'):
                # 用户通过源自定义标头定义国家和源站映射关系才走这个逻辑
                countries_list = customHeaders.get('countries-list')[0].get('value').split(',')
                logger.debug(f'Countries List: {countries_list}')
                origin_list = customHeaders.get('origin-list')[0].get('value').split(',')
                logger.debug(f'Origin List: {origin_list}')
                countryCode = viewerCountry[0]['value']
                # 根据客户端缩在国家找到对应的源站
                origin = None
                for i in range(len(countries_list)):
                    for c in countries_list[i].split('|'):
                        if c == viewerCountry[0].get('value'):
                            origin = origin_list[i]
                            break
                logger.debug(f'Actual Origin: {origin}')
                if origin:
                    # 如果可以找到则修改源站
                    request['origin']['custom']['domainName'] = origin
    except Exception:
        traceback.print_exc()
    finally:
        if customHeaders.get('lambda-debug'):        
            del(customHeaders['lambda-debug'])
        if customHeaders.get('countries-list'):
            del(customHeaders['countries-list'])
        if customHeaders.get('origin-list'):
            del(customHeaders['origin-list'])
        domainName = request['origin']['custom']['domainName']
        logger.info(f'New origin Domainname: {domainName}')
        return request        

