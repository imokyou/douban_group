#  我就是想看看豆瓣上有多少个群组

## 随笔
* 用代理爬
* 代理在各大免费网站上找
* 数据存到mongodb，数据格式：{'name': '', 'gid': '', 'members': 1000, 'created_at': '2017-01-25', 'owner_name': 'xxxx', 'owner_id': 'xxxx'}
* 群组页面规则： https://www.douban.com/group/(gid)
* 群组会员页面规则：https://www.douban.com/group/(gid)/members
* url队列用redis管理，三个key, urls, urls_success, urls_failed, 每个url重试次数为3次
* 服务启动前的10分钟做代理池预热
* 有三个主进程：一个爬代理，检测代理是否有效，一个去爬豆瓣
* 主进程下开多个线程处理事务
* 跑完后生成统计报告：用时、总数、失败总数



## 代码模块流程
* runserver开启三个主进程：代理池的两个进程干活；爬豆瓣进程hold住，十分钟内不要动，用redis标识
* 爬代理进程
    * 开5个线程，每个线程爬一个网站，优先爬高匿代理。如果被封就拿代理爬，最多试三个代理。
    * 把代理存到redis中, 先检测，直接存结果
* 检测代理进程
    * 把代理全都拿出来，开10个线程去检测，如果有效就放回，无效就丢掉
* 爬豆瓣进程
    * 开10个线程去跑，优先通过代理访问，最多重试3次
    * 如果页面有匹配的就存到urls, 爬成功就存到urls_success, 失败就存到urls_failed, 利用urls_success和urls_failed排重
    * 解析成功就存到mongodb