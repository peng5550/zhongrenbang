import flask, json
from flask import request, render_template
from SQLConn import SQLConnection

server = flask.Flask(__name__)
TABLE_NAME = "taskData"
SQL = SQLConnection()


def saveTaskInfo(taskList, secret):
    for task in taskList:
        taskId = task.get("EarnDeatile").get("id")
        if not SQL.select_data(table_name=TABLE_NAME, item_info={"id": taskId}):
            item = {
                "id": taskId,
                "title": task["EarnDeatile"]["name"].replace("&npsp;", ""),
                "keywords": task["EarnDeatile"]["groupname"],
                "money": task["EarnDeatile"]["money"],
                "introduce": f"{task['EarnDeatile']['detail']}{task['EarnDeatile']['condition']}",
                "stepJson": str(task["WjMissionDeatile"]),
                "uuid": secret
            }
            SQL.insert_data(table_name=TABLE_NAME, item_info=item)


def loadData(secret):
    dayData = f"select * from {TABLE_NAME} where uuid='{secret}';"
    SQL.conn.ping(reconnect=True)
    SQL.db.execute(dayData)
    res = SQL.db.fetchall()
    if res:
        return res
    else:
        return []


def searchData(id, secret):
    dayData = f"select * from {TABLE_NAME} where id={id} and uuid='{secret}';"
    SQL.conn.ping(reconnect=True)
    SQL.db.execute(dayData)
    res = SQL.db.fetchall()
    if res:
        return res
    else:
        return []


@server.route('/task/search/<secret>', methods=['GET', 'POST'])
def showIndex(secret):
    if request.method == "POST":
        return json.dumps({"status": False}, ensure_ascii=False)

    if request.method == "GET":
        dataList = loadData(secret)
        return render_template('index.html', data=dataList)


@server.route('/task/detail/<secret>/<taskId>', methods=['GET', 'POST'])
def showTask(secret, taskId):
    if request.method == "POST":
        return json.dumps({"status": False}, ensure_ascii=False)

    if request.method == "GET":

        taskData = searchData(taskId, secret)
        print("showTask", taskData)
        if taskData:
            info = taskData[0]
            stepInfo = eval(info[5])
            return render_template('showtask.html', data=info[:5], stepInfo=stepInfo)
        else:
            return


@server.route('/save', methods=['POST'])
def saveDatas():
    if request.method == "POST":
        data = request.get_json().get("data")
        secret = request.get_json().get("secret")
        saveTaskInfo(data, secret)
        return json.dumps({"code": 200, "message": "保存成功"}, ensure_ascii=False)


if __name__ == '__main__':
    server.run(host='127.0.0.1', port=8888)
