# -*- coding: utf-8 -*-
import boto3
import os

from PIL import Image
from io import BytesIO

BUCKET_NAME = '[BUCKET NAME]'
TARGET_PREFIX = '[target_prefix]'
LARGE_LENGTH = 1280
THUMBNAIL_HEIGHT = 150
QUALITY = 60
NEW_LARGE_IMAGES_PREFIX = 'images/'
NEW_THUMBNAILS_PREFIX = 'thumbnails/'

def start_converting():
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(BUCKET_NAME)

    for obj in bucket.objects.filter(Prefix=TARGET_PREFIX):
        input_file = BytesIO(obj.get()['Body'].read())
        img = Image.open(input_file)

        img = fix_correct_orientation(img)
        output_thumnail, output_large = resize_and_convert_to_jpeg(img)

        input_file.close()

        # Save images at s3
        root, _ = os.path.splitext(obj.key)
        key = NEW_LARGE_IMAGES_PREFIX + root.split('/')[1] + '.jpg'
        new_obj = s3.Object(BUCKET_NAME, key)
        new_obj.put(Body=output_large)

        key = NEW_THUMBNAILS_PREFIX + root.split('/')[1] + '.jpg'
        new_obj = s3.Object(BUCKET_NAME, key)
        new_obj.put(Body=output_thumbnail)

        obj.delete()


def fix_correct_orientation(img):
    try:
        exif = img._getexif()
        orientation = exif.get(0x112, 1)
    except:
        orientation = 1
    convert_image = {
    1: lambda img: img,
    2: lambda img: img.transpose(Image.FLIP_LEFT_RIGHT),
    3: lambda img: img.transpose(Image.ROTATE_180),
    4: lambda img: img.transpose(Image.FLIP_TOP_BOTTOM),
    5: lambda img: img.transpose(
        Image.FLIP_LEFT_RIGHT).transpose(Image.ROTATE_90),
    6: lambda img: img.transpose(Image.ROTATE_270),
    7: lambda img: img.transpose(
        Image.FLIP_LEFT_RIGHT).transpose(Image.ROTATE_270),
    8: lambda img: img.transpose(Image.ROTATE_90),
    }
    return convert_image[orientation](img)


def resize_and_convert_to_jpeg(img):
    img = img.convert('RGB')
    if img.height < img.width:
        width = int(img.width * LARGE_LENGTH / img.height)
        img_large = img.resize((width, LARGE_LENGTH),Image.LANCZOS)
    else:
        height = int(img.height * LARGE_LENGTH / img.width)
        img_large = img.resize((LARGE_LENGTH, height), Image.LANCZOS)
    thumbnail_width = int(img.width * THUMBNAIL_HEIGHT / img.height)
    img.thumbnail((thumbnail_width, THUMBNAIL_HEIGHT), Image.LANCZOS)

    tmp = BytesIO()

    img.save(tmp, 'JPEG', quality=QUALITY)
    tmp.seek(0)
    output_thumbnail = tmp.getvalue()

    img_large.save(tmp, 'JPEG', quality=QUALITY)
    tmp.seek(0)
    output_large = tmp.getvalue()

    tmp.close()

    return output_thumnail, output_large


if __name__ == "__main__":
    start_converting()
