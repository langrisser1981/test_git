import boto3
import io
from PIL import ImageDraw, ExifTags, ImageColor
from PIL import Image as PilImage
from tkinter import filedialog
from tkinter import *

rekognition = boto3.client('rekognition')
dynamodb = boto3.client('dynamodb')

image = PilImage.open('single.jpg')
print(f'format:{image.format}, size:{image.size}, color:{image.mode}')
width = 640
ratio = float(640)/image.size[0]
height = int(image.size[1]*ratio)
image = image.resize((width, height), PilImage.BILINEAR)
print(f'new size:{image.size}')

stream = io.BytesIO()
image.save(stream, format='JPEG')
image_binary = stream.getvalue()

response = rekognition.search_faces_by_image(
        CollectionId = 'family_collection',
        Image = {'Bytes':image_binary})
        #Blob of image bytes up to 5 MBs.

for match in response['FaceMatches']:
    faceId = match['Face']['FaceId']
    confidence = match['Face']['Confidence']
    print(f'faceID:{faceId}, confidence:{confidence}')

    face = dynamodb.get_item(
            TableName = 'family_collection',
            Key = {'RekognitionId':{'S':faceId}})

    if 'Item' in face:
        person = face['Item']['FullName']['S']
    else:
        person = 'no match find'

    print(person)

