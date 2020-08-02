## author: 教室工作室馆长
## 成语接龙代码部分参考： 微信公众号：Charles的皮卡丘
## 使用科大讯飞 语音听写和语音合成——人工智能API
import websocket
import datetime
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
import time
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import _thread as thread
import pyttsx3
import os
import pyaudio
import wave
import io
import sys
import random

input_filename = "input.wav"               # 麦克风采集的语音输入
input_filepath = ""              # 输入文件的path
in_path = input_filepath + input_filename

STATUS_FIRST_FRAME = 0  # 第一帧的标识
STATUS_CONTINUE_FRAME = 1  # 中间帧标识
STATUS_LAST_FRAME = 2  # 最后一帧的标识

#通过麦克风采集音频
def get_audio(filepath):
   
    CHUNK = 256
    FORMAT = pyaudio.paInt16
    CHANNELS = 1                # 声道数
    RATE = 16000                # 采样率
    RECORD_SECONDS = 5
    WAVE_OUTPUT_FILENAME = filepath
    p = pyaudio.PyAudio()
    print("开始成语接龙，请说四字成语：")
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("*"*5, "开始录音：请在5秒内输入语音")
    frames = []
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        i=i
        data = stream.read(CHUNK)
        frames.append(data)
    print("*"*5, "录音结束\n")
    stream.stop_stream()
    stream.close()
    p.terminate()
    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
        
#调用讯飞语音听写API的类
class Ws_Param(object):
    # 初始化
    def __init__(self, APPID, APIKey, APISecret, AudioFile):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.AudioFile = AudioFile

        # 公共参数(common)
        self.CommonArgs = {"app_id": self.APPID}
        # 业务参数(business)，更多个性化参数可在官网查看
        self.BusinessArgs = {"domain": "iat", "language": "zh_cn","ptt":0, "accent": "mandarin", "vinfo":1,"vad_eos":10000}

    # 生成url
    def create_url(self):
        url = 'wss://ws-api.xfyun.cn/v2/iat'
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/iat " + "HTTP/1.1"
        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
            self.APIKey, "hmac-sha256", "host date request-line", signature_sha)
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        # 将请求的鉴权参数组合为字典
        v = {
            "authorization": authorization,
            "date": date,
            "host": "ws-api.xfyun.cn"
        }
        # 拼接鉴权参数，生成url
        url = url + '?' + urlencode(v)
        # print("date: ",date)
        # print("v: ",v)
        # 此处打印出建立连接时候的url,参考本demo的时候可取消上方打印的注释，比对相同参数时生成的url与自己代码生成的url是否一致
        # print('websocket url :', url)
        return url


# 收到websocket消息的处理
def on_message(ws, message):
    try:
        code = json.loads(message)["code"]
        sid = json.loads(message)["sid"]
        if code != 0:
            errMsg = json.loads(message)["message"]
            print("sid:%s 响应报错:%s 代码为:%s" % (sid, errMsg, code))

        else:
            data = json.loads(message)["data"]["result"]["ws"]
            global result
            #result=""
            for item in data:
                    result += item["cw"][0]["w"]

    except Exception as e:
        print("receive msg,but parse exception:", e)

    return result

# 收到websocket错误的处理
def on_error(ws, error):
    print("### 有错误啊:", error)


# 收到websocket关闭的处理
def on_close(ws):
    print("### 欢迎使用讯飞AI ###")


