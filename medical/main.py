from fastapi import FastAPI, File, UploadFile
from typing import List
from chatbot import calling_langgarph

app = FastAPI()

@app.get("/")
def greet(): 
    return "Hello world"

@app.post("/saveFiles")
async def uploadDocuments(file: UploadFile = File(...)):
    file_ext = file.filename.split(".")[-1].lower()
    temp_path = f"temp_{file.filename.replace(' ', '_')}"
    with open(f'savedFiles/{file.filename}', "wb") as f:
        f.write(file.file.read())
    return "Successully Saved the file"

@app.post("/saveMultipleFiles")
async def uploadDocuments(files: List[UploadFile] = File(...)):
    for file in files :
        with open(f'savedFiles/{file.filename}', "wb") as f:
            f.write(file.file.read())
    return "Successully Saved all files"

@app.get("/userInput/{inputQuestion}")
def userInputQuestion(inputQuestion):
    return calling_langgarph(inputQuestion)

