from db_conn import db_handle
from ingest_user import get_user_info

def stage():
    handle = db_handle('sneakypassword')
    conn = handle.connect()
    handle.get_tables(conn)
    if not 'user_maps' in handle.tablenames and not 'groups_maps' in handle.tablenames:
        handle.build_db()
    return conn, handle


def insert(conn, handle):
    user_dict, group_dict = get_user_info()
    for user in user_dict.values():
        handle.exec_query(conn, "INSERT INTO user_maps (uid, username, groups) VALUES (%s, %s, %s)", (user.uid, user.username, ",".join(user.groups)))
    for gname, gid in group_dict.iteritems():
        handle.exec_query(conn, "INSERT INTO group_maps (gid, gname) VALUES (%s, %s)", (gid, gname))