# 收到websocket连接建立的处理
def on_open(ws):
    def run(*args):
        frameSize = 8000  # 每一帧的音频大小
        intervel = 0.04  # 发送音频间隔(单位:s)
        status = STATUS_FIRST_FRAME  # 音频的状态信息，标识音频是第一帧，还是中间帧、最后一帧

        with open(wsParam.AudioFile, "rb") as fp:
            while True:
                buf = fp.read(frameSize)
                # 文件结束
                if not buf:
                    status = STATUS_LAST_FRAME
                # 第一帧处理
                # 发送第一帧音频，带business 参数
                # appid 必须带上，只需第一帧发送
                if status == STATUS_FIRST_FRAME:

                    d = {"common": wsParam.CommonArgs,
                         "business": wsParam.BusinessArgs,
                         "data": {"status": 0, "format": "audio/L16;rate=16000",
                                  "audio": str(base64.b64encode(buf), 'utf-8'),
                                  "encoding": "raw"}}
                    d = json.dumps(d)
                    ws.send(d)
                    status = STATUS_CONTINUE_FRAME
                # 中间帧处理
                elif status == STATUS_CONTINUE_FRAME:
                    d = {"data": {"status": 1, "format": "audio/L16;rate=16000",
                                  "audio": str(base64.b64encode(buf), 'utf-8'),
                                  "encoding": "raw"}}
                    ws.send(json.dumps(d))
                # 最后一帧处理
                elif status == STATUS_LAST_FRAME:
                    d = {"data": {"status": 2, "format": "audio/L16;rate=16000",
                                  "audio": str(base64.b64encode(buf), 'utf-8'),
                                  "encoding": "raw"}}
                    ws.send(json.dumps(d))
                    time.sleep(1)
                    break
                # 模拟音频采样间隔
                time.sleep(intervel)
        ws.close()

    thread.start_new_thread(run, ())
#读取成语库数据data.txt文件
def readData(filepath):
        fp = open(filepath, 'r', encoding='utf-8')
        idiom_data = {}
        valid_idioms = {}
        for line in fp.readlines():
            line = line.strip()
            if not line: continue
            item = line.split('\t')
            if len(item) != 3: continue
            if item[0][0] not in idiom_data:
                idiom_data[item[0][0]] = [item]
            else:
                idiom_data[item[0][0]].append(item)
            valid_idioms[item[0]] = item[1:]
        return idiom_data, valid_idioms
#播放wav音频文件
def playwav():
    chunk = 1024
    wf = wave.open('output.wav', 'rb')
    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
    channels=wf.getnchannels(),
    rate=wf.getframerate(),
    output=True)
    data = wf.readframes(chunk)
    while len(data) > 0:
        stream.write(data)
        data = wf.readframes(chunk)
    stream.stop_stream()
    stream.close()
    p.terminate()

#将pcm加入头文件组成完整的wav音频文件
def pcm2wav(pcm_file, save_file, channels=1, bits=16, sample_rate=16000):
        pcmf=open(pcm_file, 'rb')
        pcmdata = pcmf.read()
        pcmf.close()
        if bits % 8 != 0:
             raise ValueError("bits % 8 must == 0. now bits:" + str(bits))
        wavfile=wave.open(save_file, 'wb')
        wavfile.setnchannels(channels)
        wavfile.setsampwidth(bits//8)
        wavfile.setframerate(sample_rate)
        wavfile.writeframes(pcmdata)
        wavfile.close()
#调用讯飞语音合成API的类
class Ws_Param2(object):
    # 初始化
    def __init__(self, APPID, APIKey, APISecret, Text):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.Text = Text

        # 公共参数(common)
        self.CommonArgs = {"app_id": self.APPID}
        # 业务参数(business)，更多个性化参数可在官网查看
        self.BusinessArgs = {"aue": "raw", "auf": "audio/L16;rate=16000", "vcn": "x2_nannan", "tte": "utf8"}
        self.Data = {"status": 2, "text": str(base64.b64encode(self.Text.encode('utf-8')), "UTF8")}
        #使用小语种须使用以下方式，此处的unicode指的是 utf16小端的编码方式，即"UTF-16LE"”
        #self.Data = {"status": 2, "text": str(base64.b64encode(self.Text.encode('utf-16')), "UTF8")}

    
    # 生成url
    def create_url(self):
        url = 'wss://tts-api.xfyun.cn/v2/tts'
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/tts " + "HTTP/1.1"
        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
            self.APIKey, "hmac-sha256", "host date request-line", signature_sha)
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        # 将请求的鉴权参数组合为字典
        v = {
            "authorization": authorization,
            "date": date,
            "host": "ws-api.xfyun.cn"
        }
        # 拼接鉴权参数，生成url
        url = url + '?' + urlencode(v)
        # print("date: ",date)
        # print("v: ",v)
        # 此处打印出建立连接时候的url,参考本demo的时候可取消上方打印的注释，比对相同参数时生成的url与自己代码生成的url是否一致
        # print('websocket url :', url)
        return url

