import base64
import hashlib
import hmac
import io
import json
import threading
from collections import defaultdict
import requests
import pickle
import os
from mttkinter import mtTkinter as mtk
from tkinter import ttk, scrolledtext, END, Tk, Frame, filedialog
from datetime import datetime
import urllib.parse
from PIL import Image, ImageTk
from tkinter.messagebox import *
import time
import uuid

USERNAME = "18663458009"
PASSWORD = "kl6860179"
TASK_FILE = "./tasks.txt"
SESSION_FILE = "./session.pkl"


class SendDingDingMessage:
    def __init__(self):
        with open("./DingDingRobat.json", "r+", encoding="utf-8")as file:
            self.ddinfo = json.loads(file.read())

    def sendMessage(self, sendText, imgUrl):
        '''
        使用钉钉机器人向钉钉发送消息
        :param secret:机器人的 secret
        :param webHook: 机器人的 webHook
        :param sendText: 发送的文字
        :param imgUrl: 查看全部的url，即img2url生成的图片
        :return:
        '''
        secret = self.ddinfo.get("secret")
        webHook = self.ddinfo.get("webHook")
        # 使用钉钉机器人发送定制消息
        timestamp = str(round(time.time() * 1000))
        secret_enc = secret.encode('utf-8')
        string_to_sign = '{}\n{}'.format(timestamp, secret)
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        webhook = "{}&timestamp={}&sign={}".format(webHook, timestamp, sign)
        headers = {"Content-Type": "application/json",
                   "Charset": "UTF-8"}

        # 消息类型和数据格式参照钉钉开发文档
        data = {
            "actionCard": {
                "title": "众人帮新任务提醒",
                "text": sendText,
                "btnOrientation": "0",
                "singleTitle": "查看详情" if imgUrl else "",
                "singleURL": imgUrl,
            },
            "msgtype": "actionCard"
        }

        r = requests.post(webhook, data=json.dumps(data), headers=headers)
        print(r.text)
        # time.sleep(2)

