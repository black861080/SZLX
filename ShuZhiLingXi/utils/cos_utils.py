from qcloud_cos import CosConfig, CosS3Client
from config.config import Config
import sys
import logging
import base64
from io import BytesIO
import uuid
from PIL import Image
import time
import tempfile
import os

# 配置日志输出
logging.basicConfig(level=logging.INFO, stream=sys.stdout)


class COSClient:
    def __init__(self):
        config = CosConfig(
            Region=Config.COSConfig.REGION,
            SecretId=Config.COSConfig.SECRET_ID,
            SecretKey=Config.COSConfig.SECRET_KEY
        )
        self.client = CosS3Client(config)
        self.bucket = Config.COSConfig.BUCKET

    def upload_base64_image(self, base64_data, prefix='chat_images/'):
        """
        上传base64格式的图片到COS
        :param base64_data: base64编码的图片数据
        :param prefix: 文件夹前缀
        :return: 图片的访问URL
        """
        try:
            # 确保base64字符串有正确的填充
            padding = len(base64_data) % 4
            if padding:
                base64_data += '=' * (4 - padding)

            # 解码base64数据
            img_data = base64.b64decode(base64_data)

            # 验证图片格式并转换
            image = Image.open(BytesIO(img_data))
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # 重新编码为JPEG
            buffered = BytesIO()
            image.save(buffered, format="JPEG")
            img_data = buffered.getvalue()

            # 生成唯一的文件名
            file_name = f"{prefix}{str(uuid.uuid4())}.jpg"

            # 上传到COS
            self.client.put_object(
                Bucket=self.bucket,
                Body=img_data,
                Key=file_name,
                ContentType='image/jpeg'
            )

            # 生成带签名的URL，有效期1小时
            url = self.client.get_object_url(
                Bucket=self.bucket,
                Key=file_name,
            )

            logging.info(f"图片上传成功，URL: {url}")
            return url.replace('%2F', '/')

        except Exception as e:
            logging.error(f"上传图片到COS失败: {str(e)}")
            raise Exception(f"上传图片到COS失败: {str(e)}")

    def upload_base64_video(self, base64_data, prefix='chat_videos/'):
        """
        上传base64格式的视频到COS
        :param base64_data: base64编码的视频数据
        :param prefix: 文件夹前缀
        :return: 视频的访问URL
        """
        try:
            # 确保base64字符串有正确的填充
            padding = len(base64_data) % 4
            if padding:
                base64_data += '=' * (4 - padding)

            # 解码base64数据
            video_data = base64.b64decode(base64_data)
            
            # 使用系统临时目录创建临时文件
            temp_dir = tempfile.gettempdir()
            temp_file_path = os.path.join(temp_dir, f"{str(uuid.uuid4())}.mp4")
            
            # 确保目录存在
            os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
            
            # 写入临时文件
            with open(temp_file_path, 'wb') as f:
                f.write(video_data)

            # 生成唯一的文件名
            file_name = f"{prefix}{str(uuid.uuid4())}.mp4"

            try:
                # 使用分块上传
                response = self.client.upload_file(
                    Bucket=self.bucket,
                    Key=file_name,
                    LocalFilePath=temp_file_path,
                    PartSize=10,  # 分块大小（MB）
                    MAXThread=10  # 最大并发数
                )
            finally:
                # 确保临时文件被删除
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

            # 生成URL
            url = self.client.get_object_url(
                Bucket=self.bucket,
                Key=file_name,
            )

            logging.info(f"视频上传成功，URL: {url}")
            return url.replace('%2F', '/')

        except Exception as e:
            logging.error(f"上传视频到COS失败: {str(e)}")
            raise Exception(f"上传视频到COS失败: {str(e)}")

    def upload_base64_audio(self, base64_data, prefix='chat_audios/'):
        """
        上传base64格式的录音到COS
        :param base64_data: base64编码的录音数据
        :param prefix: 文件夹前缀
        :return: 录音的访问URL
        """
        try:
            # 确保base64字符串有正确的填充
            padding = len(base64_data) % 4
            if padding:
                base64_data += '=' * (4 - padding)

            # 解码base64数据
            audio_data = base64.b64decode(base64_data)

            # 使用系统临时目录创建临时文件
            temp_dir = tempfile.gettempdir()
            temp_file_path = os.path.join(temp_dir, f"{str(uuid.uuid4())}.mp3")

            # 确保目录存在
            os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)

            # 写入临时文件
            with open(temp_file_path, 'wb') as f:
                f.write(audio_data)

            # 生成唯一的文件名
            file_name = f"{prefix}{str(uuid.uuid4())}.mp3"

            try:
                # 使用分块上传
                response = self.client.upload_file(
                    Bucket=self.bucket,
                    Key=file_name,
                    LocalFilePath=temp_file_path,
                    PartSize=10,  # 分块大小（MB）
                    MAXThread=10  # 最大并发数
                )
            finally:
                # 确保临时文件被删除
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

            # 生成URL
            url = self.client.get_object_url(
                Bucket=self.bucket,
                Key=file_name,
            )

            logging.info(f"录音上传成功，URL: {url}")
            return url.replace('%2F', '/')

        except Exception as e:
            logging.error(f"上传录音到COS失败: {str(e)}")
            raise Exception(f"上传录音到COS失败: {str(e)}")