# 读取docx, pdf或图片，提取文本
import os
import re
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.layout import LAParams, LTTextBoxHorizontal
from pdfminer.converter import PDFPageAggregator
from collections import defaultdict
import pandas as pd
import chardet


def is_chinese(string):   # 不能光是中文，这个应该是判断是不是一堆空格的
    """
    检查整个字符串是否包含中文
    :param string: 需要检查的字符串
    :return: bool
    """
    for ch in string:
        if u'\u4e00' <= ch <= u'\u9fff':
            return True
    return False

def is_text(text):   
    """
    检查整个字符串是否有空格
    :param string: 需要检查的字符串
    :return: bool
    """
    if text != " \n":
        return True
    else:
        False

def is_leftright(df):
    if df["x0"][df["x0"]>190].count() > 20:
        return True
    else:
        False


def del_duplicate(text_list):  # list -> list   这边清理之后 分模块再处理的话只需要 del text_list[0]第一个标题就可以了
    text = []
    j = ""
    for i in text_list:
        # 去除空行
        if re.sub("\s", "", i) == "":
            continue
        elif re.sub("\s", "", i) == j:
            continue
        else:
            j = re.sub("\s", "", i)
            line_elem = re.split("\s[\s]+|\n", i)
            for elem in line_elem:
                if elem != "" and elem != " ":
                    text.append(elem)
    text = sorted(set(text),key=text.index)  # 把重复的元素删除，且保留原有的顺序
    return text

class FileReader(object):
    def __init__(self):
        pass
    
    def read(self, file_name):
        ext = os.path.splitext(file_name)[-1].lower()
        if ext == '.pdf':
            return self.read_pdf(file_name)
        elif ext == '.docx':
            return self.read_docx(file_name)
        elif ext in ['.jpg','.png','.bmp']:
            return self.image_ocr(file_name)
        else:
            raise ValueError("Invalid file format! {}".format(file_name))

    def read_docx(self, file_name):
        pass

    def read_pdf(self, file_name):
        """
        This function takes the file object, read the file content and store it into a dictionary for processing

        :param fileObj: File object for reading the file
        :return: None
        """
        parser = PDFParser(open(file_name,'rb'))  # 用文件对象来创建一个pdf文档分析器，PDFParser从文件中提取数据
        document = PDFDocument(parser)  # 创建一个PDF文档 PDFDocument保存数据，存储文档数据结构到内存中 
        if not document.is_extractable:   # 检测文件是否提供txt转换，不提供就忽视
            raise PDFTextExtractionNotAllowed
        rsrcmgr = PDFResourceManager()    # PDFResourceManager：pdf 共享资源管理器,用于存储共享资源，如字体或图像。
        device = PDFDevice(rsrcmgr)       # 把解析到的内容转化为你需要的东西
        
        # BEGIN LAYOUT ANALYSIS
        laparams = LAParams()     # 加入需要解析的参数   
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)  # 创建一个PDF设备对象
        interpreter = PDFPageInterpreter(rsrcmgr, device)    # 创建一个PDF解释器对象，解析page内容
        page_number = len([page for page in PDFPage.create_pages(document)])  # 循环遍历列表，每次处理一个page的内容
        # if page_number > 1:
        text_list = []   # 这个list是用来装全部的参数的  
        for page in PDFPage.create_pages(document):
            page_dict =  defaultdict(list)
            interpreter.process_page(page)
            layout = device.get_result() 
            page_list = []
            for lt_obj in layout:         # 遍历每一页的每一个元素     
                if isinstance(lt_obj, LTTextBoxHorizontal):
                    if is_text(lt_obj.get_text()) is True:
                        line_num = len(lt_obj.get_text().strip('\n').split('\n'))
                        if line_num == 1:
                            page_dict["x0"].append(lt_obj.bbox[0])
                            page_dict["y0"].append(page.mediabox[3] - lt_obj.bbox[3])
                            page_dict["text"].append(lt_obj.get_text().strip().replace(u'\xa0', u' '))
                            # print("origin text: ", lt_obj.get_text(), lt_obj.bbox, page.mediabox[3] - lt_obj.bbox[3])
                        else:
                            line_height = (lt_obj.bbox[3]-lt_obj.bbox[1])/line_num
            #                 print(lt_obj.get_text(), line_height, lt_obj.bbox)
                            for idx, line in enumerate(lt_obj.get_text().strip('\n').split('\n')):
                                page_dict['x0'].append(lt_obj.bbox[0])
                                page_dict['y0'].append(page.mediabox[3] - lt_obj.bbox[3] + idx*line_height)
                                page_dict['text'].append(line.replace(u'\xa0', u' '))
                    else:
                        pass
            print("before sorted: ", pd.DataFrame(page_dict))
            page_df = pd.DataFrame(page_dict).sort_values("y0", ascending=True) # 依照y0排序
            print("after sorted: ", page_df)

            # 同一行从左到右合并
            same_line = []
            line_y = 0
            for idx, line in enumerate(page_df.text):
                x = page_df.x0[idx]
                y = page_df.y0[idx]
                print("line: ", line, x, y, line_y, idx)
                if abs(y-line_y) < 1 or not same_line:
                    same_line.append((line, x))
                else:
                    same_line.sort(key=lambda x: x[1])
                    text_list.append(" ".join(x[0] for x in same_line))
                    same_line = [(line, x)]
                line_y = y
            if same_line:
                same_line.sort(key=lambda x: x[1])
                text_list.append(" ".join(x[0] for x in same_line))
            # page_list = page_df["text"].tolist()
            # text_list.extend(page_list)   # 多维的list合并为一维
        # else:
        #     for page in PDFPage.create_pages(document):
        #         page_dict =  defaultdict(list)    # 建立一个空的dict，以dict存储
        #         # page_prop_dict =  {}
        #         interpreter.process_page(page)
        #         layout = device.get_result()
        #         # id = 0
        #         for lt_obj in layout:   
        #             if isinstance(lt_obj, LTTextBoxHorizontal):
        #                 if is_text(lt_obj.get_text()) is True:
        #                     page_dict["x0"].append(lt_obj.bbox[0])   # 利用 x0筛选左右和上下的格式
        #                     page_dict["y0"].append(lt_obj.bbox[1])   # 利用 y0来排序
        #                     page_dict["text"].append(lt_obj.get_text())     # 保存每个模块的字段
        #                     # page_prop_dict[id] = lt_obj
        #                 else:
        #                     pass
        #                 # id += 1
        #         page_df = pd.DataFrame(page_dict)
        #         if is_leftright(page_df):          # 左右格式的情况
        #             df_left = page_df[page_df['x0']<=190].sort_values("y0", ascending=False)
        #             df_right = page_df[page_df['x0']>190].sort_values("y0", ascending=False)
        #             page_df = pd.concat([df_left, df_right], axis=0, ignore_index=True)
        #         else:
        #             page_df = page_df.sort_values("y0", ascending=False)
        #         text_list = page_df["text"].tolist()
        
        # ret_text = []
        # for text in text_list:
        #     for seg in text.split('\n'):
        #         if seg:
        #             ret_text.append(seg)
        # return ret_text
        return text_list

    def image_ocr(self, file_name):
        pass