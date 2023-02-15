from collections import Counter

lang_unicodes = [('\u0021','\u007F')
	]

def dect_word_latin(word):
	latin = 0
	nonlatin = 0
	for ch in word:
		latin = False
		for block in lang_unicodes:
			if ch >= block[0] and ch <= block[1]:
				latin = True
				break
		if latin == False:
			nonlatin += 1
		else:
			latin += 1
			
	assert latin + nonlatin == len(word), "{} does not have total count of {} latin + {} non-latin chars".format(word, latin, nonlatin)
	return True if latin > nonlatin else False

print(dect_word_latin('你好，我的名字是瑞特維克'))