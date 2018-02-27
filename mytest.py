# -*- coding: UTF-8 -*_
import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = 'E:\\Tesseract-OCR\\tesseract.exe'

pytesseract.pytesseract.img_mode
img = Image.open('C:\\Users\\chenyan\\Desktop\\123.png')
s = pytesseract.image_to_string(img)
print(s)