def on_message2(ws2, message):
    try:
        message =json.loads(message)
        code = message["code"]
        sid = message["sid"]
        audio = message["data"]["audio"]
        audio = base64.b64decode(audio)
        status = message["data"]["status"]
        #print(message)
        if status == 2:
            print("结束讯飞AI调用")
            ws2.close()
        if code != 0:
            errMsg = message["message"]
            print("sid:%s call error:%s code is:%s" % (sid, errMsg, code))
        else:

            with open('output.pcm', 'ab') as f:
                f.write(audio)
            pcm2wav("output.pcm","output.wav")
    except Exception as e:
        print("receive msg,but parse exception:", e)



# 收到websocket错误的处理
def on_error2(ws2, error):
    print("### error:", error)


# 收到websocket关闭的处理
def on_close2(ws2):
    print("### closed ###")



# 收到websocket连接建立的处理
def on_open2(ws2):
    def run(*args):
        d = {"common": wsParam2.CommonArgs,
             "business": wsParam2.BusinessArgs,
             "data": wsParam2.Data,
             }
        d = json.dumps(d)
        #print("------>开始发送文本数据")
        ws2.send(d)
        if os.path.exists('output.pcm'):
            os.remove('output.pcm')
        

    thread.start_new_thread(run, ())



if __name__ == "__main__":   
        #engine = pyttsx3.init()
    while 1:
        idiom_data,valid_idioms = readData('data.txt')
        ai_answer = None
        get_audio(in_path)
        wsParam = Ws_Param(APPID='5f09e790', APIKey='69000af7b9794e39688630d4a62002e5',
                       APISecret='e88504cabbb8646417da0ee975ed84e3',
                       AudioFile=r'input.wav')
        websocket.enableTrace(False)
        wsUrl = wsParam.create_url()
        result=""
        ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close)
        ws.on_open = on_open
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        print("识别到：",result)
        idiom=result
        idiom = idiom.strip()
        try:
            answers = idiom_data[idiom[-1]]
            answer = random.choice(answers)
            ai_answer = answer.copy()
            wsParam2 = Ws_Param2(APPID='5f09e790', APIKey='69000af7b9794e39688630d4a62002e5',
                           APISecret='e88504cabbb8646417da0ee975ed84e3',
                           Text="我接："+ai_answer[0])
            print("我接：",ai_answer[0])
        except Exception as e:
            wsParam2 = Ws_Param2(APPID='5f09e790', APIKey='69000af7b9794e39688630d4a62002e5',
                           APISecret='e88504cabbb8646417da0ee975ed84e3',
                           #Text="你说的是神马成语！不会接")
                           Text="请在B站关注我，回复“成语接龙”即可获得源代码，麻烦观众老爷长按右下的点赞按钮持续2秒,编程UP做视频不光要剪辑，还需要写代码很辛苦呢。大家对我的支持就是我做视频的动力，么么哒")
            #print("你说的是神马成语！不会接！")
        websocket.enableTrace(False)
        wsUrl2 = wsParam2.create_url()
        ws2 = websocket.WebSocketApp(wsUrl2, on_message=on_message2, on_error=on_error2, on_close=on_close2)
        ws2.on_open = on_open2
        ws2.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        playwav()
        #print("我的回答是：",ai_answer[0])
        #engine.say(ai_answer[0])
        #engine.runAndWait()

            
