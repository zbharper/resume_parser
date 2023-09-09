# 简历解析器

import os
from collections import defaultdict
import chardet
import yaml

import extractor 
import file_reader
from resume import Resume
from split import SegmentsMethod

class ResumeParser(object):
    def __init__(self):
        self.reader = file_reader.FileReader()
        self.extractor = extractor.ResumeInfoExtractor()
        self.segmentor = SegmentsMethod()
        
    def parse(self, file_name, fid=None):
        resume = Resume(file_id=fid, file_name=file_name)
        text_list = self.reader.read(file_name)
        segments = self.segment(text_list)
        if text_list:
            info = self.extractor.extract_all(text_list, segments)
            resume.set_basic_para(info)

        return resume

    def segment(self, text_list):
        segment_dict = defaultdict(list)
        segment_dict["education_segment"], text_list = self.segmentor.load_segment(text_list, "education_keywords")
        segment_dict["work_segment"], text_list = self.segmentor.load_segment(text_list, "work_experience_keywords")
        segment_dict["project_segment"], text_list = self.segmentor.load_segment(text_list, "project_keywords")
        segment_dict["campus_segment"], text_list = self.segmentor.load_segment(text_list, "campus_keywords")
        segment_dict["other_segment"], text_list = self.segmentor.load_segment(text_list, "other_keywords")
        segment_dict["contact_segment"] = text_list
        return segment_dict