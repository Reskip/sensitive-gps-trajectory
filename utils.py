class CPrint(object):
    TEXT_BOX = None

    def __init__(self):
        pass

    def set_text_box(text_box):
        CPrint.TEXT_BOX = text_box

    def print(text):
        print(text)
        if CPrint.TEXT_BOX:
            CPrint.TEXT_BOX.insert("end", text+"\n")
