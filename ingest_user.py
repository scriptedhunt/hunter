
class User(object):
    def __init__(self, username, uid):
        self.username = username
        self.uid = uid
        self.groups = []

    def add_group(self, gname):
        self.groups.append(gname)

def get_user_info(passwordfile='/etc/passwd',groupfile='/etc/group'):
    user_dict = {}
    group_dict = {}
    with open(passwordfile, 'r') as fh:
        for line in fh.readlines():
            fields = line.split(':')
            user_dict[fields[0]] = User(fields[0], fields[2])
            group_dict[fields[0]] = fields[3]
    group_dict2 = {}
    with open(groupfile, 'r') as fh:
        for line in fh.readlines():
            fields = line.split(':')
            group_dict2[fields[0]] = fields[2]
            for k, v in group_dict.iteritems():
                if fields[2] == v:
                    user_dict[k].add_group(fields[0])
            if not fields[3].strip() == "":
                users = fields[3].strip().split(',')
                for user in users:
                    if user_dict.has_key(user):
                        user_dict[user].add_group(fields[0])

    return user_dict, group_dict2


if __name__ == "__main__":
    di, d2 = get_user_info()

    for k,v in di.iteritems():
        print "\n\n+++++++++++++++++++++++++"
        print k
        for n in v.groups:
            print n
        print "+++++++++++++++++++++++++"
    for k,v in d2.iteritems():
        print "key=%s value=%s" % (k,v)