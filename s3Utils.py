# coding=utf-8
import json
import os

from sts.sts import Sts,Scope
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
import re

class S3Utils:
    def __init__(self, secret_id, secret_key, bucket,appid,region):
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.bucket = bucket
        self.appid = appid
        self.region = region
        self.newBucket = bucket + '-' + appid
        config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
        self.client = CosS3Client(config)


    def get_actions_list(self, role):
        if role == 'upload':
            actions = [
                'name/cos:PutObject',
                'name/cos:PostObject',
                'name/cos:HeadBucket',
                'name/cos:HeadObject',
                'name/cos:InitiateMultipartUpload',
                'name/cos:ListMultipartUploads',
                'name/cos:ListParts',
                'name/cos:UploadPart',
                'name/cos:CompleteMultipartUpload',
                'name/cos:AbortMultipartUpload',
                'name/cos:PutObjectCopy',
            ]
        elif role == 'download':
            actions = [
                'name/cos:GetBucket',
                'name/cos:HeadBucket'
                'name/cos:HeadObject',
                'name/cos:GetObject',
            ]
        elif role == 'upload_download':
            actions = [
                'name/cos:GetBucket',
                'name/cos:HeadBucket',
                'name/cos:DeleteObject',
                'name/cos:PutObject',
                'name/cos:GetObject',
                'name/cos:PutObjectCopy',
                'name/cos:HeadObject',
                'name/cos:PostObject',
                'name/cos:InitiateMultipartUpload',
                'name/cos:ListMultipartUploads',
                'name/cos:ListParts',
                'name/cos:UploadPart',
                'name/cos:CompleteMultipartUpload',
                'name/cos:GetBucketObjectVersions'
            ]
        else:
            actions = []
        return actions

    def get_credential_demo(self, allow_prefix, role):
        config = {
            'url': 'https://sts.tencentcloudapi.com/',
            'domain': 'sts.tencentcloudapi.com', 
            # 临时密钥有效时长，单位是秒
            'duration_seconds': 60*60*12,
            'secret_id': self.secret_id,  
            'secret_key': self.secret_key,

            'bucket':  self.newBucket, 
            'region': self.region,
            # 这里改成允许的路径前缀，可以根据自己网站的用户登录态判断允许上传的具体路径
            # 例子： a.jpg 或者 a/* 或者 * (使用通配符*存在重大安全风险, 请谨慎评估使用)
            'allow_prefix': allow_prefix,
            # 密钥的权限列表。简单上传和分片需要以下的权限，其他权限列表请看 https://cloud.tencent.com/document/product/436/31923
            'allow_actions': self.get_actions_list(role),
            # 临时密钥生效条件，关于condition的详细设置规则和COS支持的condition类型可以参考 https://cloud.tencent.com/document/product/436/71306
            "condition": {
            }
        }

        sts = Sts(config)
        response = sts.get_credential()
        return response

    def isObjectExist(self, key):
        try:
            response = self.client.object_exists(
                Bucket=self.bucket,
                Key=key
            )
            return response
        except Exception as e:
            return False

    def isValidObjectName(self, key):
        if len(key.encode('utf-8')) > 850:
            return False
        if key.startswith('/') or key.startswith('\\'):
            return False
        if '%0a' in key or '%0d' in key:
            return False
        if re.search(r'[\x18\x19\x1a\x1b]', key):
            return False
        if any(char in key for char in ['↑', '↓', '→', '←']):
            return False
        if any(char in key for char in ['*', '%']):
            return False
        return True
    def isValidDir(self, key):
        if self.isValidObjectName(key) == False:
            return False
        if key[-1] == '/':
            return True
        else:
            return False
    
    def createDir(self, key):
        response = self.client.put_object(
            Bucket=self.newBucket,
            Body='',
            Key=key
        )
        return response

    def uploadObject(self, key, file):
        response = self.client.upload_file(
            Bucket= self.newBucket,
            Key=key,
            LocalFilePath=file
        )
        return response

    def getObjectUrl(self, key):
        response = self.client.get_object_url(
            Bucket= self.newBucket,
            Key=key
        )
        return response
    def getPreSignUrl(self, key):
        response = self.client.get_presigned_download_url(
            Bucket= self.newBucket,
            Key=key,
        )
        return response
    
    def getUnifyToken(self,downloadList,uploadList,downUpList):
        scopes = list()
        print(downloadList,uploadList,downUpList)
        for item in downloadList:
            for action in self.get_actions_list('download'):
                scopes.append(Scope(action, self.newBucket, self.region, item))
        for item in uploadList:
            for action in self.get_actions_list('upload'):
                scopes.append(Scope(action, self.newBucket, self.region, item))
        for item in downUpList:
            for action in self.get_actions_list('upload_download'):
                scopes.append(Scope(action, self.newBucket, self.region, item))
        config = {
            'sts_scheme': 'https',
            'sts_url': 'sts.tencentcloudapi.com/',
            # 临时密钥有效时长，单位是秒
            'duration_seconds': 60*60*12,
            'secret_id': self.secret_id,
            # 固定密钥
            'secret_key': self.secret_key,
            # 换成 bucket 所在地区
            'region': self.region,
            #  设置网络代理
            # 'proxy': {
            #     'http': 'xxx',
            #     'https': 'xxx'
            # },
            'policy': Sts.get_policy(scopes)
        }

        sts = Sts(config)
        response = sts.get_credential()
        return response