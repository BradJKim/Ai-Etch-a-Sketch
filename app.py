import readchar
from enum import Enum, auto

from FileHandler import FileHandler
from LLMController import LLMController
from KeyboardController import KeyboardController
from LCDController import LCDController

class PageState(Enum):
    INPUT_DISPLAY = auto()
    OUTPUT_DISPLAY = auto()
    
def main():
    input_file_handler = FileHandler('input.txt')
    output_file_handler = FileHandler('output.txt')
    llm_controller = LLMController(input_file_handler, output_file_handler)
    lcd_controller = LCDController(input_file_handler, output_file_handler)
    keyboard_controller = KeyboardController()
    
    pageState = PageState.INPUT_DISPLAY
    resSignal = True
    disSignal = True
    startup = True
    position = 0
    viewWindow = [0, 29]
            
    
    """ FUNCTIONS """
    
    def init():
        input_file_handler.clearFile()
        input_file_handler.appendToFile("Ask a question:", position, False)
        updateScreenDisplay("INPUT")
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

    def updateScreenDisplay(displayMode, viewWindow):
        nonlocal disSignal
        disSignal = lcd_controller.displayScreen(displayMode, position, viewWindow)
        
    def incrementViewWindow():
        nonlocal viewWindow
        if viewWindow[1] < lcd_controller.maxLines:
            viewWindow = [viewWindow[0]+1, viewWindow[1]+1]

    def decrementViewWindow():
        nonlocal viewWindow
        if viewWindow[0] > 0:
            viewWindow = [viewWindow[0]-1, viewWindow[1]-1]
            
    """ MAIN """
    
    init()
    
    while resSignal and disSignal:
        key = keyboard_controller.grabInputChar()
        
        if startup:
            input_file_handler.clearFile()
            startup = False
                
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
                    case readchar.key.ENTER     : updatePageState(PageState.INPUT_DISPLAY)
                    case readchar.key.UP        : incrementViewWindow()
                    case readchar.key.DOWN      : decrementViewWindow()

        match pageState:
            case PageState.INPUT_DISPLAY:
                updateScreenDisplay("INPUT", viewWindow)
            case PageState.OUTPUT_DISPLAY:
                updateScreenDisplay("OUTPUT", viewWindow)

            
    print("App terminated")
        
        
if __name__ == "__main__":
    main()