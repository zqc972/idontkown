import pyautogui
import PIL.ImageGrab as ImageGrab
import PIL.Image as Image
import imagehash
import signal
import sqlite3
import random


# 修改此处进行定义操作窗口区域

pre_frame = None    # 上一帧
cur_frame = None    # 当前帧
raw_hash = ['', '', '', '']     # 用于记录未选择状态下ABCD的hash值
last_insert_sql = ''
stop_flag = False

db = sqlite3.connect('data.db')


# 初始化
def init():
    cursor = db.cursor()
    cursor.execute('create table if not exists data (question varchar(16) primary key,answer varchar(16))')


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
    data = cursor.fetchone()
    if data is not None:
        return data[1]
    else:
        return None


# 插入数据
def record(question_hash: str, answer_hash: str):
    global last_insert_sql
    sql = 'insert into data(question, answer) values (\'' + question_hash + '\',\'' + answer_hash + '\')'
    # 避免对同一正确答案多次存储
    if sql != last_insert_sql:
        db.execute(sql)
        db.commit()
        last_insert_sql = sql


# 获取图片主色调
def get_average_color(image: Image.Image):
    temp_img = image.resize((36, 8))
    r = g = b = 0
    for count, color in temp_img.getcolors(temp_img.width * temp_img.height):
        r = r + count * color[0]
        g = g + count * color[1]
        b = b + count * color[2]
    r = int(r / (temp_img.width * temp_img.height))
    g = int(g / (temp_img.width * temp_img.height))
    b = int(b / (temp_img.width * temp_img.height))
    return r, g, b


# 颜色分类
def classify_color(color: []):
    if color[0] > 192 and color[1] < 90 and color[2] < 90:
        print('检测到红色')
        return '红色'
    elif color[0] < 100 and color[1] > 192 and color[2] > 138:
        print('检测到绿色')
        return '绿色'
    elif color[0] < 64 and color[1] < 64 and color[2] > 192:
        print('检测到蓝色')
        return '蓝色'
    elif color[0] > 192 and color[1] > 192 and color[2] > 192:
        print('检测到白色')
        return '白色'
    elif color[0] < 64 and color[1] < 64 and color[2] < 64:
        print('检测到黑色')
        return '黑色'
    else:
        print('检测到中间色', color)
        return '中间色'


# 处理逻辑
def auto_process():
    # 可改进为截图一整个区域后，再将题目和各选项给切分出来
    img_question = ImageGrab.grab(bbox=(500, 350, 1050, 450))
    img_A = ImageGrab.grab(bbox=(622, 468, 982, 550))
    img_B = ImageGrab.grab(bbox=(622, 564, 982, 646))
    img_C = ImageGrab.grab(bbox=(622, 660, 982, 742))
    img_D = ImageGrab.grab(bbox=(622, 756, 982, 838))

    global pre_frame
    global cur_frame
    cur_frame = ImageGrab.grab(bbox=(525, 32, 1079, 1018))
    if pre_frame is not None:
        hash_cur_frame = imagehash.dhash(cur_frame)
        hash_pre_frame = imagehash.dhash(pre_frame)
        if hash_cur_frame != hash_pre_frame:
            print('监测区域中有移动..')
            pre_frame = cur_frame
            return

    hash_question = str(imagehash.average_hash(img_question))
    hash_A = str(imagehash.average_hash(img_A))
    color_A = classify_color(get_average_color(img_A))
    hash_B = str(imagehash.average_hash(img_B))
    color_B = classify_color(get_average_color(img_B))
    hash_C = str(imagehash.average_hash(img_C))
    color_C = classify_color(get_average_color(img_C))
    hash_D = str(imagehash.average_hash(img_D))
    color_D = classify_color(get_average_color(img_D))

    # 记录原始答案的图像hash值，以备在公布正确答案后存入数据库
    if color_A == color_B == color_C == color_D == '白色':
        raw_hash[0] = hash_A
        raw_hash[1] = hash_B
        raw_hash[2] = hash_C
        raw_hash[3] = hash_D

    # 若数据库中未收录该题目
    if not query_question(str(hash_question)):
        # 检测答案颜色，判断当前是已作答还是未作答状态
        if color_A == color_B == color_C == color_D == '白色':
            # 进行盲选
            select = random.randint(1, 4)
            print('准备盲选')
            if select == 1:
                pyautogui.press('A')
            elif select == 2:
                pyautogui.press('B')
            elif select == 3:
                pyautogui.press('C')
            elif select == 4:
                pyautogui.press('D')
        # 选择后对正确答案记录
        elif color_A == '绿色':
            print('正在将答案A记录为正确答案')
            record(hash_question, raw_hash[0])
        elif color_B == '绿色':
            print('正在将答案B记录为正确答案')
            record(hash_question, raw_hash[1])
        elif color_C == '绿色':
            print('正在将答案C记录为正确答案')
            record(hash_question, raw_hash[2])
        elif color_D == '绿色':
            print('正在将答案D记录为正确答案')
            record(hash_question, raw_hash[3])
    else:
        print('               已在数据库中找到该题目')
        hash_answer = query_answer(hash_question)
        # 对答案进行hash对比
        if hash_A == hash_answer:
            print('选择A答案')
            pyautogui.press('A')
        elif hash_B == hash_answer:
            print('选择B答案')
            pyautogui.press('B')
        elif hash_C == hash_answer:
            print('选择C答案')
            pyautogui.press('C')
        elif hash_D == hash_answer:
            print('选择D答案')
            pyautogui.press('D')
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
    while not stop_flag:
        auto_process()
        print('====================================')
