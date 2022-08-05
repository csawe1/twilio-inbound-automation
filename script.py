from twilio.rest import Client
from datetime import datetime
import requests, os, os.path, shutil
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import gspread

ACCOUNT_SID = "" # Enter the twilio account SID
AUTH_TOKEN = ""  # Enter the twilio account auth token
base_url = "https://api.twilio.com"
client = Client(ACCOUNT_SID, AUTH_TOKEN)
messages = client.messages.list()
# messages = client.messages.list(date_sent=datetime.date(datetime.now()))
sa = gspread.service_account(filename="creds.json")

auth = GoogleAuth()
auth.LocalWebserverAuth()
drive = GoogleDrive(auth)
folder = "1bDqrxyzvIHBvLbskXsuni4DE37QWum3s"

sheet = sa.open("Example")
worksheet = sheet.worksheet("Sheet1")
messages = client.messages.list()
size = len(worksheet.get_values())
counter = 1

numbers = []

for message in messages:
    if message.from_ not in numbers:
        numbers.append(message.from_)
  
for number in numbers:   
    upload_data = []
    text = ""
    images = []
    videos = []
    for message in messages:
        if message.from_ == number and message.direction == "inbound":
            if message.body:
                if text == "":
                    text = text + message.body
                else:
                    text = text + ". " + message.body  
            elif message.media:
                    MessageSid = message.sid
                    try:
                        message = client.messages(MessageSid).fetch()
                        media = message.media.list()
                        for medium in media:
                            Sid = medium.sid
                            data = client.messages(MessageSid).media(Sid).fetch()
                            new_url = f"{base_url}{data.uri}"
                            download_url = new_url.replace(".json", "")
                            data_type = data.content_type.split("/")[1]
                            download_dir = f"./images/{Sid}.{data_type}"
                            print("Downloading...")
                            stream = requests.get(download_url)
                            with open(download_dir, "wb") as local_file:
                                local_file.write(stream.content)
                            print("Downloaded.")       
                    except Exception as e:
                        print(e)
    
    directory = "./images"
    for file in os.listdir(directory):
        print("Uploading to drive...")
        filename = os.path.join(directory, file)
        name, extension = os.path.splitext(file)
        googlefile = drive.CreateFile({'parents': [{'id': folder}], 'title': file})
        googlefile.SetContentFile(filename)
        googlefile.Upload()
        print("Uploaded.")
        if extension in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif']:
            images.append('=image("https://drive.google.com/uc?export=view&id={}", 4, 200, 200)'.format(googlefile['id']))
            googlefile.content.close()
        else:
            videos.append(googlefile['id'])
            googlefile.content.close()
        
        
    upload_data.append(str(datetime.date(datetime.now())))
    upload_data.append(number)
    upload_data.append(text)
    for image in images:
        upload_data.append(image)
    for video in videos:
        upload_data.append(video)
    print("Inserting into google sheets...")
    worksheet.insert_row(upload_data, (size+counter), value_input_option="USER_ENTERED")  
    print("Done.")
    counter += 1    
    
    try:
        shutil.rmtree("images")
    except OSError as e:
        print("Error: %s - %s." %(e.filename,e.strerror))
    if not os.path.exists("./images"):
        os.mkdir("images")
