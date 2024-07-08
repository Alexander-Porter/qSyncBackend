from dotenv import load_dotenv
from s3Utils import S3Utils
import os
load_dotenv() 
myS3=S3Utils(os.getenv("SECRET_ID"), os.getenv("SECRET_KEY"), os.getenv("BUCKET"), os.getenv("REGION"))
myS3.get_credential_demo("test.txt","download")