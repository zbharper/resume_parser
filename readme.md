#整体思路：

1. lac 提取姓名与机构
2. 机构中提取学校名
3. 关键词提取学历，并找出最高学历
4. 正则表达式提取邮箱和手机号
5. 地址中提取籍贯
6. 关键词提取求职意向及技能

# 使用方式,可參考test.ipynb

```
from resume_parser import ResumeParser

parser = ResumeParser()
pdf_file = '/home/deepctrl/test/resume/xxxxxx.pdf'

resume = parser.parse(pdf_file)
```