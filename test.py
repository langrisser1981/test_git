import boto3
import io
from PIL import ImageDraw, ExifTags, ImageColor
from PIL import Image as PilImage

from tkinter import filedialog
from tkinter import *

root = Tk()

def fileopen():
    filename =  filedialog.askopenfilename(initialdir = "/",title = "Select file",filetypes = (("jpeg files","*.jpg"),("all files","*.*")))
    print(filename)
    text.delete(1.0, END)
    text.insert(END, filename+'\n')
    loadimage()

def loadimage():
    bucket="rekognition-20181204"
    photo="input.jpg"
    client=boto3.client('rekognition')

    # Load image from S3 bucket
    s3_connection = boto3.resource('s3')
    s3_object = s3_connection.Object(bucket,photo)
    s3_response = s3_object.get()

    stream = io.BytesIO(s3_response['Body'].read())
    image = PilImage.open(stream)

    if hasattr(image, '_getexif'):
        orientation = 0x0112
        exif = image._getexif()
        if exif is not None and orientation in exif.keys():
            orientation = exif[orientation]
            rotations = {
                    3: PilImage.ROTATE_180,
                    6: PilImage.ROTATE_270,
                    8: PilImage.ROTATE_90
                    }

            if orientation in rotations.keys():
                image = image.transpose(rotations[orientation])
    
    #Call DetectFaces 
    response = client.detect_faces(Image={'S3Object': {'Bucket': bucket, 'Name': photo}},
        Attributes=['ALL'])

    imgWidth, imgHeight = image.size  
    draw = ImageDraw.Draw(image)  
                    

    # calculate and display bounding boxes for each detected face       
    print('Detected faces for ' + photo)    
    for faceDetail in response['FaceDetails']:
        text.insert(END, 'The detected face is between ' + str(faceDetail['AgeRange']['Low']) + ' and ' + str(faceDetail['AgeRange']['High']) + ' years old\n')

        box = faceDetail['BoundingBox']
        left = imgWidth * box['Left']
        top = imgHeight * box['Top']
        width = imgWidth * box['Width']
        height = imgHeight * box['Height']
                
        text.insert(END, 'Smile: {0:}'.format(str(faceDetail['Smile']['Value']))+'\n')
        text.insert(END, 'Emotions: {0:}'.format(str(faceDetail['Emotions'][0]['Type']))+'\n')
        text.insert(END, 'Gender: {0:}'.format(str(faceDetail['Gender']['Value']))+'\n')
        print('Left: ' + '{0:.0f}'.format(left))
        print('Top: ' + '{0:.0f}'.format(top))
        print('Face Width: ' + "{0:.0f}".format(width))
        print('Face Height: ' + "{0:.0f}".format(height))

        points = (
            (left,top),
            (left + width, top),
            (left + width, top + height),
            (left , top + height),
            (left, top)

        )
        draw.line(points, fill='#00d400', width=2)

        # Alternatively can draw rectangle. However you can't set line width.
        #draw.rectangle([left,top, left + width, top + height], outline='#00d400') 
    image.show()

if __name__ == "__main__":
    root.title('rekognition test')
    scroll = Scrollbar(root)

    text = Text(root, width=30, height=8)

    text.config(yscrollcommand=scroll.set, font=('Arial', 8, 'bold', 'italic'))
    scroll.config(command=text.yview)

    scroll.grid(row=2, column=2, sticky=NS)
    text.grid(row=2, column=1, sticky=W)

    button = Button(text='choose file', width=30, command=fileopen)
    button.grid(row=1, column=1, columnspan=2)

    text.insert(END, 'init\n')
    root.mainloop()
