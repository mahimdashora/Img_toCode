from fastapi import FastAPI, Request, File, UploadFile, BackgroundTasks
from fastapi.templating import Jinja2Templates
import shutil
import ocr
import os
import uuid
import json

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/v1/extract_text")
async def extract_text(image: UploadFile = File(...)):
    temp_file = _save_file_to_disk(image, path="temp", save_as="temp")
    text = await ocr.read_image(temp_file)
    return {"filename": image.filename, "text": text}

@app.post("/api/v1/bulk_extract_text")
#async
async def bulk_extract_text(request: Request, bg_task: BackgroundTasks):
    #await
    images = await request.form()
    folder_name = str(uuid.uuid4())
    os.mkdir(folder_name)

    for image in images.values():
        temp_file = _save_file_to_disk(image, path=folder_name, save_as=image.filename)

    bg_task.add_task(ocr.read_images_from_dir, folder_name, write_to_file=True)
    
    return {"task_id": folder_name, "num_files": len(images)}



@app.get("/api/v1/bulk_output/{task_id}")
#asyncs
def bulk_output(task_id):
    text_map = {}
    visited=[]
   # n=len(os.listdir(task_id))
   # visited=[0]*n and visited[file_]==0
    for file_ in os.listdir(task_id):
        if file_.endswith("txt") and file_ not in visited :
            text_map[file_] = open(os.path.join(task_id, file_)).read()
            visited.append(file_)
            #s.add(task_id)
  #Convert image to grayscale
         
    return {"task_id": task_id, "output": text_map}

def _save_file_to_disk(uploaded_file, path=".", save_as="default"):
    extension = os.path.splitext(uploaded_file.filename)[-1]
    temp_file = os.path.join(path, save_as + extension)
    with open(temp_file, "wb") as buffer:
        shutil.copyfileobj(uploaded_file.file, buffer)
    return temp_file