class Application(Frame):

    def __init__(self, master):
        super(Application, self).__init__()
        self.msgRobot = SendDingDingMessage()
        # self.login()
        self.root = master
        self.root.geometry("800x770")
        self.root.title("众人帮Helper 2.0")
        self.creatUI()
        self.uptime()
        self.sess = requests.Session()
        headers = {
            'Host': 'm.zrb.net',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36 QBCore/4.0.1301.400 QQBrowser/9.0.2524.400 Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2875.116 Safari/537.36 NetType/WIFI MicroMessenger/7.0.5 WindowsWechat',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Referer': 'http://m.zrb.net/next/index',
        }
        self.sess.headers = headers

    def creatUI(self):
        # 数据展示
        self.showData = mtk.LabelFrame(self.root, text="新任务", fg="blue")
        self.showData.place(x=20, y=20, width=760, height=510)

        title = ['1', '2', '3', '4', '5', '6']
        self.box = ttk.Treeview(self.showData, columns=title, show='headings')
        self.box.place(x=20, y=15, width=730, height=450)
        self.box.column('1', width=30, anchor='center')
        self.box.column('2', width=180, anchor='center')
        self.box.column('3', width=100, anchor='center')
        self.box.column('4', width=50, anchor='center')
        self.box.column('5', width=50, anchor='center')
        self.box.column('6', width=140, anchor='center')

        self.box.heading('1', text='序号')
        self.box.heading('2', text='任务名称')
        self.box.heading('3', text='悬赏主ID')
        self.box.heading('4', text='关键字')
        self.box.heading('5', text='赏金')
        self.box.heading('6', text='获取时间')

        self.VScroll1 = ttk.Scrollbar(self.box, orient='vertical', command=self.box.yview)
        self.VScroll1.pack(side="right", fill="y")
        self.box.configure(yscrollcommand=self.VScroll1.set)

        self.box.bind(sequence="<Double-Button-1>", func=lambda x: self.thread_it(self.showDetail))

        # 日志
        self.logs = mtk.LabelFrame(self.root, text="log日志", fg="blue")
        self.logs.place(x=20, y=550, width=300, height=200)
        self.logtext = scrolledtext.ScrolledText(self.logs, fg="green")
        self.logtext.place(x=20, y=15, width=270, height=140)

        self.settings = mtk.LabelFrame(self.root, text="设置", fg="blue")
        self.settings.place(x=340, y=550, width=440, height=200)

        self.timeSleep = mtk.Label(self.settings, text="任务延时(分钟)：")
        self.timeSleep.place(x=20, y=30, width=100, height=25)
        self.timeSleepText = mtk.Entry(self.settings)
        self.timeSleepText.place(x=120, y=30, width=80, height=25)

        self.timeNow = mtk.Label(self.settings, text="当前时间：")
        self.timeNow.place(x=20, y=100, width=70, height=25)
        self.timeNowText = mtk.Label(self.settings, text=str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        self.timeNowText.place(x=100, y=100, width=150, height=25)

        self.startBtn = mtk.Button(self.settings, text="启动", command=lambda: self.thread_it(self.start))
        self.startBtn.place(x=280, y=30, width=100, height=30)

        self.stopBtn = mtk.Button(self.settings, text="退出", command=lambda: self.thread_it(self.stop))
        self.stopBtn.place(x=280, y=100, width=100, height=30)

    def createNewUI(self, taskName, taskInfo):
        detailWin = mtk.Toplevel(self.root)
        detailWin.title(taskName)
        detailWin.geometry("650x550")
        tasksInfoBox = mtk.LabelFrame(detailWin, text="任务说明：", fg="blue")
        tasksInfoBox.place(x=20, y=20, width=610, height=510)
        tasksIntro = scrolledtext.ScrolledText(tasksInfoBox, fg="green")
        tasksIntro.place(x=20, y=10, width=580, height=60)
        tasksIntro.insert(END,
            f"{''.join([taskInfo.get('EarnDeatile').get('detail')[j] for j in range(len(taskInfo.get('EarnDeatile').get('detail'))) if ord(taskInfo.get('EarnDeatile').get('detail')[j]) in range(65536)])}\n{taskInfo.get('EarnDeatile').get('condition')}".replace(
                "&nbsp;", ""))

        taskStep = mtk.LabelFrame(tasksInfoBox, text="任务步骤", fg="blue")
        taskStep.place(x=20, y=80, width=200, height=380)
        stepText = scrolledtext.ScrolledText(taskStep, fg="green")
        stepText.place(x=10, y=10, width=180, height=330)
        if isinstance(taskInfo.get("WjMissionDeatile"), list):
            totalTextList = []
            for index, item in enumerate(taskInfo.get("WjMissionDeatile")):
                detail = item.get("detail", "")
                othLink = item.get("btnname", "")
                detailText = detail + othLink
                text = f"\n\nstep {index + 1}: " + ''.join(
                    [detailText[j] for j in range(len(detailText)) if ord(detailText[j]) in range(65536)]).strip()
                totalTextList.append(text)
            stepText.insert(END, "\n\n".join(totalTextList))
        else:
            stepText.insert(END, f"\n\nstep 1: {taskInfo.get('WjMissionDeatile').get('msg')}")

        self.imageShow = mtk.LabelFrame(tasksInfoBox, text="图例", fg="blue")
        self.imageShow.place(x=240, y=80, width=350, height=380)
        taskId = taskInfo.get('EarnDeatile').get('id')
        imageList = self.imageInfo.get(taskId)
        IMG = []
        if imageList:
            for image in imageList:
                if image[0]:
                    self.pil_image = Image.open(image[0])
                    self.pil_image = self.pil_image.resize((320, 350), Image.ANTIALIAS)
                    IMG.append(self.pil_image)
        self.image = mtk.Label(self.imageShow)
        if IMG:
            self.counter = 0
            self.imgNow = ImageTk.PhotoImage(IMG[self.counter])
            self.image.configure(image=self.imgNow)
            self.image.place(x=2, y=2, width=322, height=352)
            self.image.bind(sequence="<MouseWheel>", func=lambda x: self.thread_it(self.changeImage, IMG))
            self.image.bind(sequence="<Button-3>", func=lambda x: self.thread_it(self.saveImage, IMG))

        else:
            self.image.configure(text="暂无图片", fg="red")

    def deleteTree(self):
        x = self.box.get_children()
        for item in x:
            self.box.delete(item)

    def postTasks(self, tasksInfo, secret):
        post_data = {"data": tasksInfo, "secret": secret}
        response = requests.post("http://49.233.214.151:8888/save", json=post_data)
        print(response.text)

    def showDetail(self):
        for item in self.box.selection():
            itemText = self.box.item(item, "values")
            itemIndex = int(itemText[0]) - 1
            taskName = itemText[1]
            self.createNewUI(taskName, self.tasksInfo[itemIndex])

    def changeImage(self, IMG):
        if self.counter < (len(IMG) - 1):
            self.counter += 1
        else:
            self.counter = 0

        self.imgNow = IMG[self.counter]
        self.tk_image = ImageTk.PhotoImage(self.imgNow)
        self.image.configure(image=self.tk_image)

    def saveImage(self, IMG):
        imgNow = IMG[self.counter]
        imgPath = filedialog.asksaveasfilename(title=u'保存图片', filetypes=[("jpg", ".jpg")]) + ".jpg"
        imgNow.save(imgPath)

    def downloadImage(self, semaphore, tasksInfo):
        semaphore.acquire()
        taskId = tasksInfo.get("EarnDeatile").get("id")
        if isinstance(tasksInfo.get("WjMissionDeatile"), list):
            for index, stepInfo in enumerate(tasksInfo.get("WjMissionDeatile")):
                imageUrl = stepInfo.get('imgurl')
                if imageUrl:
                    image_bytes = requests.get(imageUrl).content
                    data_stream = io.BytesIO(image_bytes)
                    self.imageInfo[taskId].append([data_stream, index])
                else:
                    imageUrl = stepInfo.get('detailImg')
                    if imageUrl:
                        image_bytes = requests.get(imageUrl).content
                        data_stream = io.BytesIO(image_bytes)
                        self.imageInfo[taskId].append([data_stream, index])
        semaphore.release()

    def uptime(self):
        self.timeNowText["text"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.root.after(100, self.uptime)

    def downloadCaptchaImage(self):
        url = "http://m.zrb.net/checkcode.ashx"
        content = self.sess.get(url).content
        with open("./captcha.jpg", "wb")as img:
            img.write(content)

    def verifyCaptcha(self):
        self.downloadCaptchaImage()
        code = input("请输入验证码：")
        return code

    def saveSession(self, sess):
        with open(SESSION_FILE, "wb")as file:
            pickle.dump(sess, file)

    def loadTasks(self):
        if not os.path.exists(TASK_FILE):
            self.taskTotals = []
        else:
            with open(TASK_FILE, "r+", encoding="utf-8")as file:
                self.taskTotals = [task.strip() for task in file.readlines()]

    def saveTasks(self, taskIdList):
        lock = threading.Lock()
        lock.acquire()
        with open(TASK_FILE, "a+", encoding="utf-8")as file:
            for task in taskIdList:
                if str(task) not in self.taskTotals:
                    file.write(str(task) + "\n")
                    self.taskNew.append(task)
        lock.release()
        return self.taskNew

    def loginCheck(self):
        if not os.path.exists(SESSION_FILE):
            return False

        with open(SESSION_FILE, "rb")as file:
            sess = pickle.load(file)

        response = sess.get("http://m.zrb.net/next/user_admin").text

        if "修改密码" in response:
            return sess

        return False

    def login(self):
        res = self.loginCheck()
        if res:
            self.sess = res
            return True

        self.sess = requests.Session()
        headers = {
            'Host': 'm.zrb.net',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36 QBCore/4.0.1301.400 QQBrowser/9.0.2524.400 Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2875.116 Safari/537.36 NetType/WIFI MicroMessenger/7.0.5 WindowsWechat',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Referer': 'http://m.zrb.net/next/index',
        }
        self.sess.headers = headers

        loginUrl = "http://m.zrb.net/m/login"
        self.sess.get(loginUrl)
        code = self.verifyCaptcha()

        loginData = {
            "version": "0",
            "useraccount": USERNAME,
            "txtpassword": PASSWORD,
            "user_checkimg": code
        }

        response = self.sess.post(loginUrl, data=loginData)
        if "修改密码" in response.text:
            self.saveSession(self.sess)

        else:
            pass

    def indexPage(self, semaphore, page):
        semaphore.acquire()
        indexPageUrl = "http://m.zrb.net/api/EarnUser/EarnList"
        post_data = {
            "version": "136",
            "pindex": page,
            "type": "7",
            "subtype": "2",
            "keywords": " ",
            "isios": 0
        }
        response = self.sess.post(indexPageUrl, json=post_data)
        responseJson = response.json()
        self.tasks += [item["earnid"] for item in responseJson]
        semaphore.release()

    def detailPage(self, semaphore, earnid):
        semaphore.acquire()
        detailUrl = "http://m.zrb.net/api/EarnUser/EarnDetail"
        post_data = {
            "version": "136",
            "unaccount": "",
            "earnid": earnid,
            "submitDetail": ""
        }
        response = self.sess.post(detailUrl, json=post_data).json()
        self.tasksInfo.append(response)
        semaphore.release()

    def detailData(self, tasksInfoList):
        treeIndex = 1
        self.deleteTree()
        self.taskNameList = []
        for data in tasksInfoList:
            treeData = [
                treeIndex,
                "".join(
                    [data.get("EarnDeatile").get("name")[j] for j in range(len(data.get("EarnDeatile").get("name"))) if
                     ord(data.get("EarnDeatile").get("name")[j]) in range(65536)]),
                data.get("EarnDeatile").get("uid"),
                data.get("EarnDeatile").get("groupname", ""),
                data.get("EarnDeatile").get("money"),
                self.nowTime,
            ]
            if treeData[1] not in self.taskNameList:
                self.taskNameList.append(treeData[1])
                self.box.insert("", "end", values=treeData)
                self.box.yview_moveto(1.0)
                treeIndex += 1

    def taskManager1(self, func):
        semaphore = threading.Semaphore(2)
        ts = [threading.Thread(target=func, args=(semaphore, page,)) for page in range(1, 11)]
        [t.start() for t in ts]
        [t.join() for t in ts]

    def taskManager2(self, func, dataList):
        semaphore = threading.Semaphore(2)
        ts = [threading.Thread(target=func, args=(semaphore, data,)) for data in dataList]
        [t.start() for t in ts]
        [t.join() for t in ts]

    def start(self):

        try:
            self.sleepText = int(self.timeSleepText.get()) * 60
        except:
            showerror("错误信息", "请输入正确的任务等待时间!")
            return

        while True:
            self.taskNew = []
            self.tasks = []
            self.tasksInfo = []
            self.imageInfo = defaultdict(list)
            self.nowTime = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            self.logtext.insert(END,
                                f"{datetime.now().strftime('%Y:%m:%d %H:%M:%S')}\t\t\t开始任务.\n")
            self.logtext.yview_moveto(1.0)
            self.loadTasks()
            self.taskManager1(self.indexPage)
            self.saveTasks(self.tasks)
            if len(self.taskNew) > 0:
                self.taskManager2(self.detailPage, self.taskNew)
                self.detailData(self.tasksInfo)
                self.taskManager2(self.downloadImage, self.tasksInfo)
            secret = str(uuid.uuid1()).replace('-', '')
            self.postTasks(self.tasksInfo, secret)
            self.logtext.insert(END,
                                f"{datetime.now().strftime('%Y:%m:%d %H:%M:%S')}\t\t\t获取任务成功,共获取到{len(self.taskNameList)}条新任务.\n")
            self.logtext.yview_moveto(1.0)
            msgText = f"【众人帮新任务提示】\n- 截止当前时间：{self.nowTime}\n- 新增加{len(self.taskNameList)}条任务."
            url = "http://49.233.214.151:8888/task/search/{}".format(secret)
            self.msgRobot.sendMessage(msgText, url)
            time.sleep(self.sleepText)

    @staticmethod
    def thread_it(func, *args):
        t = threading.Thread(target=func, args=args)
        t.setDaemon(True)
        t.start()

    def stop(self):
        os._exit(0)

    def run(self):
        self.root.mainloop()





if __name__ == '__main__':
    root = Tk()
    Application(root)
    root.mainloop()
