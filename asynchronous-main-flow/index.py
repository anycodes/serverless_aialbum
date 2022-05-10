# -*- coding: utf-8 -*-

import av
import os
import json
import oss2
import random
import math
import imghdr
import exifread
import urllib.request
import urllib.parse
import pyheif
import whatimage
from PIL import Image
import tensorflow as tf
from config import Config
from dataset import DataSet
from utils.vocabulary import Vocabulary
from generator import CaptionGenerator
from aliyunsdkcore.client import AcsClient
from aliyunsdkalimt.request.v20181012.TranslateGeneralRequest import TranslateGeneralRequest

x_pi = 3.14159265358979324 * 3000.0 / 180.0
pi = 3.1415926535897932384626  # π
a = 6378245.0  # 长半轴
ee = 0.00669342162296594323  # 扁率

AccessKeyId = os.environ.get("ACCESS_KEY_ID")
AccessKeySecret = os.environ.get("ACCESS_KEY_SECRET")

# 存储桶操作
uploadUrl = "https://upload.aialbum.net"
downloadUrl = "https://download.aialbum.net"
baseUrl = "http://%s.%s" % (os.environ.get('OSS_BUCKET'), os.environ.get('OSS_ENDPOINT'))
auth = oss2.Auth(os.environ.get('ACCESS_KEY_ID'), os.environ.get('ACCESS_KEY_SECRET'))
bucket = oss2.Bucket(auth, os.environ.get('OSS_ENDPOINT'), os.environ.get('OSS_BUCKET'))

doRequest = lambda data, headers: urllib.request.urlopen(
    urllib.request.Request(url="http://%s/photo/update/status" % (os.environ.get("DOMAIN")),
                           data=urllib.parse.urlencode(data).encode("utf-8"), headers=headers))

# ACS对象
acs = AcsClient(AccessKeyId, AccessKeySecret, 'cn-hangzhou')
# load model
config = Config()
sess = tf.compat.v1.Session()
model = CaptionGenerator(config)
model.load(sess, "/mnt/auto/image_caption/model.npy")
tf.compat.v1.get_default_graph().finalize()
vocabulary = Vocabulary(config.vocabulary_size, config.vocabulary_file)
randomStr = lambda num=5: "".join(random.sample('abcdefghijklmnopqrstuvwxyz', num))
# 路径处理
localFileBase = "/tmp/photo"
localSourceFileBase = os.path.join(localFileBase, "original/")
localTargetFileBase = os.path.join(localFileBase, "thumbnail/")
localCaptionFileBase = os.path.join(localFileBase, "caption/")
os.makedirs(localSourceFileBase)
os.makedirs(localTargetFileBase)
os.makedirs(localCaptionFileBase)


def wgs84togcj02(lng, lat):
    """
    WGS84转GCJ02(火星坐标系)
    :param lng:WGS84坐标系的经度
    :param lat:WGS84坐标系的纬度
    :return:
    """
    if out_of_china(lng, lat):  # 判断是否在国内
        return lng, lat
    dlat = transformlat(lng - 105.0, lat - 35.0)
    dlng = transformlng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * pi
    magic = math.sin(radlat)
    magic = 1 - ee * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * pi)
    dlng = (dlng * 180.0) / (a / sqrtmagic * math.cos(radlat) * pi)
    mglat = lat + dlat
    mglng = lng + dlng
    return [mglng, mglat]


def gcj02towgs84(lng, lat):
    """
    GCJ02(火星坐标系)转GPS84
    :param lng:火星坐标系的经度
    :param lat:火星坐标系纬度
    :return:
    """
    if out_of_china(lng, lat):
        return lng, lat
    dlat = transformlat(lng - 105.0, lat - 35.0)
    dlng = transformlng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * pi
    magic = math.sin(radlat)
    magic = 1 - ee * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * pi)
    dlng = (dlng * 180.0) / (a / sqrtmagic * math.cos(radlat) * pi)
    mglat = lat + dlat
    mglng = lng + dlng
    return [lng * 2 - mglng, lat * 2 - mglat]


def transformlat(lng, lat):
    ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + \
          0.1 * lng * lat + 0.2 * math.sqrt(math.fabs(lng))
    ret += (20.0 * math.sin(6.0 * lng * pi) + 20.0 *
            math.sin(2.0 * lng * pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lat * pi) + 40.0 *
            math.sin(lat / 3.0 * pi)) * 2.0 / 3.0
    ret += (160.0 * math.sin(lat / 12.0 * pi) + 320 *
            math.sin(lat * pi / 30.0)) * 2.0 / 3.0
    return ret


