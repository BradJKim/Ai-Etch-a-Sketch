import readchar

class KeyboardController:
    def __init__(self):
        pass
    
    def grabInputChar (self):
        try:
            return readchar.readkey()
        except Exception as e:
            print("Keyboard Controller Error: ", e)
            return False