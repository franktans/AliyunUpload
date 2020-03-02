#!/usr/bin/env python
# ! -*- coding:utf-8 -*-
import sys
import oss2
import random
import os
import tablib
import time
import json
from urllib.parse import quote
from aliyunsdkcore.client import AcsClient
from aliyunsdkmts.request.v20140618 import SubmitJobsRequest


#阿里云的账户、密码和bucket
access_key_id =''
access_key_secret = ''
bucketname = ''

dataset = tablib.Dataset()
header = ('title', 'url')
dataset.headers = header

#在阿里云转码页中找到
mps_region_id = ''
pipeline_id = ''
template_id = ''
oss_location = ''
oss_bucket = ''
oss_input_object = ''           #转码文件输入路径，由上传至OSS时的filename而决定
oss_output_object = ''          #转码文件输出路径，由上传至OSS时的filename而决定


#上传进度条
def percentage(consumed_bytes, total_bytes):
    if total_bytes:
        rate = int(100 * (float(consumed_bytes) / float(total_bytes)))
        print('\r{0}% '.format(rate), end='')
        sys.stdout.flush()

#上传过程
def putAliyun(path):
    Filename = path.split("/")[-1]
    print('正在上传：'+Filename)
    auth = oss2.Auth(access_key_id, access_key_secret)
    bucket = oss2.Bucket(auth, 'http://oss-cn-hangzhou.aliyuncs.com', bucketname)
    result = bucket.put_object_from_file(key=Filename, filename=path, progress_callback=percentage)

    if result.status == 200:
        print('文件上传成功！')
        file_url = bucket.sign_url('GET', Filename, 3600)   #该url未经转码，不能通过URL在线播放

        name = Filename.split(".")[0]   #截取不含扩展名的视频名称
        #上传成功，执行转码过程
        oss_input_object = Filename
        oss_output_object = 'transfer/'+name+'.mp4'     #输出视频在OSS中的路径
        # 创建AcsClient实例
        client = AcsClient(access_key_id, access_key_secret, mps_region_id)
        # 创建request，并设置参数
        request = SubmitJobsRequest.SubmitJobsRequest()
        request.set_accept_format('json')
        # 获取输入路径和信息
        job_input = {'Location': oss_location,
                     'Bucket': oss_bucket,
                     'Object': quote(oss_input_object)}
        request.set_Input(json.dumps(job_input))
        # 获取输出路径
        output = {'OutputObject': quote(oss_output_object)}
        # 输出视频类型
        output['Container'] = {'Format': 'mp4'}
        # 输出视频格式
        output['Video'] = {'Codec': 'H.264',
                           'Bitrate': 1500,
                           'Width': 1280,
                           'Fps': 25}
        # 输出音频格式
        output['Audio'] = {'Codec': 'AAC',
                           'Bitrate': 128,
                           'Channels': 2,
                           'Samplerate': 44100}
        # 获取模板ID
        output['TemplateId'] = template_id
        outputs = [output]
        request.set_Outputs(json.dumps(outputs))
        request.set_OutputBucket(oss_bucket)
        request.set_OutputLocation(oss_location)
        request.set_PipelineId(pipeline_id)
        # 发起API请求并显示返回值，包括RequestID、JodID和视频文件的URL
        response_str = client.do_action_with_exception(request)
        response = json.loads(response_str)
        #如果需要，输出RequestID
        #print('RequestId is:', response['RequestId'])
        if response['JobResultList']['JobResult'][0]['Success']:
            #如果需要，输出JobID
            #print('JobId is:', response['JobResultList']['JobResult'][0]['Job']['JobId'])
            print('转码后url: https://'+bucketname+'.oss-cn-hangzhou.aliyuncs.com/' + oss_output_object)
            print('文件转码成功！')
        else:
            print('SubmitJobs Failed code:',
                  response['JobResultList']['JobResult'][0]['Code'],
                  ' message:',
                  response['JobResultList']['JobResult'][0]['Message'])

    else:
        print('文件上传失败', result.status)

#运行方法为python Upload.py 文件的绝对路径
path = sys.argv[1]
putAliyun(path)  #执行上传并转码过程


