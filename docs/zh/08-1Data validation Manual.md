

# Data validation

##   delinquency_status_mba 

```
newrez.portnewrezgeneral.delinquency_status_mba → basic_data_daily_loan_common.delq_status
newrez.portnewrezlm.activelmflag ('1' → 'Y')     → basic_data_daily_loan_common.lm_flag
（fcl_flag 映射为 null，Newrez 日报中不提供此字段）
```

![image-20260524095140650](C:\Users\jli\MyData\Copilot\ForeclosureRule2\docs\zh\image\image-20260524095140650.png)

-- newrez.portnewrezgeneral.delinquency_status_mba 统计信息：

**SELECT**

​    *a*.delinquency_status_mba ,

​    **COUNT**(*) **AS** *cnt*

**FROM** newrez.portnewrezgeneral *a*

**where** *a*.dataasof = '2026-04-16'

**GROUP** **BY** *a*.delinquency_status_mba

**ORDER** **BY** *cnt* **DESC**;

--  执行结果：

delinquency_status_mba    cnt

Current	3535
Full Payoff	608
1-29 DPD	212
30-59 DPD	33
Foreclosure	30
60-89 DPD	18
90-119 DPD	6
Performing Bankruptcy	4
Service Release	4
REO	3
Foreclosure / Perf BK	3
150-179 DPD	3
3rd Party Sale	2
Non-Performing Bankruptcy	2
180+ DPD	2
120-149 DPD	2
Foreclosure / Non-Perf BK	1
REO Sale	1



## port.basic_data_loan_fcl

--   查询port.basic_data_loan_fcl的数据日期分布--5月24日查询，查到最近日期是 5月22日

**SELECT**

​    *a*.dataasof ,

​    **COUNT**(*) **AS** *cnt*

**FROM** port.basic_data_loan_fcl *a*

**GROUP** **BY** *a*.dataasof

**ORDER** **BY** dataasof **DESC**;



dataasof    count

2026-05-22	5765
2026-05-21	5765
2026-05-20	5658
2026-05-19	5658
2026-05-18	5658
2026-05-17	5658
2026-05-16	5658
2026-05-15	5658
2026-05-14	5658
2026-05-13	5658
2026-05-12	5658
2026-05-11	5658
2026-05-10	5658
2026-05-09	5658
2026-05-08	5658
2026-05-07	5341



---  查询ActiveFcFlag 的分布

**SELECT**

​    *a*.ActiveFcFlag ,

​    **COUNT**(*) **AS** *cnt*

**FROM** port.basic_data_loan_fcl *a*

**where** *a*.dataasof = '2026-05-22'

**GROUP** **BY** *a*.ActiveFcFlag

**ORDER** **BY** *cnt* **DESC**;

ActiveFcFlag    count

0	5008
	  713
1	44