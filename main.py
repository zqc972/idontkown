import pyautogui
import PIL.ImageGrab as ImageGrab
import PIL.Image as Image
import imagehash
import signal
import sqlite3
import random
import time
import os

# 修改此处进行定义操作窗口区域

pre_frame = None  # 上一帧
cur_frame = None  # 当前帧
raw_hash = ['', '', '', '']  # 用于记录未选择状态下ABCD的hash值
last_insert_sql = ''
last_update_sql = ''
stop_flag = False

db = sqlite3.connect('data.db')


# 初始化
def init():
    cursor = db.cursor()
    cursor.execute('create table if not exists data (id integer primary key autoincrement,'
                   'question varchar(16) ,'
                   'answer varchar(16))')


# 通过问题的hash值判断是否为新题目
def query_question(q_hash: str):
    cursor = db.cursor()
    cursor.execute('select * from data where question =\'' + q_hash + '\'')
    data = cursor.fetchall()
    if len(data) > 0:
        return True
    else:
        return False


# 查询答案
def query_answer(q_hash: str):
    cursor = db.cursor()
    cursor.execute('select * from data where question = \'' + q_hash + '\'')
    data = cursor.fetchall()
    if data is not None:
        return data
    else:
        return None


# 插入数据
def record(question_hash: str, answer_hash: str):
    global last_insert_sql
    sql = 'insert into data(question,answer) SELECT \'' + question_hash + '\',\'' + answer_hash + '\' ' + \
          'where not exists (select * from data where question = \'' + question_hash + '\' and answer=\'' + \
          answer_hash + '\')'
    # 避免对同一正确答案多次存储
    if sql != last_insert_sql:
        logfile = open('e:/insertlog.txt', 'a')
        logfile.write(sql + '\n')
        logfile.close()
        db.execute(sql)
        db.commit()
        last_insert_sql = sql


# 更新数据
def update(question_hash: str, answer_hash: str):
    global last_update_sql
    sql = 'update data set answer=\'' + answer_hash + '\''
    # 避免对同一正确答案多次存储
    if sql != last_update_sql:
        logfile = open('e:/updatelog.txt', 'a')
        logfile.write(sql)
        logfile.close()
        db.execute(sql)
        db.commit()
        last_update_sql = sql


# 获取按钮的颜色
def get_button_color(image: Image.Image):
    pixels = image.load()
    lt0 = pixels[0, 0]
    rb0 = pixels[image.size[0] - 1, image.size[1] - 1]
    if lt0 == rb0 == (243, 232, 223):
        lt1 = pixels[3, 3]
        rb1 = pixels[image.size[0] - 4, image.size[1] - 4]
        if lt1 == rb1 == (255, 255, 255):
            return '白色'
        elif lt1 == rb1 == (203, 46, 45):
            return '红色'
        elif lt1 == rb1 == (66, 193, 138):
            return '绿色'
    return '其他色'


