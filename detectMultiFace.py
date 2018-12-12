import boto3
import botocore

import io
from PIL import ImageDraw, ExifTags, ImageColor
from PIL import Image as PilImage
from tkinter import filedialog
from tkinter import *
import pprint
import time

pp = pprint.PrettyPrinter(indent=4)
rekognition = boto3.client('rekognition')
dynamodb = boto3.client('dynamodb')

def openFile():
    text.delete(1.0, END)
    fileName =  filedialog.askopenfilename(initialdir = ".\sample",title = "Select file",filetypes = (("jpeg files","*.jpg"),("all files","*.*")))
    text.insert(END, f'{fileName}\n\n')
    process(fileName)

def process(fileName):
    tStart = time.perf_counter()

    image = PilImage.open(fileName)

    if hasattr(image, '_getexif'):
        orientation = 0x0112
        rotations = {
                3: PilImage.ROTATE_180,
                6: PilImage.ROTATE_270,
                8: PilImage.ROTATE_90
                }
        exif = image._getexif()
        if exif is not None and orientation in exif.keys():
            key = exif[orientation]
            if key in rotations.keys():
                image = image.transpose(rotations[key])

    text.insert(END, f'Original size:{image.size}, Mode:{image.mode}\n')
    width = 640
    ratio = float(640)/image.size[0]
    height = int(image.size[1]*ratio)
    image = image.resize((width, height), PilImage.BILINEAR)
    text.insert(END, f'New size:{image.size}\n\n')

    stream = io.BytesIO()
    image.save(stream, format='JPEG')
    image_binary = stream.getvalue()
    draw = ImageDraw.Draw(image)  

    response = rekognition.detect_faces(
            Image = {'Bytes':image_binary},
            Attributes = ['ALL'])
    all_faces = response['FaceDetails']
    expansion = .1
    for face in all_faces:
        #pp.pprint(face)
        box = face['BoundingBox']
        x1 = int(box['Left']*width) * (1-expansion)
        y1 = int(box['Top']*height) * (1-expansion)
        x2 = int((box['Left']+box['Width'])*width) * (1+expansion)
        y2 = int((box['Top']+box['Height'])*height) * (1+expansion)
        #print(f'crop: {x1}, {y1}, {x2}, {y2}')

        image_crop = image.crop((x1,y1,x2,y2))
        stream = io.BytesIO()
        image_crop.save(stream, format='JPEG')
        image_crop_binary = stream.getvalue()

        points = (
                (x1, y1),
                (x2, y1),
                (x2, y2),
                (x1, y2),
                (x1, y1)
                )
        draw.line(points, fill='#00d400', width=4)
        # Alternatively can draw rectangle. However you can't set line width.
        #draw.rectangle([x1, y1, x2, y2], outline='#00d400') 

        try:
            response = rekognition.search_faces_by_image(
                    CollectionId = 'family_collection',
                    Image = {'Bytes':image_crop_binary})
            #Blob of image bytes up to 5 MBs.
        except rekognition.exceptions.InvalidParameterException:
            print('Error: rekognition.exceptions.InvalidParameterException:')
            continue

        fullName = 'no match find'
        faceId = 0
        confidence = 0
        if len(response['FaceMatches']) > 0:
            for match in response['FaceMatches']:
                faceId = match['Face']['FaceId']
                confidence = match['Face']['Confidence']

                person = dynamodb.get_item(
                        TableName = 'family_collection',
                        Key = {'RekognitionId':{'S':faceId}})

                if 'Item' in person:
                    fullName = person['Item']['FullName']['S']
                else:
                    fullName = 'new data'

        #print(f'name:{fullName}, faceID:{faceId}, confidence:{confidence}')
        text.insert(END, f'----------\n')
        text.insert(END, f'Name:{fullName}, FaceID:{faceId}, Confidence:{confidence}\n\n')
        text.insert(END, f'The detected face is between {str(face["AgeRange"]["Low"])} and {str(face["AgeRange"]["High"])} years old\n')
        text.insert(END, f'Smile: {str(face["Smile"]["Value"])}\n')
        text.insert(END, f'Emotions: {str(face["Emotions"][0]["Type"])}\n')
        text.insert(END, f'Gender: {str(face["Gender"]["Value"])}\n')
        text.insert(END, f'\n')

    nFaces = len(all_faces)
    tEnd = time.perf_counter()
    tCost = tEnd - tStart
    text.insert(1.0, f'Find {nFaces} faces, Time Elapsed: {tCost:.2f} sec\n')
    image.show()

if __name__ == "__main__":
    root = Tk()
    root.title('rekognition demo')
    scroll = Scrollbar(root)
    text = Text(root, width=150, height=40)

    text.config(yscrollcommand=scroll.set, font=('Arial', 8, 'bold', 'italic'))
    scroll.config(command=text.yview)

    scroll.grid(row=2, column=2, sticky=NS)
    text.grid(row=2, column=1, sticky=W)

    button = Button(text='select file', width=30, command=openFile)
    button.grid(row=1, column=1, columnspan=2)

    text.insert(END, 'initialize\n')
    root.mainloop()