def transformlng(lng, lat):
    ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + \
          0.1 * lng * lat + 0.1 * math.sqrt(math.fabs(lng))
    ret += (20.0 * math.sin(6.0 * lng * pi) + 20.0 *
            math.sin(2.0 * lng * pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lng * pi) + 40.0 *
            math.sin(lng / 3.0 * pi)) * 2.0 / 3.0
    ret += (150.0 * math.sin(lng / 12.0 * pi) + 300.0 *
            math.sin(lng / 30.0 * pi)) * 2.0 / 3.0
    return ret


def out_of_china(lng, lat):
    """
    判断是否在国内，不在国内不做偏移
    :param lng:
    :param lat:
    :return:
    """
    if lng < 72.004 or lng > 137.8347:
        return True
    if lat < 0.8293 or lat > 55.8271:
        return True
    return False


def format_lati_long_data(data):
    """
    对经度和纬度数据做处理，保留6位小数
    :param data: 原始经度和纬度值
    :return:
    """
    # 删除左右括号和空格
    data_list_tmp = str(data).replace('[', '').replace(']', '').split(',')
    data_list = [data.strip() for data in data_list_tmp]

    # 替换秒的值
    data_tmp = data_list[-1].split('/')

    # 秒的值
    data_sec = int(data_tmp[0]) / int(data_tmp[1]) / 3600

    # 替换分的值
    data_tmp = data_list[-2]

    # 分的值
    data_minute = int(data_tmp) / 60

    # 度的值
    data_degree = int(data_list[0])

    # 由于高德API只能识别到小数点后的6位
    # 需要转换为浮点数，并保留为6位小数
    result = "%.6f" % (data_degree + data_minute + data_sec)
    return float(result)


def getPhotoInfo(img_path):
    img_exif = exifread.process_file(open(img_path, 'rb'))

    # 能够读取到属性
    if img_exif:
        # 纬度数
        latitude_gps = img_exif['GPS GPSLatitude']

        # 经度数
        longitude_gps = img_exif['GPS GPSLongitude']

        # 拍摄时间
        take_time = img_exif['EXIF DateTimeOriginal']
        take_time = str(take_time).split(' ')[0].replace(":", "-") + ' ' + str(take_time).split(' ')[1]

        # 纬度、经度、拍摄时间
        if latitude_gps and longitude_gps and take_time:
            # 对纬度、经度值原始值作进一步的处理
            latitude = format_lati_long_data(latitude_gps)
            longitude = format_lati_long_data(longitude_gps)

            # 注意：由于gps获取的坐标在国内高德等主流地图上逆编码不够精确，这里需要转换为火星坐标系
            location = wgs84togcj02(longitude, latitude)

            return {
                "time": take_time,
                "location": {
                    "longitude": location[0],
                    "latitude": location[1]
                }
            }
        return False
    return False


# 定义提取视频关键帧的函数
def extract_video(filename, target_source):
    container = av.open(filename)
    stream = container.streams.video[0]
    stream.codec_context.skip_frame = 'NONKEY'
    count = 0
    for frame in container.decode(stream):
        frame.to_image().save(target_source, quality=30)
        count = count + 1
        if count > 10:
            break


