import os
import sys
import re
import costumRule as cr
import argparse 

parser=argparse.ArgumentParser(description="add emmylua comment to lua function")
parser.add_argument("-i","--input",help="input dir or file path")
parser.add_argument("-o","--output",help="output dir or file path,if is dir")
args=parser.parse_args()
print(args)
inputPath=args.input
outputPath=args.output


if os.path.exists(inputPath) is False:
    print("input path not exist")

if os.path.exists(outputPath) is False:
    os.makedirs(outputPath)

outputPath=outputPath+"/"
inputPath=inputPath+"/"




funcRe=re.compile(r"function\s*(?P<funcName>[^\s]+)?\s*\((?P<params>[^()]+)\)")
classRe=re.compile(r"(?P<className>[\w_]+)\s*=\s*class")
commonCommentRe=re.compile(r"^--(?P<comment>[^\-]+)")
emmyLuaCommentRe=re.compile(r"^---@(?P<emmyType>\w+)(?P<comment>.+)")
emmyLuaParamRe=re.compile(r"(?P<param>\w+)")

typeClass=[]
for key,value in cr.RULES.items():
    typeClass.append((re.compile(key+"$",re.IGNORECASE),value))


GlobalCount=0
def getCount():
    global GlobalCount
    GlobalCount=GlobalCount+1
    return GlobalCount

commentTp="---{0} {1}"
class EmmyComment():
    def __init__(self,emmyType:str,comment:str):
        self.emmyType=emmyType
        self.comment=comment    
    def serilize(self):
        return commentTp.format("" if self.emmyType=="None" else "@"+self.emmyType,self.comment.replace("\n",""))
class LineBlock():
    def __init__(self,text:str):
        self.text=text
        self.mc:re.Match=None
        self.isCommon=False
        self.comments=dict()
    def addComment(self,emmyComment:EmmyComment):
            
        if emmyComment.emmyType=="param":
            mc=emmyLuaParamRe.search(emmyComment.comment)
            if mc:
                paramComment=self.comments.get(emmyComment.emmyType+mc.group("param"))
                if paramComment:
                    return
                else:
                    self.comments[emmyComment.emmyType+mc.group("param")]=emmyComment
            else:
                self.comments[getCount()]=emmyComment
        else:
            self.comments[getCount()]=emmyComment
    def isComment(self):
        mc=commonCommentRe.search(self.text)
        if mc:
            self.mc=mc
            self.isCommon=True
            return True
        mc=emmyLuaCommentRe.search(self.text)
        if mc:
            self.mc=mc
            self.isCommon=False
            return True
        return False
    def isClass(self):
        mc=classRe.search(self.text)
        if mc:
            self.mc=mc
            return True
        return False
    def isFunction(self):
        mc=funcRe.search(self.text)
        if mc:
            self.mc=mc
            return True
        return False
    def toComment(self):
        if self.isCommon:
            return  EmmyComment("None",self.mc.group("comment"))
        else: 
            et=self.mc.group("emmyType")
            return EmmyComment(et,self.mc.group("comment"))
    def serilize(self):
        strList:list=[]
        for comment in self.comments.values():
            strList.append(comment.serilize())
        if len(strList)==0:
            return self.text
        else:
            return "{0}\n{1}".format("\n".join(strList),self.text)

lineBlockList:list=[]
commentBuffer:list=[]

def getType(param:str):
    for items in typeClass:
        if items[0].search(param):
            return items[1]
    return "any"

def parseLine(line:str):

    lineBlock=LineBlock(line)

    if lineBlock.isComment():
        commentBuffer.append(lineBlock.toComment())
        return
    #dump 注释
    for comment in commentBuffer:
        lineBlock.addComment(comment)
    commentBuffer.clear()
    #添加到列表
    lineBlockList.append(lineBlock)

    if lineBlock.isClass():
        lineBlock.addComment(EmmyComment("class",lineBlock.mc.group("className")))

    elif lineBlock.isFunction():
        mc=lineBlock.mc
        #funcName=mc.group("funcName")
        params=mc.group("params")

        if params:
            tp="{0} {1}"
            for param in params.split(","):
                param=param.strip()
                ptype=getType(param)
                lineBlock.addComment(EmmyComment("param",tp.format(param,ptype)))
   
def isLua(fileName):
    return fileName.find(".lua")!=-1

def generateFile(inputFilePath,outputPath):
    global lineBlockList
    global commentBuffer
    inputFile=inputFilePath
    outFile=outputPath
    fileHandle=open(inputFile,"r",encoding='utf8')
    fileHandleOut=open(outFile,"w",encoding="utf8")
    for line in fileHandle.readlines():
        parseLine(line)

    fileHandle.close()
    for block in lineBlockList:
        fileHandleOut.write(block.serilize())

    fileHandleOut.close()
    lineBlockList=[]
    commentBuffer=[]

def main(dirName):
    files=os.listdir(inputPath+dirName)
    for fileName in files:
        fileNameIn=inputPath+dirName+"/"+fileName
        if os.path.isdir(fileNameIn):
            main( dirName+"/"+fileName)
        elif isLua(fileName):
            outdir=outputPath+dirName
            fileNameOut=outdir+"/"+fileName
            if os.path.exists(outdir) is False:
                os.makedirs(outdir)
            generateFile(fileNameIn,fileNameOut)
        else:
            print(fileName,"未知文件，忽略")


main("")

