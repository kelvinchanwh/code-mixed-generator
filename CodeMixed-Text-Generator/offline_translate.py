from transformers import MarianMTModel, MarianTokenizer
from typing import Sequence

class Translator:
    def __init__(self, source_lang: str, dest_lang: str) -> None:
        if dest_lang == "ko":
            self.model_name = f'Helsinki-NLP/opus-mt-tc-big-en-ko'
        else:
            self.model_name = f'Helsinki-NLP/opus-mt-{source_lang}-{dest_lang}'
        self.model = MarianMTModel.from_pretrained(self.model_name)
        self.tokenizer = MarianTokenizer.from_pretrained(self.model_name)
        
    def translate(self, texts: Sequence[str]) -> Sequence[str]:
        tokens = self.tokenizer(list(texts), return_tensors="pt", padding=True)
        translate_tokens = self.model.generate(**tokens, max_new_tokens=512)
        return [self.tokenizer.decode(t, skip_special_tokens=True) for t in translate_tokens]
        
        
marian_en_jap = Translator('en', 'jap')
marian_en_zh = Translator('en', 'zh')
marian_en_ko = Translator('en', 'ko')

print ("Setup Complete")
with open("data/en-to-zh-input_lang1", "r") as input_f:
    print ("Read File Complete")
    with open("data/ja", "w+") as ja:
        with open("data/zh", "w+") as zh:
            with open("data/kr", "w+") as kr:
                counter = 0
                for line in input_f:
                    if counter % 100 == 0:
                        print (str(counter) + " sentences translated")
                    ja.write(marian_en_jap.translate([line])[0] + "\n")
                    zh.write(marian_en_zh.translate([line])[0] + "\n")
                    kr.write(marian_en_ko.translate([line])[0] + "\n")
                    counter += 1