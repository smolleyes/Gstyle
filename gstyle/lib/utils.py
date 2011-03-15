#-*- coding: UTF-8 -*-
import re
#
## matches a character entity reference (decimal numeric, hexadecimal numeric, or named).
#charrefpat = re.compile(r'&(#(\d+|x[\da-fA-F]+)|[\w.:-]+);?')
#def decode(text):
#    """
#        Decode HTML entities in the given.
#        text should be a unicode string, as that is what we insert.
#
#        This is from:
#            http://zesty.ca/python/scrape.py
#    """
#    from htmlentitydefs import name2codepoint
#    if type(text) is unicode:
#        uchr = unichr
#    else:
#        uchr = lambda value: value > 255 and unichr(value) or chr(value)
#
#    def entitydecode(match, uchr=uchr):
#        entity = match.group(1)
#        if entity.startswith('#x'):
#            return uchr(int(entity[2:], 16))
#        elif entity.startswith('#'):
#            return uchr(int(entity[1:]))
#        elif entity in name2codepoint:
#            return uchr(name2codepoint[entity])
#        else:
#            return match.group(0)
#    return charrefpat.sub(entitydecode, text)


import htmlentitydefs

def translate_html(text_html):
    code = htmlentitydefs.codepoint2name
    new_text = ""
    dict_code = dict([(unichr(key),value) for key,value in code.items()])
    for key in text_html:
#        key = unicode(key)
        if dict_code.has_key(key):
            new_text += "&%s;" % dict_code[key]
        else:
            new_text += key
    return new_text



def htmlentitydecode(s):
    # First convert alpha entities (such as &eacute;)
    # (Inspired from [url]http://mail.python.org/pipermail/python-list/2007-June/443813.html[/url])
    def entity2char(m):
        entity = m.group(1)
        if entity in htmlentitydefs.name2codepoint:
            return unichr(htmlentitydefs.name2codepoint[entity])
        return u" "  # Unknown entity: We replace with a space.
    expression = u'&(%s);' % u'|'.join(htmlentitydefs.name2codepoint)
    t = re.sub(expression, entity2char, s)


    # Then convert numerical entities (such as &#38;#233;)
    t = re.sub(u'&#38;#(d+);', lambda x: unichr(int(x.group(1))), t)

    # Then convert hexa entities (such as &#38;#x00E9;)
    return re.sub(u'&#38;#x(w+);', lambda x: unichr(int(x.group(1),16)), t)

if __name__ == "__main__":
    str_html = u"Belle image étoile.jpg"
#    unichr("é")
    result = translate_html(str_html)
    print result
    out = htmlentitydecode(result)
    print out
