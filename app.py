import readchar
from enum import Enum, auto

from fileHandler import FileHandler
from LLMController import LLMController
from KeyboardController import KeyboardController


class PageState(Enum):
    INPUT_DISPLAY = auto()
    OUTPUT_DISPLAY = auto()
    
def main():
    input_file_handler = FileHandler('input.txt')
    output_file_handler = FileHandler('output.txt')
    llm_controller = LLMController(input_file_handler, output_file_handler)
    keyboard_controller = KeyboardController()
    
    pageState = PageState.INPUT_DISPLAY
    resSignal = True
    position = 0
            
    
    """ FUNCTIONS """
    
    def init():
        input_file_handler.clearFile()
        output_file_handler.clearFile()
    
    def updatePageState(state):
        nonlocal pageState
        pageState = state
    
    def incrementPosition():
        nonlocal position
        maxLength = input_file_handler.getCharLength()
        if position != maxLength: position += 1
        
    def decrementPosition():
        nonlocal position
        if position != 0: position -= 1
        
    def resetPosition():
        nonlocal position
        position = 0

    def updatePosition(input):
        match input:
            case 'RIGHT': incrementPosition()
            case 'LEFT': decrementPosition()

    def writeToInputAt(pos, text):
        input_file_handler.appendToFile(text, pos, False)
        incrementPosition()
        
    def deleteInputCharAt(pos):
        input_file_handler.deleteCharAt(pos)
        decrementPosition()
        
    def handleEnterInput():
        nonlocal resSignal
        updatePageState(PageState.OUTPUT_DISPLAY)
        resSignal = llm_controller.prompt()
        resetPosition()
        
        
    """ MAIN """
    
    init()
    while resSignal:
        key = keyboard_controller.grabInputChar()
        
        match pageState:
            case PageState.INPUT_DISPLAY:
                match key:
                    case readchar.key.RIGHT     : updatePosition("RIGHT")
                    case readchar.key.LEFT      : updatePosition("LEFT")
                    case readchar.key.ENTER     : handleEnterInput()
                    case readchar.key.BACKSPACE : deleteInputCharAt(position - 1)
                    case readchar.key.SPACE     : writeToInputAt(position, " ")
                    case _                      : writeToInputAt(position, key)
            case PageState.OUTPUT_DISPLAY:
                match key:
                    case readchar.key.ENTER     : updatePageState(PageState.INPUT_DISPLAY) # ENTER key
                
    print("App terminated")
        
        
if __name__ == "__main__":
    main()