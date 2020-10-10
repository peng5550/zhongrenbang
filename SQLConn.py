import time
import pymysql

class SQLConnection:


    def __init__(self):
        self.conn = pymysql.connect(host="127.0.0.1", port=3306, user="root", passwd="123456", db="zhongrenbang")
        self.db = self.conn.cursor()

    def insert_data(self, table_name, item_info):
        keys = ', '.join(list(item_info.keys()))
        values = ', '.join(['%s'] * len(item_info))
        insert_sql = "insert into `{}`({})values({});".format(table_name, keys, values)
        try:
            self.db.execute(insert_sql, tuple(item_info.values()))
            self.conn.commit()
        except Exception as e:
            print(e.args)
            self.conn.rollback()

    def select_data(self, table_name, item_info):
        string_list = []
        for i in item_info.keys():
            string = '%s="%s"' % (i, str(item_info.get(i)))
            string_list.append(string)
        sql_string = ' and '.join(string_list)

        select_sql = "select * from {} where {};".format(table_name, sql_string)

        self.db.execute(select_sql)
        res = self.db.fetchall()
        if res:
            return True
        else:
            return False

    def reConn(self, num=28800, stime=3):
        """
        校验数据库连接是否异常
        num：8小时
        stime：间隔3秒重连
        """
        _number = 0
        _status = True
        while _status and _number <= num:
            try:
                self.conn.ping()  # cping 校验连接是否异常
                _status = False
            except:
                if self.conn == True:  # 重新连接,成功退出
                    _status = False
                    break
                _number += 1
                time.sleep(stime)
            print("reConn", _number)

if __name__ == '__main__':
    conn = SQLConnection()
