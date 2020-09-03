import pymysql


con = pymysql.connect(host='<хост БД>',
                      user='<имя пользователя>',
                      password='<пароль от БД>',
                      db='<имя БД>',
                      charset='utf8mb4')
cur = con.cursor()


def update_max_symbols(group_id: str, max_symbols: int) -> None:
    cur.execute("UPDATE `groups` SET `max_symbols` = (%s) WHERE `group_id` = (%s)",
                (max_symbols, group_id,)
                )
    con.commit()


def read_max_symbols(group_id: str) -> int:
    cur.execute("SELECT `max_symbols` FROM `groups` WHERE `group_id` = (%s)",
                (group_id,)
                )
    return cur.fetchone()[0]


def update_del_sys_messages(group_id: str, del_sys_messages: int) -> None:
    cur.execute("UPDATE `groups` SET `del_sys_messages` = (%s) WHERE `group_id` = (%s)",
                (del_sys_messages, group_id,)
                )
    con.commit()
    

def read_del_sys_messages(group_id: str) -> int:
    cur.execute("SELECT `del_sys_messages` FROM `groups` WHERE `group_id` = (%s)",
                (group_id,)
                )
    return cur.fetchone()[0]