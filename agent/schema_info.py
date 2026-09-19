DATABASE_SCHEMA = """
【重要】数据库表结构说明 - PSEO 高校毕业生就业与收入数据分析系统

## student_placement PSEO就业与收入数据表
字段说明：
- institution_id(学校/机构ID) - VARCHAR
- institution_name(学校/机构名称) - VARCHAR
- institution_state(学校所在州/地区) - VARCHAR
- institution_type(学校类型或层级) - VARCHAR
- degree_level(学历层级) - VARCHAR
- degree_field(专业/学科字段) - VARCHAR
- major_category(专业大类) - VARCHAR
- graduation_year(毕业年份) - INT
- cohort_year(毕业 cohort/统计批次) - VARCHAR
- industry(就业行业) - VARCHAR
- employment_count(就业人数) - INT
- total_graduates(毕业生人数/样本人数) - INT
- employment_rate(就业率) - DOUBLE，已按0-100百分比保存
- median_earnings_1yr(毕业后1年收入中位数) - DOUBLE
- median_earnings_5yr(毕业后5年收入中位数) - DOUBLE
- median_earnings_10yr(毕业后10年收入中位数) - DOUBLE
- p25_earnings(收入第25百分位) - DOUBLE
- p75_earnings(收入第75百分位) - DOUBLE

## users 用户表（登录验证用）
- id, name, email, phone, department
"""