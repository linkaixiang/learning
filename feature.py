 # -*- coding: utf-8 -*-
import collections
import json


'属性文件中各种属性在第几列'
INDEX_REQ_IID = 0
INDEX_RESP_IID = 1
INDEX_GID = 2
INDEX_REQ_NAME = 3
INDEX_REQ_CAT = 4
INDEX_RESP_NAME = 5
INDEX_RESP_CAT = 6

'''林凯翔计算特征辅助函数 '''
def get_dict_from_file(filename):
    '''公用函数，用于从文件中读取字典,所有文件的格式都是： key+\t+value+\n'''
    dict_from_file = {}
    with open(filename) as f:
        line = f.readline()
        dict_from_file = json.loads(line)
    return dict_from_file

'''********compute_feature_itemsex的辅助函数 begin **********'''
def is_overlap(key_set, name):
    '判断关键词是否在名称中'
    man_flag = 0
    for item in key_set:
        if item in name:
            man_flag += 1
    return man_flag

def judege_sex(item_name, cat_name):
    '根据商品名称，类别名称判断男女'
    woman_flags_cat = {"女", "妇","美颜","美容","验孕","减肥","瘦身","乳腺癌"}
    man_flags_cat = {"男","剃须","补肾","壮阳","延时","脱发","雄"}
    man_flag = 0
    wman_flag = 0
    flag = 0
    all = 0
    man_flag += is_overlap(man_flags_cat,item_name)
    man_flag += is_overlap(man_flags_cat,cat_name)
    wman_flag += is_overlap(woman_flags_cat,item_name)
    wman_flag += is_overlap(woman_flags_cat,cat_name)
    if wman_flag == 0 and man_flag != 0:
        flag = 1
    if wman_flag !=0 and man_flag == 0:
        flag = -1
    return flag

def is_same_sex(item_name1, cat_name1,item_name2, cat_name2):
    '判断两个商品是否是相同的特征'
    flag = 0
    request_sex = judege_sex(item_name1,cat_name1)
    response_sex = judege_sex(item_name2,cat_name2)
    if response_sex == request_sex and request_sex != 0:
        flag = 1
    return flag

'''********compute_feature_relatedset的辅助函数 begin ********'''
def is_in_set(category_name1, category_name2):
    'return 1 if cagegory names both in the set, 0, if at least one not in, -1 if not legal input'
    related_set = {"成人用品", "性功能障碍", "阳痿早泄", "肾阳虚", "肾阴虚", "综合滋补"}
    flag1 = 0
    flag2 = 0
    if category_name2 == "None" or category_name1 == "None":
        return -1
    category_namelist1 = category_name1.split(" ")
    category_namelist2 = category_name2.split(" ")
    for items in category_namelist1:
        if items in related_set:
            flag1 = 1
            break
    for items in category_namelist2:
        if items in related_set:
            flag2 = 1
            break

    return flag1 * flag2

'''********compute_feature_useritemsex的辅助函数 begin ********'''
def is_related_sex(categoryname, itemname, user_sex):
    flag = 0
    sex = ""
    sex_flag = judege_sex(itemname,categoryname)
    if sex_flag == 1:
        sex = "男"
    elif sex_flag == -1:
        sex = "女"

    if user_sex == sex:
        flag = 1
    return flag

'''********compute_feature_ctr的辅助函数 begin**************'''
def get_ctr_dict(resp_dict, feedback_dict):
    '''计算每个item的feedback次数除以推荐次数，加入平滑，对转化率开立方使得分布均匀,特征离散化
       输入：response，feedback的字典
       输出：ctr的字典 key是iid, value是ctr的数值'''
    ctr_dict = {}
    for item in resp_dict:
        if item in feedback_dict:
            rate = (float(feedback_dict[item] + 1) / (1000 + resp_dict[item])) ** (1.0/3)
            ctr_dict[item] = rate
        else:
            ctr_dict[item] = 0
    return ctr_dict

class Feature:
    def __init__(self,attrfile, **kwargs):
        self.attrfile = attrfile
        # 林凯翔特征的输入
        self.feedback_dict = get_dict_from_file(kwargs["feedback_dict"])
        self.addcart_dict = get_dict_from_file(kwargs["addcart_dict"])
        self.visit_dict = get_dict_from_file(kwargs["visit_dict"])
        self.response_dict = get_dict_from_file(kwargs["response_dict"])
        self.ctr_dict = get_ctr_dict(self.response_dict,self.feedback_dict)
        self.user_sex_dict = get_dict_from_file(kwargs["user_sex_dict"])

    def compute_feature_feedback(self, response_iid):
        '''获取点击次数特征 (lkx)
           输入：feedback 字典， response iid.
           输出：response iid 对应的feedback次数'''
        feature = 0
        feedback_dict = self.feedback_dict
        if response_iid in feedback_dict:
            feature = feedback_dict[response_iid]
        return feature

    def compute_feature_addcart(self, response_iid):
        '''获取添加次数特征 (lkx)
           输入：addcart 字典， response iid.
           输出：response iid 对应的addcart次数'''
        feature = 0
        if response_iid in self.addcart_dict:
            feature = self.addcart_dict[response_iid]
        return feature

    def compute_feature_visit(self,response_iid):
        '''获取浏览次数特征 (lkx)
           输入：addcart 字典， response iid.
           输出：response iid 对应的addcart次数'''
        feature = 0
        if response_iid in self.ctr_dict:
            feature = self.visit_dict[response_iid]
        return feature

    def compute_feature_itemsex(self,request_item_name,request_category_name,response_item_name,response_category_name):
        '''request和response的iid 是否对应相同性别的用户购买 (lkx)
           输入：request item name and category, response item name and category
           输出：1, same sex; 0, different sex or cannot judge'''
        feature = 0
        feature = is_same_sex(request_item_name,request_category_name,response_item_name,response_category_name)
        return feature

    def compute_feature_relatedset(self,request_category_name, response_category_name):
        '''request和response的商品的类别是否属于相关类别 (lkz)
           输入：request item name and category, response item name and category
           输出：1, 属于相关类别; 0, 不属于相关类别 or cannot judge'''
        feature = 0
        if is_in_set(request_category_name, response_category_name) == 1:
            feature = 1
        return feature

    def compute_feature_ctr(self, response_iid):
        '''获取点击次数除以推荐次数特征 (lkx)
           输入：ctr 字典， response iid.
           输出：response iid 对应的ctr'''
        feature = 0
        if response_iid in self.ctr_dict:
            feature = self.ctr_dict[response_iid]
        return feature

    def compute_feature_useritemsex(self, gid, response_category_name, response_item_name):
        sex = ""
        feature = 0
        sex_dict = self.user_sex_dict
        if gid in sex_dict:
            sex = sex_dict[gid]["sex"]
        sex = sex.encode("utf-8")
        if sex in {"男","女"}:
            feature = is_related_sex(response_category_name, response_item_name, sex)
        return feature



if __name__ == '__main__':
    exit()
    #example1
    #arguments = {}
    #feat = Feature('filepath', **arguments)

    #example2 
    #feat = Feature('filepath', dict1='dict1path', dict2='dict2path'...) 
   
