# 提取基本信息：姓名、性别、年龄（出生日期）、联系方式、学校、学历、求职意向、籍贯、薪资
# 工作经历和项目经历
from LAC import LAC
import re
from utils.extract import Extractor
from helpers import Exp_Decode, Exp_Extract, extract_skill
import hanlp

class TextItem(object):
    def __init__(self, txt):
        self.raw = txt
        self.segments = None

def segment_first(method):
    def inner(extractor, text_item):
        if not text_item.segments:
            text_item.segments = extractor.lac.run(text_item.raw)
        return method(extractor, text_item)
    return inner

class ResumeInfoExtractor(object):
    def __init__(self):
        self.lac = LAC(mode='lac')
        self.extractor = Extractor()
        self.exp_parser = Exp_Extract(hanlp.load(hanlp.pretrained.ner.MSRA_NER_ELECTRA_SMALL_ZH))

    def extract_contact(self, text_list, segments):
        #文本预处理
        text = []
        for i in segments['contact_segment']:
            # 根据换行符分栏
            line_elem = re.split("\n", i)
            for elem in line_elem:
                # 文本清洗
                if elem != "" and elem != " ":
                    text.append(self.extractor.clean_text(elem,
                                    remove_parentheses=False, 
                                    remove_email=False, 
                                    remove_phone_number=False))

        info = []
        for i in text:
            info_elem = re.split("\||\s", i)
            for elem in info_elem:
                if re.sub("[\s]", "", elem) != "":
                    info.append(elem)
        print("clean info: ", info)
        contact_text = info
        contact_info = {}
        contact_info["name"] = self.get_name(contact_text)
        contact_info["gender"] = self.get_gender(contact_text)
        contact_info["id_card"] = self.get_id_card(contact_text)
        contact_info["birthday"] = self.get_birthday(contact_text)
        # contact_info["experience"] = self.get_experience(contact_text)
        contact_info["current_place"] = self.get_current_place(contact_text)
        contact_info["native_place"] = self.get_native_place(contact_text)
        contact_info["phone_number"] = self.get_phone_number(contact_text)
        contact_info["QQ"] = self.get_qq(contact_text)
        contact_info["email"] = self.get_email(contact_text)
        contact_info["home_phone_number"] = self.get_tel(contact_text)
        return contact_info

    def extract_education(self, text_list, segments):
        '''
            返回学校与学历的组合，有多个则从高到低排列
        '''
        education_text = segments['education_segment']
        if len(education_text) <= 1:
            return []

        edu_decode = Exp_Decode()
        # 提取时间，描述，状态
        edu_exp = edu_decode.descrip_extract(education_text)
        # 提取公司，部门，职位，地点，薪水，行业
        edu_info = self.exp_parser.correct_eduinfo(edu_exp)
        # 综合全部信息
        res = []
        for i in range(len(edu_exp)):
            d = {**edu_exp[i], **edu_info[i]}
            # ?不需要未处理的info项
            # d.pop("info")
            # 提取课程
            courses = self.exp_parser.courses_extract(d["info"]) + self.exp_parser.courses_extract(d["description"])
            d["courses"] = courses
            res.append(d.copy())
        return res

    def extract_working_experience(self, text_list, segments):
        '''
            工作经历：公司名、时间、title、薪资、工作内容
        '''
        work_text = segments['work_segment']

        if len(work_text) <= 1:
            return []
        work_decode = Exp_Decode()
        # 提取时间，描述，状态
        work_exp = work_decode.descrip_extract(work_text)
        # 提取公司，部门，职位，地点，薪水，行业
        work_info = self.exp_parser.correct_workinfo(work_exp)
        # 综合全部信息
        res = []
        for i in range(len(work_exp)):
            d = {**work_exp[i], **work_info[i]}
            # ?不需要未处理的info项
            # d.pop("info")
            # 提取技能
            skills = []
            for k in d["description"]:
                skills = skills + extract_skill(k)
            d["skills"] = skills
            res.append(d.copy())
        return res

    def extract_project_experience(self, text_list, segments):
        project_text = segments["project_segment"]
        project_decode = Exp_Decode()

        if len(project_text) <= 1:
            return []
        project_exp = project_decode.descrip_extract(project_text)
        # 提取公司，部门，职位，地点，薪水，行业
        project_info = self.exp_parser.correct_projectinfo(project_exp)
        # 综合全部信息
        res = []
        for i in range(len(project_exp)):
            d = {**project_exp[i], **project_info[i]}
            # ?不需要未处理的info项
            # d.pop("info")
            # 提取技能
            skills = []
            for k in d["description"]:
                skills = skills + extract_skill(k)
            d["skills"] = skills
            res.append(d.copy())
        return res

    def extract_campus_experience(self, text_list, segments):
        project_text = segments["campus_segment"]
        project_decode = Exp_Decode()

        if len(project_text) <= 1:
            return []
        project_exp = project_decode.descrip_extract(project_text)
        # 提取公司，部门，职位，地点，薪水，行业
        project_info = self.exp_parser.correct_projectinfo(project_exp)
        # 综合全部信息
        res = []
        for i in range(len(project_exp)):
            d = {**project_exp[i], **project_info[i]}
            # ?不需要未处理的info项
            # d.pop("info")
            # 提取技能
            skills = []
            for k in d["description"]:
                skills = skills + extract_skill(k)
            d["skills"] = skills
            res.append(d.copy())
        return res

    def extract_skills(self, text_list, segments):
        other_text = segments["other_segment"]
        skills = []
        for text in other_text:
            skills = skills + extract_skill(text)
        return [{'skills': skills}]


    def get_name(self, text_list):
        lac_result = self.lac.run(text_list)
        for sub_result in lac_result:
            for idx in range(len(sub_result[0])):
                if sub_result[1][idx] == "PER":
                    return sub_result[0][idx].replace(" ", "")
        return ""

    def get_gender(self, text_list):
        for text in text_list:
            if "男" in text:
                return '男'
            elif "女" in text:
                return '女'
        return ""

    def get_id_card(self, text_list):
        for text in text_list:
            zipcode = self.extractor.extract_id_card(text)
            if len(zipcode) > 0:
                return zipcode[0]
        return ""

    def get_birthday(self, text_list):
        for text in text_list:
            if re.search(r'\b(?:\d{4}/\d{2}/\d{2}|\d{4}/\d{2}/\d{2}|\d{4}-\d{2}-\d{2}|\d{4}.\d{2}.\d{2}|\b(?!86)\d{1,2})\b|生日|出生日期|个人信息|年龄|岁', text):
                birthday = re.sub("生日|出生日期|个人信息|年龄|岁", "", text)
                birthday = re.sub("[：，。]", "", birthday)
                return birthday
        return ""

    # def get_experience(self, text_list):
    #     for text in text_list:
    #         if re.search("年|个月", text):
    #             experience = re.sub("", "", text)
    #             experience = re.sub("[：，？！。\|]", "", experience)
    #             return experience
    #     return ""

    def get_current_place(self, text_list):
        candidates = []
        for i in range(len(text_list)):
            text_list[i] = re.sub("现居|居住于|现居地", "", text_list[i])
            text_list[i] = re.sub("[：，？！。\|]", "", text_list[i])
            candidates.append(text_list[i])
        lac_result = self.lac.run("\n".join(candidates))
        location = ""
        for i in range(len(lac_result[0])):
            if lac_result[1][i] == "LOC":
                location += lac_result[0][i]
        return location

    def get_native_place(self, text_list):
        for text in text_list:
            if re.search("出生地|籍贯|祖籍", text):
                native_place = re.sub("出生地|籍贯|祖籍", "", text)
                native_place = re.sub("[：，？！。\|]", "", native_place)
                return native_place
        return ""

    def get_email(self, text_list):
        for text in text_list:
            email = self.extractor.extract_email(text)
            if len(email) > 0:
                return email[0]
        return ""

    def get_phone_number(self, text_list):
        for text in text_list:
            zipcode = self.extractor.extract_phone_number(text)
            if len(zipcode) > 0:
                return zipcode[0]
        return ""
    
    def get_qq(self, text_list):
        for text in text_list:
            zipcode = self.extractor.extract_qq(text)
            if len(zipcode) > 0 and re.search("QQ|qq", text):
                return zipcode[0]
        return ""

    def get_tel(self, text_list):
        rex = r'^([0-9]{3,4}-)?[0-9]{7,8}$'
        for text in text_list:
            if re.search(rex, text):
                zipcode = re.search(rex, text)
                return zipcode[0]
        return ""

    
    
    @segment_first
    def extract_goal(self, txt):
        '''
            返回求职意向
        '''
        return ""

    @segment_first
    def extract_salary_per_month(self, txt):
        "返回期望月薪"
        return ""

    @segment_first
    def extract_cert(self, txt):
        '''
            证书及资质等
        '''
        return ""

    def extract_all(self, text_list, segments):
        all_info = {}

        all_info['contact_token'] = self.extract_contact(text_list, segments)
        all_info["education_token"] = self.extract_education(text_list, segments)
        all_info['work_token'] = self.extract_working_experience(text_list, segments)
        all_info['project_token'] = self.extract_project_experience(text_list, segments)
        all_info['campus_token'] = self.extract_campus_experience(text_list, segments)
        all_info['skill_token'] = self.extract_skills(text_list, segments)

        return all_info

    