# 处理逻辑
def auto_process():
    # 与机器人pk自动进入下一局
    continue_button = ImageGrab.grab(bbox=(755, 775, 850, 800))
    hash_continue_button = str(imagehash.dhash(continue_button))
    if hash_continue_button == '9555555567555166':
        pyautogui.press('D')

    # 可改进为截图一整个区域后，再将题目和各选项给切分出来
    img_question = ImageGrab.grab(bbox=(550, 350, 1054, 454))
    img_a = ImageGrab.grab(bbox=(622, 468, 982, 550))
    img_b = ImageGrab.grab(bbox=(622, 564, 982, 646))
    img_c = ImageGrab.grab(bbox=(622, 660, 982, 742))
    img_d = ImageGrab.grab(bbox=(622, 756, 982, 838))

    global pre_frame
    global cur_frame
    cur_frame = ImageGrab.grab(bbox=(525, 32, 1079, 1018))
    if pre_frame is not None:
        hash_cur_frame = imagehash.dhash(cur_frame)
        hash_pre_frame = imagehash.dhash(pre_frame)
        if hash_cur_frame != hash_pre_frame:
            # print('监测区域中有移动..')
            pre_frame = cur_frame
            return

    hash_question = str(imagehash.dhash(img_question))
    hash_a = str(imagehash.dhash(img_a))
    color_a = get_button_color(img_a)
    hash_b = str(imagehash.dhash(img_b))
    color_b = get_button_color(img_b)
    hash_c = str(imagehash.dhash(img_c))
    color_c = get_button_color(img_c)
    hash_d = str(imagehash.dhash(img_d))
    color_d = get_button_color(img_d)

    # 记录原始答案的图像hash值，以备在公布正确答案后存入数据库
    if color_a == color_b == color_c == color_d == '白色':
        raw_hash[0] = hash_a
        raw_hash[1] = hash_b
        raw_hash[2] = hash_c
        raw_hash[3] = hash_d
        print('======   原始答案hash值已记录 =======')
        if not os.path.exists('debug/' + hash_question + '.png'):
            cur_frame.save('debug/' + hash_question + '.png')

    # 若数据库中未收录该题目
    if not query_question(str(hash_question)):
        # print('               XXX未找到该题目XXX')
        # 检测答案颜色，判断当前是已作答还是未作答状态
        if color_a == color_b == color_c == color_d == '白色':
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
        # 选择后对正确答案记录
        elif color_a == '绿色':
            print('正在将答案A记录为正确答案,hash:' + raw_hash[0])
            record(hash_question, raw_hash[0])
        elif color_b == '绿色':
            print('正在将答案B记录为正确答案,hash:' + raw_hash[1])
            record(hash_question, raw_hash[1])
        elif color_c == '绿色':
            print('正在将答案C记录为正确答案,hash:' + raw_hash[2])
            record(hash_question, raw_hash[2])
        elif color_d == '绿色':
            print('正在将答案D记录为正确答案,hash:' + raw_hash[3])
            record(hash_question, raw_hash[3])
    else:
        print('               已在数据库中找到该题目')
        data = query_answer(hash_question)
        # 对答案进行hash对比
        find_flag = False
        for hash_answer in data:
            if raw_hash[0] == hash_answer[2]:
                print('选择A答案')
                pyautogui.press('A')
                find_flag = True
            elif raw_hash[1] == hash_answer[2]:
                print('选择B答案')
                pyautogui.press('B')
                find_flag = True
            elif raw_hash[2] == hash_answer[2]:
                print('选择C答案')
                pyautogui.press('C')
                find_flag = True
            elif raw_hash[3] == hash_answer[2]:
                print('选择D答案')
                pyautogui.press('D')
                find_flag = True
        if not find_flag:
            print('答案hash与选项hash不符合,无法选择')
            if not os.path.exists('debug/' + hash_question + '-' + hash_answer[2] + '.png'):
                cur_frame.save('debug/' + hash_question + '-' + hash_answer[2] + '.png')

            if color_a == color_b == color_c == color_d == '白色':
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

            if color_a == '绿色':
                record(hash_question, raw_hash[0])
                print('追加答案为A')
            elif color_b == '绿色':
                record(hash_question, raw_hash[1])
                print('追加答案为B')
            elif color_c == '绿色':
                record(hash_question, raw_hash[2])
                print('追加答案为C')
            elif color_d == '绿色':
                record(hash_question, raw_hash[3])
                print('追加答案为D')
    # 更新帧，为下一动态检测而准备
    pre_frame = cur_frame


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

    # img_question = ImageGrab.grab(bbox=(550, 350, 1054, 454))
    # img_a = ImageGrab.grab(bbox=(622, 468, 982, 550))
    # img_b = ImageGrab.grab(bbox=(622, 564, 982, 646))
    # img_c = ImageGrab.grab(bbox=(622, 660, 982, 742))
    # img_d = ImageGrab.grab(bbox=(622, 756, 982, 838))
    #
    # hash_question = str(imagehash.dhash(img_question))
    # hash_a = str(imagehash.dhash(img_a.resize((120, 24)).convert('1')))
    # color_a = get_button_color(img_a)
    # hash_b = str(imagehash.dhash(img_b.resize((120, 24)).convert('1')))
    # color_b = get_button_color(img_b)
    # hash_c = str(imagehash.dhash(img_c.resize((120, 24)).convert('1')))
    # color_c = get_button_color(img_c)
    # hash_d = str(imagehash.dhash(img_d.resize((120, 24)).convert('1')))
    # color_d = get_button_color(img_d)
    #
    # if hash_c == hash_d:
    #     print('c 和 d 相同')
    # raw_hash[0] = hash_a
    # raw_hash[1] = hash_b
    # raw_hash[2] = hash_c
    # raw_hash[3] = hash_d
    # print('hash_question:' + hash_question)
    # print('raw_hash:', raw_hash)

    while not stop_flag:
        auto_process()
        time.sleep(0.1)
