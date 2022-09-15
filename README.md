# 易班自动签到
本项目仅供学习与研究使用, 一切后果由使用者承担

# 使用教程
## 初始化
克隆仓库  
进入src目录  
创建`userData.py`文件, 内容如下
```python
user_data = [{
	'Phone': '手机号',
	'PassWord': '密码(明文)',
	'SendKey': 'Server酱 Token Key', # 用于微信通知, 在Server酱官网注册用户获取
	'Address': '定位地址' 
},# 第二个人. 如果不需要, 只保留,号前的内容和最后的]号就行
{
	'Phone': '手机号',
	'PassWord': '密码(明文)',
	'SendKey': 'Server酱 Token Key',
	'Address': '定位地址' 
}]
```
Server酱 [官网](https://sct.ftqq.com/)

一切准备就绪后, 双击 `yibanAutoSign.py` 就可以运行了.  
一般情况下, 签到是限定时间的. 所以在限定时间外签到肯定会失败, 而且会浪费 Server酱 每日免费额度(5次)

## 自动执行
### Windows
使用计划任务, 要保证在签到时间内网络通畅, 以及设备在线(电脑不开机怎么执行任务)  
具体教程百度或 [点这里](https://topbook.cc/overview?selectedArticle=1383&title=%E4%BD%BF%E7%94%A8%E8%AE%A1%E5%88%92%E4%BB%BB%E5%8A%A1%E7%A8%8B%E5%BA%8F%EF%BC%8C%E8%AE%A9%20Windows%20%E8%87%AA%E5%8A%A8%E5%B7%A5%E4%BD%9C%E3%80%82)

### Linux
使用 `Crond` 或类似的计划任务程序  
你会Linux应该不用我教了