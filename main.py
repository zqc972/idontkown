import pyautogui
import PIL.ImageGrab as ImageGrab   # 与pyscreenshot效果一致
import PIL.Image as Image
import imagehash
import signal
import sqlite3
import random


# 修改此处进行定义操作窗口区域
window_x1 = 0
window_y1 = 0
window_x2 = 400
window_y2 = 400

pre_frame = None    # 上一帧
cur_frame = None    # 当前帧
stop_flag = False

db = sqlite3.connect('data.db')


# 初始化
def init():
    cursor = db.cursor()
    cursor.execute('create table if not exists data (question varchar(16) primary key,answer varchar(16))')


# 查询问题hash
def query_question(q_hash: str):
    cursor = db.cursor()
    cursor.execute('select * from data where question =\'' + q_hash + '\'')
    data = cursor.fetchall()
    if len(data) > 0:
        return True
    else:
        return False


def query_answer(q_hash: str):
    cursor = db.cursor()
    cursor.execute('select * from data where question = \'' + q_hash + '\'')
    data = cursor.fetchone()
    return data


# 插入数据
def record(question_hash: str, answer_hash: str):
    db.execute('insert into data(question, answer) values (' + question_hash + ',' + answer_hash + ')')


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


def classify_color(color: []):
    if color[0] > 192 and color[1] < 64 and color[2] < 64:
        print('检测到红色')
        return '红色'
    elif color[0] < 75 and color[1] > 192 and color[2] > 138:
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
    print('正在检测')
    # 应改进为截图一整个区域后，再将题目和各选项给切分出来
    img_question = ImageGrab.grab(bbox=(500, 350, 1050, 450))
    img_A = ImageGrab.grab(bbox=(622, 468, 982, 550))
    img_B = ImageGrab.grab(bbox=(622, 564, 982, 646))
    img_C = ImageGrab.grab(bbox=(622, 660, 982, 742))
    img_D = ImageGrab.grab(bbox=(622, 756, 982, 838))

    global pre_frame
    global cur_frame
    cur_frame = ImageGrab.grab(bbox=(525, 32, 1079, 1018))
    if pre_frame is not None:
        hash_cur_frame = imagehash.average_hash(cur_frame)
        hash_pre_frame = imagehash.average_hash(pre_frame)
        if hash_cur_frame != hash_pre_frame:
            print('监测区域中有移动..')
            pre_frame = cur_frame
            return

    hash_question = imagehash.average_hash(img_question)
    hash_A = imagehash.average_hash(img_A)
    color_A = classify_color(get_average_color(img_A))
    hash_B = imagehash.average_hash(img_B)
    color_B = classify_color(get_average_color(img_B))
    hash_C = imagehash.average_hash(img_C)
    color_C = classify_color(get_average_color(img_C))
    hash_D = imagehash.average_hash(img_D)
    color_D = classify_color(get_average_color(img_D))

    if not query_question(str(hash_question)):
        # 检测颜色
        if color_A == color_B == color_C == color_D == '白色':
            # 进行盲选
            select = random.randint(1, 4)
            if select == 1:
                pass
            elif select == 2:
                pass
            elif select == 3:
                pass
            elif select == 4:
                pass
        # 选择后对正确答案记录
        # 但要注意记录时不要重复添加数据，以及数据应为白色答案的hash值
        elif color_A == '绿色':
            record(hash_question, hash_A)
        elif color_B == '绿色':
            record(hash_question, hash_B)
        elif color_C == '绿色':
            record(hash_question, hash_C)
        elif color_D == '绿色':
            record(hash_question, hash_D)
    else:
        hash_answer = query_answer(hash_question)
        # 对答案进行hash对比
        if hash_A == hash_answer:
            record(hash_question, hash_A)
        elif hash_B == hash_answer:
            record(hash_question, hash_B)
        elif hash_C == hash_answer:
            record(hash_question, hash_C)
        elif hash_D == hash_answer:
            record(hash_question, hash_D)
    # 更新帧，为下一动态检测而准备
    pre_frame = cur_frame


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
