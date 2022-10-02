from urllib.request import Request, urlopen
from langdetect import detect
from googletrans import Translator


def scrape_google_image(vocab:str, input_language:list = ["en"]):
    """
    scrape_google_image(): by using urllib module, it will scrape the first image on the google image page

    Args:
        vocab (str): a single vocabulary in string

    Returns:
        str: image url
    """
    
    # detect language
    lang = detect(vocab)
    
    # If the vocab is not in English, translate it before getting the details
    if "es" in input_language:
        translator = Translator()
        vocab = translator.translate(vocab, src="es", dest='en').text
    elif lang != "en":
        translator = Translator()
        vocab = translator.translate(vocab, src=lang, dest='en').text
        
    vocab = vocab.replace(' ', '+')
    
    req = Request(
        url = f'https://www.google.com/search?q={vocab}&tbm=isch', 
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    webpage = urlopen(req).read().decode()

    first_src = webpage.find('encrypted') - 8

    url_count = 0
    for i in webpage[first_src:]:
        if i == "\"":
            break
        url_count += 1

    return webpage[first_src:first_src + url_count]