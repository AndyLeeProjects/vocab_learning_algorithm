
from secret import secret
import requests, json
from googletrans import Translator
from langdetect import detect

def connect_lingua_api(vocabs:list, languages:list) -> dict:
    """
    connect_lingua_api()
        Using LinguaAPI, the definitions, examples, synonyms and contexts are gathered.
        Then they are stored into a dictionary format. 

    """
    vocab_dic = {}
    for vocab in vocabs:
        
        # detect language
        lang = detect(vocab)
        
        # If the vocab is not in English, translate it before getting the details
        if lang in languages:
            translator = Translator()
            vocab_orig = vocab
            vocab = translator.translate(vocab, src=lang, dest='en').text
        else:
            vocab_orig = None
        
        url = "https://lingua-robot.p.rapidapi.com/language/v1/entries/en/" + \
            vocab.lower().strip(' ')
        headers = {
            "X-RapidAPI-Key": secret.lingua_API('API Key'),
            "X-RapidAPI-Host": "lingua-robot.p.rapidapi.com"
        }
        
        # Request Data
        response = requests.request("GET", url, headers=headers)
        data = json.loads(response.text)
        audio_url = None

        # DEFINE vocab_info
        # try: Some vocabularies do not have definitions (ex: fugazi)
        try:
            vocab_dat = data['entries'][0]['lexemes']
        except IndexError:
            vocab_dat = None
            definitions = None
            synonyms = None
            examples = None

        if vocab_dat != None:
            # GET DEFINITIONS
            # try: If the definition is not in Lingua Dictionary, output None

            definitions = [vocab_dat[j]['senses'][i]['definition']
                            for j in range(len(vocab_dat)) for i in range(len(vocab_dat[j]['senses']))]
            definitions = definitions[:5]
            
            # GET AUDIO URLS
            try:
                for i in range(len(data['entries'][0]['pronunciations'])):
                    try:
                        audio_url = data['entries'][0]['pronunciations'][i]['audio']['url']
                        break
                    except:
                        pass
            except KeyError:
                pass

            # GET SYNONYMS
            # try: If synonyms are not in Lingua Dictionary, output None
            try:
                synonyms = [vocab_dat[j]['synonymSets'][i]['synonyms']
                            for j in range(len(vocab_dat)) for i in range(len(vocab_dat[j]['synonymSets']))]
            except KeyError:
                synonyms = None

            # GET EXAMPLES
            try:
                examples = [vocab_dat[j]['senses'][i]['usageExamples']
                            for j in range(len(vocab_dat)) for i in range(len(vocab_dat[j]['senses']))
                            if 'usageExamples' in vocab_dat[j]['senses'][i].keys()]
            except:
                examples = None
        if vocab_orig != None:
            vocab = vocab_orig
        vocab_dic.setdefault(vocab, []).append({'definitions': definitions,
                                                'examples': examples,
                                                'synonyms': synonyms,
                                                'audio_url': audio_url})
    return vocab_dic