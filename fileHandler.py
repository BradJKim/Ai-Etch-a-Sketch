class FileHandler:
    def __init__(self, fileName):
        self.fileName = fileName
    
    def readFile(self):
        with open(self.fileName, "r") as f:
            return f.read()

    def clearFile(self):
        with open(self.fileName, "r+") as f:
            f.seek(0)
            f.truncate()
            
    def appendToFile(self, text, pos=-1, newLine=True):
        with open(self.fileName, 'r+') as f:
            content = f.read()
            is_empty = len(content) == 0
            
            if pos == -1:
                pos = len(content)
            
            new_content = content[:pos]
            rest = content[pos:]
            
            if newLine and not is_empty:
                new_content += '\n'
            new_content += text
            new_content += rest
            
            f.seek(0)
            f.write(new_content)
            f.truncate()
            
    def deleteCharAt(self, pos):
        with open(self.fileName, 'r') as f:
            content = f.read()
        
        if 0 <= pos < len(content):
            content = content[:pos] + content[pos + 1:]
        
        with open(self.fileName, 'w') as f:
            f.write(content)
            
    def getCharLength(self):
        with open(self.fileName, 'r') as f:
            return len(f.read())