import boto3
import cv2
import time
import io
from PIL import Image, ImageDraw, ExifTags, ImageColor
'''
------------------------------------------------------------------------
Part 1: 攝影機記錄使用者
------------------------------------------------------------------------
'''
cap = cv2.VideoCapture(0) #啟用(零號)相機
#参数cv2.CAP_DSHOW是微软特有的，用于防止释放摄像头时的[ WARN:0] terminating async callback警告
milli = int(round(time.time() * 1000))

while(True):
    

  milli = 2*1000
  cv2.waitKey(milli)
  
  time.sleep(3) ##延遲執行的秒數: (設定3秒)  
  
  ret, frame = cap.read()  #捕獲一幀影象
  cv2.imshow('frame', frame)
  
  cv2.imwrite('guest.jpg', frame)
  break


cap.release()  #關閉相機
cv2.destroyAllWindows()  #關閉視窗
'''
------------------------------------------------------------------
Part 2: AWS帳號－－連結用金鑰儲存 (executable)
------------------------------------------------------------------
'''
ACCESS_KEY = '---------------'
SECRET_KEY = '---------------'

'''
-------------------------------------------------------------------------------------------﹁
Part 3: 照片傳至Rekongnize進行偵測   (executable)                         |  
--------------------------------------------------------------------------------------------」
'''

def detect_labels(photo):
    # 要讀取之檔案
    no_mask = 0

    photo = 'guest.jpg'
    with open(photo, 'rb') as imgfile:
     imgbytes = imgfile.read()

    client=boto3.client('rekognition',region_name='us-east-1',
                        aws_access_key_id=ACCESS_KEY,
                        aws_secret_access_key=SECRET_KEY)

    response = client.detect_protective_equipment(Image={'Bytes': imgbytes}, 
        SummarizationAttributes={'MinConfidence':80, 'RequiredEquipmentTypes':['FACE_COVER']})
        
 
    print('Detected PPE for people in image ' + photo) 
    print('\nDetected people\n---------------')   
    for person in response['Persons']:
        

        body_parts = [person['BodyParts'][0]]
        if len(body_parts) == 0:
                print ('No body parts found')
        else:
            for body_part in body_parts:
                ppe_items = body_part['EquipmentDetections']
                if len(ppe_items) ==0:
                   # print ('\t\tNo PPE detected on ' + body_part['Name'])
                    no_mask += 1
                #else:    
                    #for ppe_item in ppe_items:
                      #  print('\t\t' + ppe_item['Type'] + '\n\t\t\tConfidence: ' + str(ppe_item['Confidence'])) 
                       # print('\t\tGreat! You are wearing a mask!')
                        
            #print()
        #print()

    print()
    return len(response['Persons']), no_mask

#Draw frames and show
def detect_ppe(photo, confidence):

    fill_green='#00d400'
    fill_red='#ff0000'
    fill_yellow='#ffff00'
    line_width=3

    #open image and get image data from stream.
    image = Image.open(open(photo,'rb'))
    stream = io.BytesIO()
    image.save(stream, format=image.format)    
    image_binary = stream.getvalue()
    imgWidth, imgHeight = image.size  
    draw = ImageDraw.Draw(image)  

    client=boto3.client('rekognition', region_name='us-east-1',
                        aws_access_key_id=ACCESS_KEY,
                        aws_secret_access_key=SECRET_KEY)

    response = client.detect_protective_equipment(Image={'Bytes': image_binary})

    for person in response['Persons']:
        
        found_mask=False

        for body_part in person['BodyParts']:
            ppe_items = body_part['EquipmentDetections']
                 
            for ppe_item in ppe_items:
                #found a mask 
                if ppe_item['Type'] == 'FACE_COVER':
                    fill_color=fill_green
                    found_mask=True
                    # check if mask covers face
                    if ppe_item['CoversBodyPart']['Value'] == False:
                        fill_color=fill='#ff0000'
                    # draw bounding box around mask
                    box = ppe_item['BoundingBox']
                    left = imgWidth * box['Left']
                    top = imgHeight * box['Top']
                    width = imgWidth * box['Width']
                    height = imgHeight * box['Height']
                    points = (
                            (left,top),
                            (left + width, top),
                            (left + width, top + height),
                            (left , top + height),
                            (left, top)
                        )
                    draw.line(points, fill=fill_color, width=line_width)

                     # Check if confidence is lower than supplied value       
                    if ppe_item['CoversBodyPart']['Confidence'] < confidence:
                        #draw warning yellow bounding box within face mask bounding box
                        offset=line_width+ line_width 
                        points = (
                                    (left+offset,top + offset),
                                    (left + width-offset, top+offset),
                                    ((left) + (width-offset), (top-offset) + (height)),
                                    (left+ offset , (top) + (height -offset)),
                                    (left + offset, top + offset)
                                )
                        draw.line(points, fill=fill_yellow, width=line_width)
                
        if found_mask==False:
            # no face mask found so draw red bounding box around body
            box = person['BoundingBox']
            left = imgWidth * box['Left']
            top = imgHeight * box['Top']
            width = imgWidth * box['Width']
            height = imgHeight * box['Height']
            points = (
                (left,top),
                (left + width, top),
                (left + width, top + height),
                (left , top + height),
                (left, top)
                )
            draw.line(points, fill=fill_red, width=line_width)

    image.show()
    image.save("123.jpg")



def main():
    photo='guest.jpg'
    person_count,no_mask = detect_labels(photo)
    print("Persons detected: " + str(person_count))
    print("No-mask detected: ", no_mask)
    confidence=80
    detect_ppe(photo, confidence)
    #if no_mask !=0:
        #alert()
        #sendGmailAlert()

if __name__ == "__main__":
    main()

# 警示音?播放 (用不到就算了)
#pip install playsound
def alert():
  from playsound import playsound
  playsound('path/to/your/file/', block=True)

# 聯動e-mail，做系統反饋 (executable)

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from pathlib import Path
import smtplib

def sendGmailAlert():
  content = MIMEMultipart()  #建立MIMEMultipart物件
  content["subject"] = "Someone is spreading virus!"  #郵件標題
  content["from"] = "cjun5217@gmail.com"  #寄件者
  content["to"] = "yichin421@gmail.com" #收件者
  content.attach(MIMEText("Alert！ That idiot didn't wear a mask！"))  #郵件內容
  content.attach(MIMEImage(Path("123.jpg").read_bytes()))  # 郵件圖片內容


  with smtplib.SMTP(host="smtp.gmail.com", port="587") as smtp:  # 設定SMTP伺服器
    try:
        smtp.ehlo()  # 驗證SMTP伺服器
        smtp.starttls()  # 建立加密傳輸
        smtp.login("cjun5217@gmail.com", "-----------")  # 登入寄件者gmail
        smtp.send_message(content)  # 寄送郵件
        print("Complete!")
    except Exception as e:
        print("Error message: ", e)

