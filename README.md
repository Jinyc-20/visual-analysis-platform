# Visual Analysis Platform

## 使用指南
见[wiki](https://github.com/cutrain/visual-analysis-platform/wiki "数据分析平台wiki")

### 运行环境要求
```
redis
python >= 3.4
*MySQL # "SQL-command" require
```

### Ubuntu 安装
```bash
sudo apt-get install python3
sudo apt-get install redis-server
pip install -r requirements.txt
# if you want use SQL Server input following
# sudo apt-get install unixodbc unixodbc-dev freetds-dev freetds-bin tdsodbc 
# pip install pymssql
```

### windows(x64) 安装
```
download python3 from "https://www.python.org/downloads/"
download redis from "https://github.com/MicrosoftArchive/redis/releases"
pip install -r requirements.txt
```


## 运行
```bash
python3 manage.py runserver -p 8080
```
访问 http://localhost:8080 可以使用
数据的输入和输出如果不给绝对地址则会在项目的data 文件夹下存储，建议将需要使用的数据放到data文件夹中

### 数据存放位置
`./data/`
### 模型存放位置
`./model/`


## 参与开发
### 添加新的功能
添加新的json文件到 `api/*/*.json`

json格式如下,
```js
{
  "name":"knn", // 功能id,与函数实现接口名称相同，函数名中'-'替换为'_'
  "display":"k近邻", // 功能显示内容
  "inout":"in2out1", // 输入输出个数
  "attr": [ // 功能参数表
    {
      "name":"method", // 参数id
      "display":"方法", // 参数显示内容
      "type":"list", // 参数类型
      "default":"classify", // 参数默认值
      "list":["classify", "regress"] // list参数类型的选项表
    }
  ]
}
```
添加后,运行脚本更新api ```python3 api/gen_params.py```
更新app/main中的函数
### 节点参数类型表
+ *list* 列表列出可选项,添加"list"的key
```json
{
  "name":"method",
  "display":"方法",
  "type":"list",
  "default":"classify",
  "list":["classify", "regress"]
}
```
+ *number* 输入内容只能为数字
+ *password* 密码,显示时隐藏输入
+ *file* 指定文件位置,有选择文件的button
+ *text* 单行参数
+ *richtext* 多行参数

bug反馈或其它问题请联系 duanyuge@qq.com 或 微信 cutrain_