def handler(event, context):
    events = json.loads(event.decode("utf-8"))["events"]
    for eveObject in events:
        # 路径处理
        file = eveObject["oss"]["object"]["key"]
        file_token = file.split('/')[-1]
        origin_file = 'origin/' + file_token
        target_file = 'thumbnail/' + file_token
        local_source_file = '/tmp/' + file_token + '.png'
        local_target_file = '/tmp/target_' + file_token

        headers = {
            'token': os.environ.get("UPDATE_TOKEN"),
            'update-type': 'lifecycle',
            'object': file.split('/')[-1],
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        # 下载文件
        bucket.get_object_to_file(origin_file, local_source_file)

        is_image = 0
        print("is_image origin: ", is_image)
        if not imghdr.what(local_source_file):
            is_image = is_image + 1
            print("is_image imghdr.what: ", is_image)
            # 获取图片经纬度信息
            try:
                temp_information = getPhotoInfo(local_source_file)
                if temp_information:
                    headers['update-type'] = 'base_information'
                    data = {'create_time': temp_information['time'],
                            'longitude': temp_information['location']['longitude'],
                            'latitude': temp_information['location']['latitude']}
                    doRequest(data, headers)
                else:
                    print("is_image temp_information else: ", is_image)
                    is_image = is_image + 1
            except Exception as e:
                is_image = is_image + 1
                print("is_image exception: ", is_image, e)

        if is_image >= 2:  # 视频
            # 视频，进行关键帧提取
            try:
                headers['update-type'] = 'image_type'
                data = {'image_type': '1'}
                doRequest(data, headers)

                extract_video(local_source_file, local_source_file + ".png")
                im = Image.open(local_source_file + ".png")  # 原始图片
                mark = Image.open("./logo.png")  # 水印图片
                image_width, image_height = im.size
                mark_width, mark_height = mark.size
                temp_length = (image_height if image_width > image_height else image_width) / 1.5
                mark = mark.resize((int(temp_length), int(mark_height * temp_length / mark_width)))
                layer = Image.new('RGBA', im.size, (0, 0, 0, 0))
                layer.paste(im, (0, 0))
                layer.paste(mark, (int(image_width / 2 - temp_length / 2),
                                   int(image_height / 2 - int(mark_height * temp_length / mark_width) / 2)),
                            mark)  # 数值根据水印 size
                layer.save(local_source_file, "PNG")
            except Exception as e:
                print("视频，进行关键帧提取 Error: ", e)
        else:
            # 获取图片信息
            headers['update-type'] = 'image_type'
            data = {'image_type': '0'}
            doRequest(data, headers)

            # 尝试图像转换
            local_caption_file = '/tmp/caption_' + file_token
            with open(local_source_file, 'rb') as f:
                file_data = f.read()
            fmt = whatimage.identify_image(file_data)
            if fmt == 'heic':
                try:
                    heif_file = pyheif.read_heif(local_source_file)
                    image = Image.frombytes(mode=heif_file.mode, size=heif_file.size, data=heif_file.data)
                    image.save(local_source_file, "PNG")
                except Exception as e:
                    print("HEIC Error: ", e)
            else:
                try:
                    Image.open(local_source_file).save(local_source_file, "PNG")
                except Exception as e:
                    print("JPG->PNG Error: ", e)

            # 预测需要JPRG格式
            try:
                Image.open(local_source_file).save(local_caption_file, "JPEG")
            except Exception as e:
                print("PNG->JPEG Error: ", e)

            try:
                # caption
                data = DataSet([0], [local_caption_file], config.batch_size)
                batch = data.next_batch()
                caption_data = model.beam_search(sess, batch, vocabulary)
                word_idxs = caption_data[0][0].sentence
                caption = vocabulary.get_sentence(word_idxs)

                # 结果翻译
                if caption:
                    request = TranslateGeneralRequest()
                    request.set_accept_format('json')
                    request.set_FormatType("text")
                    request.set_SourceLanguage("en")
                    request.set_TargetLanguage("zh")
                    request.set_SourceText(caption)
                    response = acs.do_action_with_exception(request)
                    try:
                        caption = json.loads(str(response, encoding='utf-8'))["Data"]["Translated"]
                    except:
                        caption = caption
                else:
                    caption = ""

                headers['update-type'] = 'image_caption'
                data = {'ai_description': caption}
                doRequest(data, headers)
            except Exception as e:
                print("Image Caption Error: ", e)


        # 最后统一进行图片压缩
        try:
            temp_command = './pngquant --quality %s-%s --speed %s %s' % ('30', '40', '3', local_source_file)
            print("command: ", temp_command)
            os.system(temp_command)
            local_target_file = local_source_file.replace(".png", '-fs8.png')
            image = Image.open(local_target_file)
            # print("Compress origin: ", image.size)
            width = 220
            height = image.size[1] / (image.size[0] / width)
            imageObj = image.resize((int(width), int(height)), Image.ANTIALIAS)
            imageObj.save(local_target_file, "PNG", optimize=True, quality=80)
            # 回传图片
            bucket.put_object_from_file(target_file, local_target_file)
        except Exception as e:
            print("Compress Error: ", e)
            # 回传图片
            bucket.put_object_from_file(target_file, local_source_file)

        headers['update-type'] = 'thumbnail'
        data = {'thumbnail': '1'}
        doRequest(data, headers)

        try:
            os.remove(local_target_file)
            os.remove(local_source_file)
            os.remove(local_caption_file)
        except:
            pass
