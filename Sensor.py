from maix import camera, display, image, nn, app,pinmap,uart
import time



target_text = None  # 目标锁定文本
prev_text = None  # 前次识别结果
counter = 0     # 初始化阶段计数器
confirm_counter = 0 #用于记录连续匹配次数


model = "/root/models/pp_ocr.mud"
ocr = nn.PP_OCR(model)

cam = camera.Camera(ocr.input_width(), ocr.input_height(), ocr.input_format())
disp = display.Display()

pinmap.set_pin_function("A16", "UART0_TX")  # 根据硬件连接调整引脚
pinmap.set_pin_function("A17", "UART0_RX")
serial = uart.UART("/dev/ttyS0", 115200,uart.BITS.BITS_8, uart.PARITY.PARITY_NONE, uart.STOP.STOP_1)  # 使用默认串口设备


image.load_font("ppocr", "/maixapp/share/font/ppocr_keys_v1.ttf", size = 20)
image.set_default_font("ppocr")




def delay_ms(ms):
    time.sleep(ms / 1000)


def send_via_serial(is_confirmed):
    """通过串口发送数据"""
    try:
        if is_confirmed:
            serial.write(b"1")
        else:
            serial.write(b"0")
    except Exception as e:
        print("串口发送失败:", str(e))
    delay_ms(100)

def define_sensor(current_text):
    global target_text, prev_text, counter ,confirm_counter # 声明全局变量
    if current_text:  # 忽略空内容
        if target_text is None:
            # 初始阶段：累积十次相同结果
            if prev_text is not None:
                if current_text == prev_text:
                    counter += 1
                else:
                    counter = 0  # 结果不一致时重置计数器
            prev_text = current_text
            
            if counter >= 9:  # 连续十次相同（0-9共10次）
                target_text = current_text
                print(f"目标已锁定：{target_text}")
                confirm_counter = 0  # 初始化确认计数器
        else:
           # 运行阶段：判断是否匹配目标
            if current_text == target_text:
                confirm_counter += 1
            else:
                confirm_counter = 0  # 匹配失败时重置
            
            # 仅当连续三次匹配成功时才发送1
            if confirm_counter >= 3:
                send_via_serial(1)
                confirm_counter = 0
            else:
                send_via_serial(0)
while not app.need_exit():

    img = cam.read()
    objs = ocr.detect(img)

    current_text = "".join([obj.char_str() for obj in objs])

    for obj in objs:
        text = obj.char_str()
        points = obj.box.to_list()
        img.draw_keypoints(points, image.COLOR_RED, 4, -1, 1)
        img.draw_string(obj.box.x4, obj.box.y4, obj.char_str(), image.COLOR_RED)
    
    define_sensor(current_text)
    disp.show(img)

    