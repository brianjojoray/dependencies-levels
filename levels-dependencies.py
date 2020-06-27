import json
import requests
import datetime
import pyecharts.options as opts
from pyecharts.charts import Graph,Tab

class dependLevels:
    def __init__(self,depList, rootName):
        self.nodes = []
        self.nodesRemove = []
        self.levels = []
        self.deps = []
        self.maxDeep = 0
        self.nodeStack = []
        for i in depList:
            #print (i)
            dep = {'parent':i[0],'child':i[1],'is_circle':False}  #is_circle 标记是否循环依赖
            self.deps += [dep]
            #print (i[0],i[1])
            self.DepAdd(i[0], i[1])

        #计算深度
        self.NodesDeep(rootName,0,'')
        #计算每一层节点数量
        self.getLevels()
        #删除不在树上的节点
        #print ('remove nodes start...nodes count is:',len(self.nodes))
        for node in self.nodes:
            if node['deep'] == -1:
                #print (node['name'])
                self.nodesRemove += [node]
        for n1 in self.nodesRemove:
            self.nodes.remove(n1)
        #print ('remove nodes end ...nodes count is:',len(self.nodes))
        #建立关系图坐标
        self.buildMap()

    def DepAdd(self,left,right):
        self.NodeAdd(node = right, parent = left)
        self.NodeAdd(node = left, child = right)

    #节点更新
    def NodeAdd(self,node,parent = None, child = None):
        k = self.NodesFind(node)
        if k is None:
            k = {'name':node, 'parent':[], 'child':[], 'deep':-1,'x':0, 'y':0, 'levelSort':0}
            if parent and parent not in k['parent']:
                k['parent'] += [parent]
            if child and child not in k['child']:
                k['child'] += [child]
            self.nodes += [k]
        else:
            if parent:
                k['parent'] += [parent]
            if child:
                k['child'] += [child]
            

    #查找节点是否存在
    def NodesFind(self,node):
        for t in self.nodes:
            if node == t['name']:
                return t
        return None
    
    #查找节点序号
    def NodesFindID(self,node):
        maxnode = len(self.nodes)
        for t,id in zip(self.nodes,range(maxnode)):
            if node == t['name']:
                return id
        return None 

    def pushNodeStack(self, node):
        self.nodeStack += [node]
        return

    def popNodeStack(self):
        self.nodeStack.pop()
        return 
    
    def NodeInStack(self,node):
        if node in self.nodeStack:
            #print (self.nodeStack)
            return True
        return False
    #树的深度
    def NodesDeep(self, node, deep, child):
        #print (node,deep,child)
        
        r = self.NodesFind(node)
        if self.NodeInStack(node):
            #print ('Found Circle Dependencies:', node, child, self.nodeStack)
            for d in self.deps:
                if child==d['child'] and node == d['parent']:
                    d['is_circle'] = True
            return

        if r['deep'] > deep:            
            return 
            
        r['deep'] = deep
        if r['parent']:
            for p in r['parent']:
                self.pushNodeStack(node)
                self.NodesDeep(p, deep + 1, node)
                #超过20层抛出错误
                assert deep < 20
                self.popNodeStack()

                
    #最大深度
    def getMaxDeep(self):
        deep = 0
        for n in self.nodes:
            if n['deep'] > deep:
                deep = n['deep']
        self.maxDeep = deep
        return deep
    
    #levels分类
    def getLevels(self):
        maxDeep = self.getMaxDeep()
        levelsList = [[] for i in range(maxDeep+1)]
        levelSortList = [0 for i in range(maxDeep+1)]
        lens = len(self.nodes)
        for n,k in zip(self.nodes,range(lens)):
            levelsList[n['deep']] += [k]
            #同一level排序
            levelSortList[n['deep']] += 1
            n['levelSort'] =  levelSortList[n['deep']]
        self.levels = levelsList
        return levelsList
    
    #获取每个level的数量
    def getLevelCount(self, level):
        return len(self.levels[level - 1])

    

    #坐标设定
    def setXY(self,name,x,y):
        node = self.NodesFind(name)
        if node:
            node['x'] = x
            node['y'] = y

    #计算每个节点的坐标
    def arrangeCell(self, name, sx , sy ):
        node = self.NodesFind(name)
        maxLevel = self.getMaxDeep()
        #print (name)
        #根据level计算x
        x = sx - sx * (node['deep'])/(maxLevel + 1) - 40
        #根据sort计算y
        level = node['deep'] + 1
        y = sy * node['levelSort']/(self.getLevelCount(level) + 1)
        
        #设定坐标
        self.setXY(name, x, y)

    #建立关系图坐标
    def buildMap(self):
        #画布大小        
        screen_x = 1800
        screen_y = 1200
        
        for node in self.nodes:
            self.arrangeCell(node['name'], screen_x, screen_y)

def getDepList():
    #获取样本数据
    res = requests.get("https://echarts.baidu.com/examples/data/asset/data/npmdepgraph.min10.json")
    data = json.loads(res.text)
    dep = []
    for e in data['edges']:
        dep += [[e['sourceID'],e['targetID']]]
    return dep

def levelRender(title, source, depList):
    #构建依赖关系图参数
    dataLevels = dependLevels(depList,source)
        
    #设置echart节点参数
    nodes = [
        {
            "x": node["x"],
            "y": node["y"],
            "id": node["name"],
            "name": node["name"],
            "value": "123",
            "symbol":"roundRect",
            "symbolSize": [5 + dataLevels.maxDeep - node["deep"], 5 + dataLevels.maxDeep - node["deep"]],
            "itemStyle": {"normal": {"color": 'green'}}
            #"label":{"formatter": "{c}"}
        }
        for node in dataLevels.nodes
    ]
    
    #设置边
    edges = [
        {
            "source": edge["parent"], 
            "target": edge["child"],
            "lineStyle":opts.LineStyleOpts
                (
                    width=2 if edge["is_circle"] is True else 0.5, 
                    curve=0.1, 
                    opacity=0.7,
                    color= 'blue' if edge["is_circle"] is True else 'grey' 
                )
        }
        for edge in dataLevels.deps
    ]
    
    #配置Graph关系图
    g = (
        Graph(init_opts=opts.InitOpts(width="1800px", height="1200px"))
        .add(
            series_name="",
            nodes=nodes,
            links=edges,
            layout="none",
            is_roam=True,
            is_focusnode=True,
            label_opts=opts.LabelOpts(is_show=True, color='red',position='top'),
            #linestyle_opts=opts.LineStyleOpts(width=0.5, curve=0.1, opacity=0.7),
            edge_label=opts.LabelOpts(
                    is_show=False, 
                    position="middle", 
                    formatter="{b}"
                ),
            edge_symbol =  ['none', 'arrow']
        )
        .set_global_opts(title_opts=opts.TitleOpts(title=title))
        .set_series_opts(
            emphasis = {
                "edgeLabel": opts.LabelOpts(
                    is_show=True, 
                    position="middle", 
                    formatter="{b}"
                )
            }
        )
        #.render(file)
    )
    return g

def depLevels():
    #获取处理后的依赖关系
    depList = getDepList()
    
    timestr = str(datetime.datetime.now())
    g1 = levelRender('request Levels Dependencies' + timestr, 'request', depList)
    g2 = levelRender('underscore Levels Dependencies' + timestr, 'underscore', depList)
    
    tab = Tab()
    tab.add(g1, "request")
    tab.add(g2, "underscore")
    tab.render("./templates/npmLevelDependencies.html")

if __name__=='__main__':
    depLevels()