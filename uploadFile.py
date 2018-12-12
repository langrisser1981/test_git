import boto3

s3 = boto3.resource('s3')

with open('files', 'r') as f:
    lines = f.readlines()

images = []
for i in range(len(lines)):
    image = lines[i].split(',', 1)
    image[1] = image[1].strip()
    #print(image)
    images.append(image)

for image in images:
    fileName = image[0]
    filePath = 'refs/'+fileName
    key = 'index/'+fileName
    fullName = image[1]
    with open(filePath, 'rb') as f:
        object = s3.Object('rekognition-20181204', key)
        ret = object.put(
                Body = f,
                Metadata = {'fullName':fullName})


