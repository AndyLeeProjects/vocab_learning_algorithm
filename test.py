from googletrans import Translator
from langdetect import detect

translator = Translator()
result = translator.translate("홍어", src='ko', dest='en').text
print(result)

print(detect("파죽지세"))