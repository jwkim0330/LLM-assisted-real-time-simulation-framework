
class Logger:
    # 왜 이런식으로 설정하고 각각은 무엇을 의미하지? -> 
    GENERAL = 0
    STATE = 1
    MESSAGE = 2
    TA = 3
    STRUCTURE = 4

    #엔진과 파일 이름을 가져온다 + log 를 분야별로(general,message 등) 기록을 할것인지 말것인지 이진변수로 들여온다,
    # 파일 이름이 -1이면 파일을 열지 않는다. 아마 파일을 받을 때 받은 파일에 대한 정보를 객체 형태로서 저장하는 느낌이다. 
    def __init__(self,engine,strFileName,blnLogGeneral,blnLogState,blnLogMessage,blnLogTA,blnLogStructure):
        self.engine = engine
        self.strFileName = strFileName
        if strFileName == -1:
            self.blnLogFile = False
        else:
            self.file = open(strFileName,'w')
            self.blnLogFile = True
        self.blnLogGeneral = blnLogGeneral
        self.blnLogState = blnLogState
        self.blnLogMessage = blnLogMessage
        self.blnLogTA = blnLogTA
        self.blnLogStructure = blnLogStructure


    def log(self,type,message):
        if type == Logger.STRUCTURE:
            if self.blnLogStructure == True:
                self.printOut("Structure Log", message)
        if type == Logger.GENERAL:
            if self.blnLogGeneral == True:
                self.printOut("General Log", message)
        if type == Logger.STATE:
            if self.blnLogState == True:
                self.printOut("State Log",message)
        if type == Logger.MESSAGE:
            if self.blnLogMessage == True:
                self.printOut("Message Log", message)
        if type == Logger.TA:
            if self.blnLogTA == True:
                self.printOut("TA Log", message)

    def printOut(self,strType,message):
        out = str(self.engine.getTime()) + "," + strType + "," + message
        if self.blnLogFile == True:
            self.file.write(out+"\n")
            self.file.flush()
        else:
            print(out)

    def __del__(self):
        if self.blnLogFile == True:
            self.file.close()
