import cnocr
import numpy
import PIL.Image as Image
import PIL.ImageGrab as ImageGrab
import pyautogui
import random
import signal
import sqlite3
import time


# 定义模拟器窗口
screen_x1 = 523
screen_y1 = 0
screen_x2 = 1121
screen_y2 = 1020

learn_mode = False

screen_width = screen_x2 - screen_x1
screen_height = screen_y2 - screen_y1

last_insert_sql = ''
last_update_sql = ''
stop_flag = False

db = sqlite3.connect('data.db')
cursor = None
ocr = None

raw_text = {}


def init():
    global db, ocr
    db.execute('create table if not exists knowledge(id integer primary key autoincrement,'
               'question varchar(60),'
               'answer varchar(20)) ')
    db.commit()
    ocr = cnocr.CnOcr()


# 查询数据
def query(question: str):
    global cursor, db
    cursor = db.cursor()
    sql = 'select * from knowledge where question = \'' + question + '\''
    data = cursor.execute(sql)
    return data.fetchone()


# 记录数据
def record(question: str, answer: str):
    global cursor, db, last_insert_sql
    sql = 'insert into knowledge(question, answer) select \'' + question + '\',\'' + answer + '\'' + \
          'where not exists (select * from knowledge where question=\'' + question + '\'' + \
          'and answer=\'' + answer + '\')'
    if last_insert_sql != sql:
        print('======= 正在记录 =========')
        db.execute(sql)
        db.commit()
        last_insert_sql = sql


# 获取按钮的颜色
def get_button_color(image: Image.Image):
    pixels = image.load()
    lt0 = pixels[0, 0]
    rb0 = pixels[image.size[0] - 1, image.size[1] - 1]
    if lt0 == rb0 == (243, 232, 223):
        lt1 = pixels[5, 5]
        rb1 = pixels[image.size[0] - 6, image.size[1] - 6]
        if lt1 == rb1 == (255, 255, 255):
            return '白色'
        elif lt1 == rb1 == (203, 46, 45):
            return '红色'
        elif lt1 == rb1 == (66, 193, 138):
            return '绿色'
    return '其他色'


def get_text(img: Image):
    global ocr
    global raw_text
    data = ocr.ocr(numpy.array(img))
    result = ''
    for line in data:
        for word in line:
            result = result + word
    return result


# 开始处理
def auto_process():
    whole_screen = ImageGrab.grab(bbox=(screen_x1, screen_y1, screen_x2, screen_y2))
    question_img = whole_screen.crop(box=(25, 356, 533, 445))
    a_img = whole_screen.crop(box=(99, 468, 458, 550))
    b_img = whole_screen.crop(box=(99, 564, 458, 645))
    c_img = whole_screen.crop(box=(99, 660, 458, 741))
    d_img = whole_screen.crop(box=(99, 757, 458, 837))
    continue_img = whole_screen.crop(box=(216, 768, 348, 806))
    count_img = whole_screen.crop(box=(260, 255, 294, 286)).convert('L')
    a_color = get_button_color(a_img)
    b_color = get_button_color(b_img)
    c_color = get_button_color(c_img)
    d_color = get_button_color(d_img)

    if get_text(continue_img) == '继续挑战':
        pyautogui.press('D')
        return

    if a_color == b_color == c_color == d_color == '白色':
        raw_text['q'] = get_text(question_img)
        raw_text['a'] = get_text(a_img)
        raw_text['b'] = get_text(b_img)
        raw_text['c'] = get_text(c_img)
        raw_text['d'] = get_text(d_img)

        data = query(raw_text['q'])
        print('data: ', data)

        if data is None or data[2] == '' or raw_text['q'] == '':
            print('！未查询到该题目')
            if learn_mode:
                # 进行盲选
                select = random.randint(1, 4)
                print('准备盲选')
                if select == 1:
                    pyautogui.press('A')
                    print('盲选答案为A')
                elif select == 2:
                    pyautogui.press('B')
                    print('盲选答案为B')
                elif select == 3:
                    pyautogui.press('C')
                    print('盲选答案为C')
                elif select == 4:
                    pyautogui.press('D')
                    print('盲选答案为D')
        elif data[2] == raw_text['a']:
            print('查询到正确答案A')
            pyautogui.press('A')
        elif data[2] == raw_text['b']:
            print('查询到正确答案B')
            pyautogui.press('B')
        elif data[2] == raw_text['c']:
            print('查询到正确答案C')
            pyautogui.press('C')
        elif data[2] == raw_text['d']:
            print('查询到正确答案D')
            pyautogui.press('D')

    if raw_text.get('q') is not None:
        if a_color == '绿色' and raw_text['a'] is not None:
            print('记录A答案为正确答案')
            record(raw_text['q'], raw_text['a'])
        elif b_color == '绿色' and raw_text['b'] is not None:
            print('记录B答案为正确答案')
            record(raw_text['q'], raw_text['b'])
        elif c_color == '绿色' and raw_text['c'] is not None:
            print('记录C答案为正确答案')
            record(raw_text['q'], raw_text['c'])
        elif d_color == '绿色' and raw_text['d'] is not None:
            print('记录D答案为正确答案')
            record(raw_text['q'], raw_text['d'])


# 中止程序
def stop(signum, frame):
    global stop_flag
    stop_flag = True
    print('you pressed ctrl + c,the program is exiting.')


if __name__ == '__main__':
    print('start')
    init()
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    while not stop_flag:
        auto_process()
        time.sleep(0.1)
